const state = {
  config: {},
  resume: null,
  interview: null,
  recognition: null,
  listening: false,
};

const els = {
  uploadForm: document.getElementById("uploadForm"),
  resumeFile: document.getElementById("resumeFile"),
  fileName: document.getElementById("fileName"),
  uploadBtn: document.getElementById("uploadBtn"),
  analysisPanel: document.getElementById("analysisPanel"),
  startInterviewBtn: document.getElementById("startInterviewBtn"),
  chat: document.getElementById("chat"),
  answerForm: document.getElementById("answerForm"),
  answerInput: document.getElementById("answerInput"),
  sendBtn: document.getElementById("sendBtn"),
  finishBtn: document.getElementById("finishBtn"),
  voiceBtn: document.getElementById("voiceBtn"),
  speakToggle: document.getElementById("speakToggle"),
  summaryPanel: document.getElementById("summaryPanel"),
  modelBadge: document.getElementById("modelBadge"),
  toast: document.getElementById("toast"),
};

function refreshIcons() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatDate(value) {
  if (!value) return "";
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function toast(message, type = "info") {
  els.toast.textContent = message;
  els.toast.className = `toast show ${type === "error" ? "error" : ""}`;
  window.setTimeout(() => {
    els.toast.className = "toast";
  }, 2600);
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "请求失败");
  }
  return data;
}

function setButtonBusy(button, busy, label) {
  button.disabled = busy;
  if (label) {
    button.querySelector("span").textContent = label;
  }
}

function chips(items) {
  const unique = [...new Set((items || []).filter(Boolean))];
  if (!unique.length) return '<span class="chip">暂无</span>';
  return unique.map((item) => `<span class="chip">${escapeHtml(item)}</span>`).join("");
}

