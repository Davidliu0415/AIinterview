const els = {
  resumeList: document.getElementById("resumeList"),
  interviewList: document.getElementById("interviewList"),
  detailTitle: document.getElementById("detailTitle"),
  detailBody: document.getElementById("detailBody"),
  refreshBtn: document.getElementById("refreshBtn"),
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
    year: "numeric",
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

function chips(items) {
  const unique = [...new Set((items || []).filter(Boolean))];
  if (!unique.length) return '<span class="chip">暂无</span>';
  return unique.map((item) => `<span class="chip">${escapeHtml(item)}</span>`).join("");
}

function list(items) {
  const values = (items || []).filter(Boolean);
  if (!values.length) return '<ul class="plain-list"><li>暂无</li></ul>';
  return `<ul class="plain-list">${values.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
}

function renderResumes(resumes) {
  if (!resumes.length) {
    els.resumeList.innerHTML = '<div class="empty-state">暂无简历</div>';
    return;
  }
  els.resumeList.innerHTML = resumes
    .map(
      (resume) => `
      <article class="record-item">
        <h3>${escapeHtml(resume.filename)}</h3>
        <p>${escapeHtml(resume.candidate_summary || "暂无摘要")}</p>
        <p>${formatDate(resume.created_at)}</p>
        <div class="record-actions">
          <button class="btn primary" type="button" data-resume-id="${resume.id}">
            <i data-lucide="eye"></i><span>查看</span>
          </button>
        </div>
      </article>
    `
    )
    .join("");
}

function renderInterviews(interviews) {
  if (!interviews.length) {
    els.interviewList.innerHTML = '<div class="empty-state">暂无面试</div>';
    return;
  }
  els.interviewList.innerHTML = interviews
    .map(
      (interview) => `
      <article class="record-item">
        <h3>${escapeHtml(interview.resume?.filename || `面试 #${interview.id}`)}</h3>
        <p><span class="status-pill">${escapeHtml(interview.status)}</span></p>
        <p>${formatDate(interview.created_at)}</p>
        <div class="record-actions">
          <button class="btn primary" type="button" data-interview-id="${interview.id}">
            <i data-lucide="messages-square"></i><span>查看</span>
          </button>
        </div>
      </article>
    `
    )
    .join("");
}

function renderResumeDetail(resume) {
  const analysis = resume.analysis || {};
  const skills = analysis.skills || {};
  const skillItems = Object.values(skills).flat().filter(Boolean);
  els.detailTitle.textContent = resume.filename;
  els.detailBody.innerHTML = `
    <section class="detail-section">
      <h2 class="section-title">摘要</h2>
      <p>${escapeHtml(analysis.candidate_summary || "暂无摘要")}</p>
    </section>
    <section class="detail-section">
      <h2 class="section-title">技能</h2>
      <div class="chip-list">${chips(skillItems)}</div>
    </section>
    <section class="detail-section">
      <h2 class="section-title">追问方向</h2>
      <div class="chip-list">${chips(analysis.question_focus || [])}</div>
    </section>
    <section class="detail-section">
      <h2 class="section-title">风险点</h2>
      ${list(analysis.risks || [])}
    </section>
    <section class="detail-section">
      <h2 class="section-title">原文</h2>
      <p>${escapeHtml((resume.raw_text || "").slice(0, 4000))}</p>
    </section>
  `;
}

function renderInterviewDetail(interview) {
  const summary = interview.summary || {};
  els.detailTitle.textContent = interview.resume?.filename || `面试 #${interview.id}`;
  els.detailBody.innerHTML = `
    <section class="detail-section">
      <h2 class="section-title">状态</h2>
      <span class="status-pill">${escapeHtml(interview.status)}</span>
      ${
        summary.overall_score
          ? `<span class="score-pill">总分 ${escapeHtml(summary.overall_score)}</span>`
          : ""
      }
    </section>
    ${
      summary.overall_score
        ? `
        <section class="detail-section">
          <h2 class="section-title">报告</h2>
          <p>${escapeHtml(summary.level_assessment || "")}</p>
          <div class="chip-list">${chips(summary.knowledge_gaps || [])}</div>
          ${list(summary.next_steps || [])}
        </section>`
        : ""
    }
    <section class="detail-section">
      <h2 class="section-title">记录</h2>
      <div class="chat">
        ${interview.messages
          .map(
            (message) => `
            <article class="message ${escapeHtml(message.role)} ${escapeHtml(message.message_type)}">
              <div class="message-head">
                <span>${message.role === "user" ? "候选人" : "面试官"}</span>
                <time>${formatDate(message.created_at)}</time>
              </div>
              <div class="message-body">${escapeHtml(message.content)}</div>
            </article>
          `
          )
          .join("")}
      </div>
    </section>
  `;
}

async function loadData() {
  const [resumes, interviews] = await Promise.all([api("/api/resumes"), api("/api/interviews")]);
  renderResumes(resumes);
  renderInterviews(interviews);
  refreshIcons();
}

els.resumeList.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-resume-id]");
  if (!button) return;
  try {
    const resume = await api(`/api/resumes/${button.dataset.resumeId}`);
    renderResumeDetail(resume);
  } catch (error) {
    toast(error.message, "error");
  }
});

els.interviewList.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-interview-id]");
  if (!button) return;
  try {
    const interview = await api(`/api/interviews/${button.dataset.interviewId}`);
    renderInterviewDetail(interview);
  } catch (error) {
    toast(error.message, "error");
  }
});

els.refreshBtn.addEventListener("click", () => {
  loadData().catch((error) => toast(error.message, "error"));
});

loadData().catch((error) => toast(error.message, "error")).finally(refreshIcons);
