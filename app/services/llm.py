from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import Settings, get_settings
from app.services import prompts


def normalize_score(value: Any) -> int:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0
    if 0 < score <= 5:
        score *= 20
    elif 5 < score <= 10:
        score *= 10
    return max(0, min(100, round(score)))


def extract_json_object(content: str, fallback: dict[str, Any]) -> dict[str, Any]:
    text = (content or "").strip()
    if text.startswith("```"):
        text = text.removeprefix("```json").removeprefix("```").strip()
        if text.endswith("```"):
            text = text[:-3].strip()

    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return deepcopy(fallback)


class DeepSeekInterviewAgent:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._model: ChatOpenAI | None = None

    @property
    def model(self) -> ChatOpenAI:
        if self._model is None:
            self._model = ChatOpenAI(
                model=self.settings.deepseek_model,
                api_key=self.settings.deepseek_api_key,
                base_url=self.settings.deepseek_base_url,
                temperature=self.settings.deepseek_temperature,
                timeout=90,
                max_retries=2,
            )
        return self._model

    def _invoke_json(self, system_prompt: str, user_prompt: str, fallback: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.deepseek_api_key:
            result = deepcopy(fallback)
            result["_warning"] = "未配置 DEEPSEEK_API_KEY，已使用本地兜底结果。"
            return result

        try:
            response = self.model.invoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
            )
            return extract_json_object(str(response.content), fallback)
        except Exception as exc:
            result = deepcopy(fallback)
            result["_warning"] = f"AI 调用失败，已使用本地兜底结果：{exc.__class__.__name__}"
            return result

    def analyze_resume(self, filename: str, resume_text: str) -> dict[str, Any]:
        fallback = fallback_resume_analysis(resume_text)
        return self._invoke_json(
            prompts.RESUME_ANALYSIS_SYSTEM,
            prompts.resume_analysis_user(filename, resume_text),
            fallback,
        )

    def create_opening_question(self, analysis: dict[str, Any], level: str) -> dict[str, Any]:
        fallback = {
            "opening_message": "你好，我们开始 Java 后端校招模拟面试。我会结合你的简历逐步追问。",
            "question": analysis.get("opening_question")
            or "请用 2 分钟介绍一个你最熟悉的 Java 后端项目，并说明你负责的模块。",
            "focus_area": "项目经历",
            "expected_points": ["项目背景", "本人职责", "技术选型", "遇到的问题", "改进结果"],
        }
        return self._invoke_json(
            prompts.OPENING_SYSTEM,
            prompts.opening_user(analysis, level),
            fallback,
        )

    def evaluate_answer(
        self,
        analysis: dict[str, Any],
        messages: list[dict[str, Any]],
        question_count: int,
        max_questions: int,
    ) -> dict[str, Any]:
        fallback = {
            "feedback": {
                "score": 65,
                "comment": "回答有基本方向，但还需要补充具体场景、关键技术点和量化结果。",
                "strengths": ["能围绕问题作答"],
                "improvements": ["补充技术细节", "说明自己的具体贡献", "给出结果或指标"],
                "suggested_answer": "建议按背景、方案、实现细节、问题处理、结果复盘的结构回答。",
            },
            "next_action": "ask_next",
            "next_question": "请解释一下 Spring Boot 自动配置的基本原理，以及你在项目中如何使用它。",
            "focus_area": "Spring Boot",
            "expected_points": ["Starter", "自动配置类", "条件注解", "配置属性", "实际使用场景"],
        }
        result = self._invoke_json(
            prompts.EVALUATE_SYSTEM,
            prompts.evaluate_user(analysis, messages, question_count, max_questions),
            fallback,
        )
        feedback = result.get("feedback")
        if isinstance(feedback, dict):
            feedback["score"] = normalize_score(feedback.get("score"))
        return result

    def summarize(self, analysis: dict[str, Any], messages: list[dict[str, Any]]) -> dict[str, Any]:
        fallback = {
            "overall_score": 68,
            "level_assessment": "具备校招 Java 后端基础，但项目表达和知识深度需要加强。",
            "strengths": ["有基础项目经历", "能进行基本技术沟通"],
            "weaknesses": ["回答结构不够稳定", "部分知识点缺少底层原理"],
            "knowledge_gaps": ["JVM", "并发编程", "MySQL 索引优化", "Spring 原理"],
            "communication": "建议回答时先给结论，再补充场景和细节。",
            "next_steps": ["复盘项目难点", "准备常见八股", "用 STAR 法组织项目回答"],
            "recommended_study_plan": ["Spring Boot 自动配置", "MySQL 索引和事务", "Java 集合与并发", "Redis 基础场景"],
        }
        result = self._invoke_json(
            prompts.SUMMARY_SYSTEM,
            prompts.summary_user(analysis, messages),
            fallback,
        )
        result["overall_score"] = normalize_score(result.get("overall_score"))
        return result


def fallback_resume_analysis(resume_text: str) -> dict[str, Any]:
    keywords = {
        "java": ["Java", "JVM", "集合", "多线程", "并发"],
        "spring": ["Spring", "Spring Boot", "Spring MVC", "MyBatis"],
        "database": ["MySQL", "SQL", "事务", "索引"],
        "middleware": ["Redis", "RabbitMQ", "Kafka", "Nacos", "Dubbo"],
        "tools": ["Git", "Maven", "Docker", "Linux"],
    }
    found: dict[str, list[str]] = {}
    lowered = resume_text.lower()
    for group, words in keywords.items():
        found[group] = [word for word in words if word.lower() in lowered]

    return {
        "candidate_summary": "已提取简历文本，可围绕项目经历、Java 基础、数据库和 Spring 生态进行面试。",
        "education": "未从兜底分析中识别到明确教育信息。",
        "skills": {
            "java": found["java"],
            "spring": found["spring"],
            "database": found["database"],
            "middleware": found["middleware"],
            "tools": found["tools"],
            "other": [],
        },
        "projects": [
            {
                "name": "简历项目经历",
                "tech_stack": [item for values in found.values() for item in values],
                "highlights": ["需要候选人在面试中补充本人职责和项目结果"],
                "risks": ["简历解析未能识别完整项目结构，建议从项目介绍开始追问"],
            }
        ],
        "question_focus": ["项目介绍", "Java 基础", "Spring Boot", "MySQL", "Redis"],
        "risks": ["需要核实项目真实性和技术细节深度"],
        "opening_question": "请介绍一个你最熟悉的 Java 后端项目，重点说明你的职责、技术选型和遇到的难点。",
    }
