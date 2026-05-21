/* =========================================
   IIS – DIAGNOSTIC ENGINE + MATURITY DASHBOARD
========================================= */

const CHOICES = [
    { text: "Fully Established", score: 4 },
    { text: "Partially Done",    score: 3 },
    { text: "Planned",           score: 2 },
    { text: "Not in Place",      score: 1 }
];

const TEAL = "#0B9B8A";
const TEAL_DARK = "#087d6e";

const EXAM_INSTRUCTION = "For each question, select ONE answer that best describes your organization's current state. If unsure, choose which is closest to reality (not aspiration).";

const exams = {
    Hiring: {
        title: "Hiring System",
        questions: [
            "Job postings explicitly state that candidates with disabilities are encouraged to apply.",
            "Job descriptions include only essential functions, avoiding criteria that may inadvertently screen out qualified candidates with disabilities.",
            "The online job application platform has been audited for accessibility and meets a recognized standard (e.g., WCAG 2.1).",
            "Recruiting communications (email, interview invitations, assessments) are accessible to candidates using assistive technology.",
            "The organization has established measurable goals for recruiting employees with disabilities.",
            "The organization has established measurable goals for recruiting employees with disabilities.",
            "A needs assessment or gap analysis is conducted to identify roles where diverse talent, including people with disabilities, is underrepresented.",
            "The organization actively partners with disability-focused organizations, job boards, or vocational programs to source candidates.",
            "Pre-employment assessments and testing tools are reviewed for accessibility before use.",
            "Equal employment opportunity statements in all postings and diversity policies explicitly mention disability inclusion."
        ]
    },
    Onboarding: {
        title: "Onboarding",
        questions: [
            "Accessibility and disability inclusion training is formally included in the onboarding program for all new employees.",
            "New employees are informed of how to request accommodations during or immediately after onboarding.",
            "Onboarding materials (handbooks, forms, presentations, e-learning) are available in accessible formats.",
            "The onboarding process includes an introduction to the organization's accessibility policy and commitment to disability inclusion.",
            "New hires with disabilities are connected to relevant employee resource groups (ERGs) or support contacts during onboarding.",
            "Onboarding workflows include verification that an employee's workstation and tools are accessible before their first day.",
            "Career development paths, including required activities to advance, are communicated in accessible formats during onboarding.",
            "Onboarding includes training on internal accessibility tools and assistive technology available to employees.",
            "Managers who onboard new employees receive specific guidance on supporting employees with disclosed disabilities.",
            "The effectiveness of onboarding for employees with disabilities is periodically evaluated and improved."
        ]
    },
    Accommodation: {
        title: "Accommodation",
        questions: [
            "A written, publicly available policy exists for employees to request ICT-related and workplace accommodations.",
            "The accommodation request process is documented, straightforward, and accessible to employees with various disabilities.",
            "Tools and workflow systems are in place to facilitate, track, and fulfill accommodation requests in a timely manner.",
            "Employees are provided with support for the use of assistive technology needed to perform their job functions.",
            "The full range of accommodations is considered, including physical, digital, communication, and scheduling adjustments.",
            "Managers are trained to handle accommodation requests respectfully and in compliance with applicable law.",
            "An exception or risk-acceptance process exists for situations where a requested accommodation cannot immediately be met.",
            "Accommodations are reassessed periodically or when an employee's role changes, to ensure continued effectiveness.",
            "Employee feedback on accommodation experiences is collected and used to improve the process.",
            "Budget is specifically allocated to fund accommodations and assistive technology for employees with disabilities."
        ]
    },
    Retention: {
        title: "Retention",
        questions: [
            "Employees with disabilities hold roles at all levels and departments, including decision-making positions.",
            "A disability-focused employee resource group (ERG) with executive sponsorship exists and is actively leveraged.",
            "Employee performance evaluation criteria include accessibility-related responsibilities where relevant to the role.",
            "Mentoring programs are available and accessible to employees with disabilities.",
            "The organization tracks retention rates of employees with disabilities and uses data to drive improvement.",
            "Career advancement opportunities are equally accessible to employees with disabilities, with no systemic barriers.",
            "Employees with disabilities are actively included in product development, user research, and accessibility audits.",
            "Employee engagement surveys include questions about disability inclusion and accessibility support.",
            "A defined process exists for employees to raise accessibility-related concerns or complaints without fear of retaliation.",
            "Communities of practice or disability inclusion working groups exist to drive continuous improvement."
        ]
    },
    Culture: {
        title: "Culture",
        questions: [
            "Executive leadership has made a public statement affirming the organization's commitment to disability inclusion.",
            "An executive sponsor or senior leader is accountable for the accessibility and disability inclusion program.",
            "Disability inclusion and accessibility are explicitly embedded in the organization's core values and code of conduct.",
            "The organization's business strategy includes proactive, measurable goals for accessibility and disability inclusion.",
            "All employees receive general disability awareness and accessibility training relevant to their role.",
            "Disability inclusion is a recognized component of the broader diversity, equity, and inclusion (DEI) strategy.",
            "The organization measures and reports on accessibility program effectiveness, including cultural indicators.",
            "A financial plan and dedicated budget exist to advance accessibility maturity across all organizational dimensions.",
            "Digital accessibility performance is integrated into employee and officer performance objectives.",
            "The organization regularly captures employee feedback on disability inclusion and accessibility culture, and acts on results."
        ]
    }
};