function list(items, className = "plain-list") {
  const values = (items || []).filter(Boolean);
  if (!values.length) return `<ul class="${className}"><li>暂无</li></ul>`;
  return `<ul class="${className}">${values.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
}

function renderAnalysis(resume) {
  if (!resume) {
    els.analysisPanel.innerHTML = '<div class="empty-state">暂无画像</div>';
    return;
  }

  const analysis = resume.analysis || {};
  const skills = analysis.skills || {};
  const skillItems = Object.values(skills).flat().filter(Boolean);
  const projects = analysis.projects || [];

  els.analysisPanel.innerHTML = `
    <section class="analysis-section">
      <h2 class="section-title">${escapeHtml(resume.filename)}</h2>
      <p class="summary-text">${escapeHtml(analysis.candidate_summary || "暂无摘要")}</p>
      ${analysis._warning ? `<p class="summary-text">${escapeHtml(analysis._warning)}</p>` : ""}
    </section>
    <section class="analysis-section">
      <h2 class="section-title">技能线索</h2>
      <div class="chip-list">${chips(skillItems)}</div>
    </section>
    <section class="analysis-section">
      <h2 class="section-title">追问方向</h2>
      <div class="chip-list">${chips(analysis.question_focus || [])}</div>
    </section>
    <section class="analysis-section">
      <h2 class="section-title">风险点</h2>
      ${list(analysis.risks || [], "risk-list")}
    </section>
    <section class="analysis-section">
      <h2 class="section-title">项目</h2>
      <div class="record-list">
        ${
          projects.length
            ? projects
                .map(
                  (project) => `
                  <article class="project-item">
                    <h3>${escapeHtml(project.name || "项目经历")}</h3>
                    <div class="chip-list">${chips(project.tech_stack || [])}</div>
                    ${list(project.highlights || [])}
                  </article>
                `
                )
                .join("")
            : '<div class="empty-state">暂无项目</div>'
        }
      </div>
    </section>
  `;
}

function roleLabel(message) {
  if (message.role === "user") return "候选人";
  if (message.message_type === "feedback") return "反馈";
  if (message.message_type === "summary") return "总结";
  return "面试官";
}

function renderMessageMeta(message) {
  const meta = message.meta || {};
  if (message.message_type === "feedback") {
    return `
      <div class="meta-block">
        <span class="score-pill">评分 ${escapeHtml(meta.score ?? "-")}</span>
        ${meta.strengths?.length ? `<div class="chip-list">${chips(meta.strengths)}</div>` : ""}
        ${meta.improvements?.length ? `${list(meta.improvements)}` : ""}
        ${
          meta.suggested_answer
            ? `<div class="suggested-answer">${escapeHtml(meta.suggested_answer)}</div>`
            : ""
        }
      </div>
    `;
  }
  if (message.message_type === "question" && meta.expected_points?.length) {
    return `<div class="meta-block"><div class="chip-list">${chips(meta.expected_points)}</div></div>`;
  }
  return "";
}

function renderChat(interview) {
  if (!interview || !interview.messages?.length) {
    els.chat.innerHTML = '<div class="empty-state">等待面试</div>';
    return;
  }

  els.chat.innerHTML = interview.messages
    .map(
      (message) => `
        <article class="message ${escapeHtml(message.role)} ${escapeHtml(message.message_type)}">
          <div class="message-head">
            <span>${roleLabel(message)}</span>
            <time>${formatDate(message.created_at)}</time>
          </div>
          <div class="message-body">${escapeHtml(message.content)}</div>
          ${renderMessageMeta(message)}
        </article>
      `
    )
    .join("");
  els.chat.scrollTop = els.chat.scrollHeight;
}

function renderSummary(interview) {
  const summary = interview?.summary || {};
  if (!summary.overall_score) {
    els.summaryPanel.classList.add("hidden");
    els.summaryPanel.innerHTML = "";
    return;
  }

  els.summaryPanel.classList.remove("hidden");
  els.summaryPanel.innerHTML = `
    <div class="summary-grid">
      <section>
        <h2 class="section-title">总分</h2>
        <span class="score-pill">${escapeHtml(summary.overall_score)}</span>
        <p class="summary-text">${escapeHtml(summary.level_assessment || "")}</p>
      </section>
      <section>
        <h2 class="section-title">沟通表现</h2>
        <p class="summary-text">${escapeHtml(summary.communication || "")}</p>
      </section>
      <section>
        <h2 class="section-title">优势</h2>
        ${list(summary.strengths || [])}
      </section>
      <section>
        <h2 class="section-title">改进</h2>
        ${list(summary.weaknesses || [])}
      </section>
      <section>
        <h2 class="section-title">知识缺口</h2>
        <div class="chip-list">${chips(summary.knowledge_gaps || [])}</div>
      </section>
      <section>
        <h2 class="section-title">学习计划</h2>
        ${list(summary.recommended_study_plan || [])}
      </section>
    </div>
  `;
}

function renderInterview(interview) {
  state.interview = interview;
  renderChat(interview);
  renderSummary(interview);

  const active = interview?.status === "active";
  els.answerInput.disabled = !active;
  els.sendBtn.disabled = !active;
  els.finishBtn.disabled = !interview || interview.status === "completed";
  refreshIcons();
}

function speak(text) {
  if (!els.speakToggle.checked || !window.speechSynthesis || !text) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text.replace(/\s+/g, " ").slice(0, 800));
  utterance.lang = state.config.speech_language || "zh-CN";
  utterance.rate = 1;
  utterance.pitch = 1;
  window.speechSynthesis.speak(utterance);
}

function speakLatestAssistant() {
  const messages = state.interview?.messages || [];
  const latest = [...messages].reverse().find((message) => message.role === "assistant");
  if (latest) speak(latest.content);
}

function setupVoice() {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) {
    els.voiceBtn.disabled = true;
    els.voiceBtn.title = "当前浏览器不支持语音输入";
    return;
  }

  const recognition = new Recognition();
  recognition.lang = state.config.speech_language || "zh-CN";
  recognition.interimResults = false;
  recognition.continuous = false;

  recognition.onstart = () => {
    state.listening = true;
    els.voiceBtn.classList.add("recording");
  };
  recognition.onend = () => {
    state.listening = false;
    els.voiceBtn.classList.remove("recording");
  };
  recognition.onerror = (event) => {
    toast(event.error || "语音输入失败", "error");
  };
  recognition.onresult = (event) => {
    const transcript = Array.from(event.results)
      .map((result) => result[0]?.transcript || "")
      .join("");
    els.answerInput.value = `${els.answerInput.value} ${transcript}`.trim();
    els.answerInput.focus();
  };

  state.recognition = recognition;
}

async function loadConfig() {
  state.config = await api("/api/config");
  els.modelBadge.textContent = state.config.model || "DeepSeek";
}

els.resumeFile.addEventListener("change", () => {
  els.fileName.textContent = els.resumeFile.files[0]?.name || "选择 PDF / DOCX";
});

els.uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = els.resumeFile.files[0];
  if (!file) {
    toast("请选择简历文件", "error");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);
  setButtonBusy(els.uploadBtn, true, "分析中");
  try {
    const resume = await api("/api/resumes", {
      method: "POST",
      body: formData,
    });
    state.resume = resume;
    renderAnalysis(resume);
    els.startInterviewBtn.disabled = false;
    toast("简历分析完成");
  } catch (error) {
    toast(error.message, "error");
  } finally {
    setButtonBusy(els.uploadBtn, false, "分析简历");
    refreshIcons();
  }
});

els.startInterviewBtn.addEventListener("click", async () => {
  if (!state.resume) return;
  els.startInterviewBtn.disabled = true;
  try {
    const interview = await api("/api/interviews", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume_id: state.resume.id, level: "campus_junior" }),
    });
    renderInterview(interview);
    speakLatestAssistant();
    toast("面试已开始");
  } catch (error) {
    toast(error.message, "error");
    els.startInterviewBtn.disabled = false;
  }
});

els.answerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const answer = els.answerInput.value.trim();
  if (!answer || !state.interview) return;

  els.sendBtn.disabled = true;
  try {
    const payload = await api(`/api/interviews/${state.interview.id}/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answer }),
    });
    els.answerInput.value = "";
    renderInterview(payload.interview);
    speakLatestAssistant();
    if (payload.result?.next_action === "finish") {
      toast("可以生成面试报告");
    }
  } catch (error) {
    toast(error.message, "error");
  } finally {
    if (state.interview?.status === "active") {
      els.sendBtn.disabled = false;
    }
  }
});

els.finishBtn.addEventListener("click", async () => {
  if (!state.interview) return;
  els.finishBtn.disabled = true;
  try {
    const interview = await api(`/api/interviews/${state.interview.id}/finish`, {
      method: "POST",
    });
    renderInterview(interview);
    speak("面试总结已生成。");
    toast("报告已生成");
  } catch (error) {
    toast(error.message, "error");
    els.finishBtn.disabled = false;
  }
});

els.voiceBtn.addEventListener("click", () => {
  if (!state.recognition || els.answerInput.disabled) return;
  if (state.listening) {
    state.recognition.stop();
  } else {
    state.recognition.start();
  }
});

els.answerInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
    els.answerForm.requestSubmit();
  }
});

loadConfig()
  .then(setupVoice)
  .catch((error) => toast(error.message, "error"))
  .finally(refreshIcons);
