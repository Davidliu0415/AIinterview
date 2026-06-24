# AI Java Backend Interview Agent

本项目是一个本地 PC Web 应用：FastAPI + Jinja2 + Vanilla JS + LangChain + DeepSeek + MySQL。它可以导入 PDF/DOCX 简历，分析候选人画像，并模拟校招/初级 Java 后端面试，支持浏览器语音输入和朗读。

## Quick Start

Windows 用户可以直接双击 `start.bat` 一键启动。脚本会自动创建虚拟环境、安装依赖、初始化 MySQL 数据库，并打开本地页面。

也可以手动启动：

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
python scripts\init_db.py
python run_app.py
```

启动后默认打开：

```text
http://127.0.0.1:8000
```

## Configure Your API Key

仓库不会提交 `.env` 文件，也不会包含任何真实 DeepSeek API key。

首次运行前，请复制示例配置：

```powershell
copy .env.example .env
```

然后打开 `.env`，把下面这一行替换成你自己的 DeepSeek API key：

```env
DEEPSEEK_API_KEY=replace-with-your-deepseek-api-key
```

完整示例：

```env
DEEPSEEK_API_KEY=sk-your-own-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_TEMPERATURE=0.4

MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_DATABASE=interview_agent
```

如果你的 MySQL 用户名、密码或端口不同，也请在 `.env` 中同步修改。

## Features

- PDF/DOCX 简历导入和文本解析
- AI 简历画像分析
- 校招/初级 Java 后端模拟面试
- 针对简历内容动态提问、追问和评分
- 浏览器语音输入与语音朗读
- MySQL 保存简历、面试记录和最终报告
- Windows 一键启动脚本
- PyInstaller exe 打包脚本

## Build EXE

```powershell
.\.venv\Scripts\activate
python scripts\build_exe.py
```

构建产物在：

```text
dist\AIInterviewAgent.exe
```

打包后的程序仍然读取同目录或当前工作目录下的 `.env`。

## API Endpoints

- `POST /api/resumes` 上传 PDF/DOCX 简历并分析
- `GET /api/resumes/{id}` 获取简历分析
- `POST /api/interviews` 创建面试
- `POST /api/interviews/{id}/answer` 提交回答并获得反馈/下一题
- `POST /api/interviews/{id}/finish` 结束面试并生成总结
- `GET /api/interviews/{id}` 获取完整面试记录

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```