/* ── STATE ──────────────────────────────── */
let userAnswers = {};
let currentExam = "";
let questionIndex = 0;
let results = { Hiring:null, Onboarding:null, Accommodation:null, Retention:null, Culture:null };
let diagnosticOpen = false;
let subNavVisible = false;

/* ── SUB-NAV ────────────────────────────── */
function showSubNav() { document.getElementById("diagnosticSubNav").style.display = "block"; subNavVisible = true; }
function hideSubNav() { document.getElementById("diagnosticSubNav").style.display = "none"; subNavVisible = false; }
function setActiveSubBtn(type) {
    document.querySelectorAll(".sub-nav-btn").forEach(b => b.classList.remove("active-sub"));
    if (type) { const t = document.getElementById("sub"+type); if(t) t.classList.add("active-sub"); }
}

/* ── LOGOUT ─────────────────────────────── */
function openLogoutModal() { document.getElementById("logoutModal").style.display = "flex"; }
function closeLogoutModal() { document.getElementById("logoutModal").style.display = "none"; }

/* ── PAGE SYSTEM ────────────────────────── */
function clearSidebarActive() {
    ["dashboardBtn","diagnosticBtn","profileBtn","contactBtn"].forEach(id => {
        const el = document.getElementById(id); if(el) el.classList.remove("active-sidebar");
    });
}

function showPage(id) {
    document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
    document.getElementById(id).classList.add("active");
    clearSidebarActive();
    if (id !== "diagnostic") diagnosticOpen = false;
    const map = {dashboard:"dashboardBtn",diagnostic:"diagnosticBtn",profile:"profileBtn",contact:"contactBtn"};
    if (map[id]) document.getElementById(map[id]).classList.add("active-sidebar");
    if (id === "dashboard") loadDashboard();
}

/* ── DIAGNOSTIC TOGGLE ──────────────────── */
function openDiagnostic() {
    if (diagnosticOpen) {
        if (subNavVisible) hideSubNav(); else if (currentExam) showSubNav();
        return;
    }
    diagnosticOpen = true;
    hideSubNav();
    setActiveSubBtn(null);
    document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
    document.getElementById("diagnostic").classList.add("active");
    clearSidebarActive();
    document.getElementById("diagnosticBtn").classList.add("active-sidebar");
    resetDiagnosticState();
}

/* ── START EXAM from tile ───────────────── */
function startExam(type) {
    document.getElementById("examMenuWrapper").style.display = "none";
    document.getElementById("diagnosticSubtitle").textContent = EXAM_INSTRUCTION;
    currentExam = type;
    questionIndex = 0;
    if (!userAnswers[currentExam]) userAnswers[currentExam] = new Array(exams[currentExam].questions.length).fill(null);
    document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
    document.getElementById("diagnostic").classList.add("active");
    showSubNav();
    setActiveSubBtn(type);
    clearSidebarActive();
    document.getElementById("diagnosticBtn").classList.add("active-sidebar");
    diagnosticOpen = true;
    loadQuestion();
}

/* ── START EXAM from sidebar ────────────── */
function startExamFromSidebar(type) {
    currentExam = type;
    questionIndex = 0;
    if (!userAnswers[currentExam]) userAnswers[currentExam] = new Array(exams[currentExam].questions.length).fill(null);
    document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
    document.getElementById("diagnostic").classList.add("active");
    document.getElementById("examMenuWrapper").style.display = "none";
    document.getElementById("diagnosticSubtitle").textContent = EXAM_INSTRUCTION;
    setActiveSubBtn(type);
    clearSidebarActive();
    document.getElementById("diagnosticBtn").classList.add("active-sidebar");
    loadQuestion();
}

/* ── LOAD QUESTION ──────────────────────── */
function loadQuestion() {
    const exam = exams[currentExam];
    const qText = exam.questions[questionIndex];
    const answers = userAnswers[currentExam] || [];

    document.getElementById("questionBox").innerHTML = `
        <div style="margin-bottom:18px;">
            <div style="font-size:13px;color:#888;margin-bottom:8px;">
                Question ${questionIndex + 1} of ${exam.questions.length}
            </div>
            <div style="background:#f4f8fb;border-left:4px solid ${TEAL};padding:16px 18px;border-radius:8px;font-size:15px;line-height:1.6;color:#0E2240;margin-bottom:18px;">
                ${qText}
            </div>
        </div>
        ${CHOICES.map((c, i) => {
            const sel = answers[questionIndex] === c.score;
            return `<button
                class="answer-btn${sel?' selected':''}"
                id="q${questionIndex}_opt${i}"
                onclick="selectAnswer(${c.score},${i})"
                style="${sel?`background:${TEAL};border-color:${TEAL};color:white;`:''}">
                <span class="choice-badge" style="background:${sel?'rgba(255,255,255,.25)':'#e0edf3'};color:${sel?'#fff':TEAL};">
                    ${String.fromCharCode(65+i)}
                </span>${c.text}
            </button>`;
        }).join("")}
        <div class="nav-buttons" style="margin-top:22px;">
            ${questionIndex > 0 ? `<button class="nav-btn" onclick="prevQuestion()">← Back</button>` : ""}
            <button class="nav-btn primary-nav" onclick="nextOrSubmit()">
                ${questionIndex === exam.questions.length - 1 ? "Submit ✓" : "Next →"}
            </button>
        </div>
    `;
}

/* ── ANSWER SELECTION ───────────────────── */
function selectAnswer(scoreValue, optionIndex) {
    if (!userAnswers[currentExam]) userAnswers[currentExam] = new Array(exams[currentExam].questions.length).fill(null);
    userAnswers[currentExam][questionIndex] = scoreValue;
    CHOICES.forEach((c, i) => {
        const btn = document.getElementById(`q${questionIndex}_opt${i}`);
        if (!btn) return;
        const badge = btn.querySelector(".choice-badge");
        if (i === optionIndex) {
            btn.classList.add("selected");
            btn.style.cssText = `background:${TEAL};border-color:${TEAL};color:white;`;
            if (badge) { badge.style.background="rgba(255,255,255,.25)"; badge.style.color="#fff"; }
        } else {
            btn.classList.remove("selected");
            btn.style.cssText = "";
            if (badge) { badge.style.background="#e0edf3"; badge.style.color=TEAL; }
        }
    });
}

function nextOrSubmit() {
    const exam = exams[currentExam];
    if (questionIndex < exam.questions.length - 1) { questionIndex++; loadQuestion(); }
    else finishExam();
}

function prevQuestion() { if (questionIndex > 0) { questionIndex--; loadQuestion(); } }

function resetDiagnosticState() {
    document.getElementById("examMenuWrapper").style.display = "flex";
    document.getElementById("diagnosticSubtitle").textContent = "Please select an assessment type.";
    document.getElementById("questionBox").innerHTML = "";
    currentExam = "";
    questionIndex = 0;
    renderExamMenu();
}

/* ── FINISH EXAM ────────────────────────── */
function finishExam() {
    const answers = userAnswers[currentExam];
    let total = 0;
    answers.forEach(v => { if (v !== null) total += v; });
    results[currentExam] = (total / (exams[currentExam].questions.length * 4)) * 100;
    questionIndex = 0;
    setActiveSubBtn(null);
    document.getElementById("questionBox").innerHTML = "";
    document.getElementById("examMenuWrapper").style.display = "flex";
    document.getElementById("diagnosticSubtitle").textContent = "Please select an assessment type.";
    renderExamMenu();
    showPage("dashboard");
}

/* ── PROGRESS HELPERS ───────────────────── */
function getProgress(type) {
    const a = userAnswers[type];
    if (!a) return 0;
    return Math.round((a.filter(x => x !== null).length / exams[type].questions.length) * 100);
}

/* ── RENDER EXAM TILES ──────────────────── */
function renderExamMenu() {
    const grid = document.getElementById("examGrid");
    if (!grid) return;
    grid.innerHTML = ["Hiring","Onboarding","Accommodation","Retention","Culture"].map(type => {
        const exam = exams[type];
        const prog = getProgress(type);
        const done = results[type] !== null;
        return `<div class="exam-tile" onclick="startExam('${type}')">
            <div class="exam-tile-title">${exam.title}</div>
            <div class="exam-progress-row">
                <div class="exam-progress-wrap"><div class="exam-progress-bar" style="width:${prog}%"></div></div>
                <span class="exam-pct-label">${done ? results[type].toFixed(0) : prog}%</span>
            </div>
        </div>`;
    }).join("");
}

/* ── MATURITY LEVEL HELPER ──────────────── */
function maturityLevel(score) {
    if (score <= 25) return "Emerging";
    if (score <= 50) return "Developing";
    if (score <= 75) return "Advancing";
    if (score <= 90) return "Leading";
    return "Exemplar";
}

/* ── LOAD DASHBOARD FROM API ─────────────── */
function loadDashboard() {
    const container = document.getElementById("imdContent");
    container.innerHTML = `<div class="no-data"><div class="big-icon">⏳</div><p>Loading...</p></div>`;

    fetch('/api/dashboard-data')
        .then(r => r.json())
        .then(data => renderDashboard(data))
        .catch(() => {
            // Fallback: render from local JS results if API unavailable
            renderDashboardLocal();
        });
}

/* ── RENDER DASHBOARD FROM API DATA ──────── */
function renderDashboard(data) {
    const container = document.getElementById("imdContent");

    if (!data.has_data) {
        container.innerHTML = `
            <div class="no-data">
                <div class="big-icon">📋</div>
                <p>No completed assessments yet.</p>
                <p style="font-size:13px;">Complete the Inclusion Diagnostic Engine to see your maturity scores here.</p>
            </div>`;
        return;
    }

    const { latest, dimensions, gaps, history, can_reassess, next_eligible } = data;

    let lockHtml = "";
    if (!can_reassess) {
        lockHtml = `<div class="lock-notice">🔒 Reassessment is locked until <strong>${next_eligible}</strong>. Assessments are available every 6 months to allow meaningful progress.</div>`;
    }

    // Overall card
    const overallHtml = `
        <div class="imd-overall">
            <div class="imd-score-circle">
                <span class="big-num">${latest.overall.toFixed(0)}</span>
                <span class="pct">/ 100</span>
            </div>
            <div class="imd-overall-text">
                <h3>Overall Inclusion Score</h3>
                <p>Cycle ${latest.cycle} &nbsp;·&nbsp; ${latest.type} &nbsp;·&nbsp; ${latest.date}</p>
            </div>
            <div class="imd-badge">${latest.maturity}</div>
        </div>`;

    // Dimension cards
    const dimHtml = `
        <div class="imd-section-title">Per-Dimension Breakdown</div>
        <div class="dim-grid">
            ${dimensions.map(d => `
                <div class="dim-card">
                    <h4>${d.name}</h4>
                    <div class="dim-score">${d.score.toFixed(0)}%</div>
                    <div class="dim-level">${d.maturity}</div>
                    <div class="dim-bar-track"><div class="dim-bar-fill" style="width:${d.score}%"></div></div>
                    <div class="dim-severity ${d.severity}">${
                        d.severity === 'critical' ? '⚠ Critical gap' :
                        d.severity === 'moderate' ? '⚡ Moderate gap' : '✓ On track'
                    }</div>
                </div>`).join("")}
        </div>`;

    // Gaps & recommendations
    let gapsHtml = "";
    if (gaps && gaps.length > 0) {
        gapsHtml = `
            <div class="imd-section-title">Gaps & Recommendations</div>
            <div class="gap-list">
                ${gaps.map(g => `
                    <div class="gap-card ${g.severity}">
                        <div class="gap-header">
                            <span class="gap-badge ${g.severity}">${g.severity}</span>
                            <span class="gap-dim">${g.dimension}</span>
                        </div>
                        <div class="gap-question">${g.question}</div>
                        ${g.recommendation ? `<div class="gap-rec">${g.recommendation}</div>` : ""}
                    </div>`).join("")}
            </div>`;
    } else {
        gapsHtml = `
            <div class="imd-section-title">Gaps & Recommendations</div>
            <div style="text-align:center;padding:20px;color:#0B9B8A;font-weight:600;">
                🎉 No critical or moderate gaps identified. Keep it up!
            </div>`;
    }

    // Score history timeline
    let timelineHtml = "";
    if (history && history.length > 0) {
        timelineHtml = `
            <div class="imd-section-title">Progress History</div>
            <div class="timeline">
                ${history.map(h => `
                    <div class="timeline-item">
                        <div class="timeline-dot">C${h.cycle}</div>
                        <div class="timeline-body">
                            <strong>${h.type === 'baseline' ? 'Baseline Assessment' : 'Reassessment'}</strong>
                            <span>${h.date}</span>
                            <div class="timeline-score">${h.overall.toFixed(1)}% &nbsp;<span style="font-size:13px;font-weight:400;color:#888;">${h.maturity}</span></div>
                            <div class="timeline-dims">
                                ${Object.entries(h.dimensions).map(([dim, score]) =>
                                    `<span class="timeline-dim-chip">${dim}: ${score.toFixed(0)}%</span>`
                                ).join("")}
                            </div>
                        </div>
                    </div>`).join("")}
            </div>`;
    }

    container.innerHTML = lockHtml + overallHtml + dimHtml + gapsHtml + timelineHtml;
}

/* ── FALLBACK: render from local JS scores ── */
function renderDashboardLocal() {
    const container = document.getElementById("imdContent");
    const types = ["Hiring","Onboarding","Accommodation","Retention","Culture"];
    const hasSome = types.some(t => results[t] !== null);

    if (!hasSome) {
        container.innerHTML = `
            <div class="no-data">
                <div class="big-icon">📋</div>
                <p>No completed assessments yet.</p>
                <p style="font-size:13px;">Complete the Inclusion Diagnostic Engine to see your maturity scores here.</p>
            </div>`;
        return;
    }

    const completedTypes = types.filter(t => results[t] !== null);
    const overall = completedTypes.reduce((s, t) => s + results[t], 0) / completedTypes.length;

    const dimHtml = `
        <div class="imd-section-title">Per-Dimension Breakdown</div>
        <div class="dim-grid">
            ${types.map(type => {
                const score = results[type];
                if (score === null) return `<div class="dim-card"><h4>${exams[type].title}</h4><div style="color:#ccc;font-size:13px;margin-top:12px;">Not taken</div></div>`;
                return `<div class="dim-card">
                    <h4>${exams[type].title}</h4>
                    <div class="dim-score">${score.toFixed(0)}%</div>
                    <div class="dim-level">${maturityLevel(score)}</div>
                    <div class="dim-bar-track"><div class="dim-bar-fill" style="width:${score}%"></div></div>
                </div>`;
            }).join("")}
        </div>`;

    container.innerHTML = `
        <div class="imd-overall">
            <div class="imd-score-circle">
                <span class="big-num">${overall.toFixed(0)}</span>
                <span class="pct">/ 100</span>
            </div>
            <div class="imd-overall-text">
                <h3>Overall Inclusion Score</h3>
                <p>Based on ${completedTypes.length} of 5 dimensions completed</p>
            </div>
            <div class="imd-badge">${maturityLevel(overall)}</div>
        </div>
        ${dimHtml}
        <div style="text-align:center;padding:16px;font-size:13px;color:#888;">
            Save your results to the server to see gap analysis and full progress history.
        </div>`;
}

/* ── INIT ───────────────────────────────── */
window.onload = () => {
    renderExamMenu();
    showPage("dashboard");
};