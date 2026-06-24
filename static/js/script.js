/* =========================================
   IIS - DIAGNOSTIC ENGINE + MATURITY DASHBOARD
   Database-Ready with Local Testing Fallback
========================================= */

const TEAL = "#0B9B8A";

const CHOICES = [
    { text: "Fully Established", score: 4, letter: "A" },
    { text: "Partially Done",    score: 3, letter: "B" },
    { text: "Planned",           score: 2, letter: "C" },
    { text: "Not in Place",      score: 1, letter: "D" }
];

const EXAM_INSTRUCTION = "For each question, select ONE answer that best describes your organization's current state.";
const ASSESSMENT_ALREADY_SUBMITTED_MESSAGE = "This assessment has already been submitted. Please wait while we process it.";
const dashboardSeverityFilters = {};
let latestDashboardData = null;
let isSubmittingAssessment = false;

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll("\"", "&quot;")
        .replaceAll("'", "&#039;");
}

function groupGapsByDimension(gaps = []) {
    const groups = [];
    const groupMap = new Map();

    gaps.forEach(gap => {
        const dimension = gap.dimension || "Other";
        if (!groupMap.has(dimension)) {
            const group = {
                dimension,
                criticalCount: 0,
                moderateCount: 0,
                lowCount: 0,
                recommendations: [],
                gaps: []
            };
            groupMap.set(dimension, group);
            groups.push(group);
        }

        const group = groupMap.get(dimension);
        if (gap.severity === "critical") {
            group.criticalCount += 1;
        } else if (gap.severity === "moderate") {
            group.moderateCount += 1;
        } else if (gap.severity === "low") {
            group.lowCount += 1;
        }

        if (gap.recommendation && !group.recommendations.includes(gap.recommendation)) {
            group.recommendations.push(gap.recommendation);
        }

        group.gaps.push(gap);
    });

    return groups;
}

function uniqueTextValues(values) {
    return [...new Set(values.map(value => String(value || "").trim()).filter(Boolean))];
}

function isAnsweredAnswer(answer) {
    return answer !== null && answer !== undefined;
}

function scoreMeaning(score, maturity) {
    const rounded = Math.round(Number(score) || 0);
    if (rounded <= 25) {
        return `Your score is in the ${maturity || "Emerging"} range. Focus first on the highest-risk gaps before expanding to broader improvement work.`;
    }
    if (rounded <= 50) {
        return `Your score is in the ${maturity || "Developing"} range. Some inclusion practices are present, but several areas still need structure and consistency.`;
    }
    if (rounded <= 75) {
        return `Your score is in the ${maturity || "Advancing"} range. You are making solid progress; the next step is closing remaining gaps and documenting repeatable practices.`;
    }
    if (rounded <= 90) {
        return `Your score is in the ${maturity || "Leading"} range. Continue strengthening evidence, accountability, and long-term monitoring.`;
    }
    return `Your score is in the ${maturity || "Exemplar"} range. Keep monitoring outcomes and sharing strong practices across the organization.`;
}

function getPriorityDimensions(dimensions = [], gaps = []) {
    const gapCounts = gaps.reduce((counts, gap) => {
        const dimension = gap.dimension || gap.name || "Other";
        counts[dimension] = (counts[dimension] || 0) + 1;
        return counts;
    }, {});

    return [...dimensions]
        .sort((a, b) => {
            const gapDelta = (gapCounts[b.name] || 0) - (gapCounts[a.name] || 0);
            if (gapDelta !== 0) return gapDelta;
            return Number(a.score || 0) - Number(b.score || 0);
        })
        .slice(0, 3)
        .map(dimension => ({
            name: dimension.name,
            score: Math.round(Number(dimension.score) || 0),
            gapCount: gapCounts[dimension.name] || 0
        }));
}

function renderScoreMeaningPanel(score, maturity) {
    return `
        <section class="imd-insight-panel">
            <div>
                <span class="imd-panel-kicker">Score meaning</span>
                <h3>What your score means</h3>
            </div>
            <p>${escapeHtml(scoreMeaning(score, maturity))}</p>
        </section>`;
}

function renderPriorityPanel(dimensions, gaps) {
    const priorities = getPriorityDimensions(dimensions, gaps);
    if (!priorities.length) return "";

    return `
        <section class="imd-priority-panel">
            <div>
                <span class="imd-panel-kicker">Areas to improve</span>
                <h3>Focus on these areas first</h3>
            </div>
            <ul>
                ${priorities.map(priority => `
                    <li>
                        <strong>${escapeHtml(priority.name)}</strong>
                        <span>${priority.score}% score${priority.gapCount ? ` - ${priority.gapCount} gap${priority.gapCount === 1 ? "" : "s"}` : ""}</span>
                    </li>`).join("")}
            </ul>
        </section>`;
}

function renderActionRoadmap(gaps = []) {
    const recommendations = uniqueTextValues(
        gaps
            .filter(gap => ["critical", "moderate", "low"].includes(gap.severity))
            .map(gap => gap.recommendation)
    ).slice(0, 5);

    if (!recommendations.length) {
        return `
            <section class="imd-roadmap-panel">
                <div>
                    <span class="imd-panel-kicker">Action roadmap</span>
                    <h3>Recommended next steps</h3>
                </div>
                <p>No gap-based recommendations are available yet. Complete the diagnostic assessment to generate action items.</p>
            </section>`;
    }

    return `
        <section class="imd-roadmap-panel">
            <div>
                <span class="imd-panel-kicker">Action roadmap</span>
                <h3>Recommended next steps</h3>
            </div>
            <ol>
                ${recommendations.map(recommendation => `<li>${escapeHtml(recommendation)}</li>`).join("")}
            </ol>
        </section>`;
}

function renderReportActions(assessmentId) {
    if (!assessmentId) return "";

    return `
        <div class="imd-report-actions">
            <button type="button" class="imd-print-btn" onclick="window.location.href='/assessment_result/${assessmentId}'">
                View / Download Report
            </button>
        </div>`;
}

function renderDashboardGapGroups(gaps) {
    const groupedGaps = groupGapsByDimension(gaps);

    return groupedGaps.map(group => {
        const activeSeverity = dashboardSeverityFilters[group.dimension] || "all";
        const visibleGaps = activeSeverity === "all"
            ? group.gaps
            : group.gaps.filter(gap => gap.severity === activeSeverity);
        const gapDefinitions = uniqueTextValues(
            visibleGaps.map(gap => gap.gap_definition)
        );
        const recommendations = uniqueTextValues(visibleGaps.map(gap => gap.recommendation));
        const cardSeverity = activeSeverity !== "all"
            ? activeSeverity
            : group.criticalCount
                ? "critical"
                : group.moderateCount
                    ? "moderate"
                    : "low";

        const severityButton = (severity, count) => {
            if (!count) return "";
            const isActive = activeSeverity === severity;
            return `
                <button
                    type="button"
                    class="gap-filter-button ${severity} ${isActive ? "active" : ""}"
                    data-dimension="${escapeHtml(group.dimension)}"
                    data-severity="${severity}"
                    aria-pressed="${isActive}"
                >
                    ${count} ${severity}
                </button>`;
        };

        return `
            <article class="gap-dashboard-card ${cardSeverity}">
                <div class="gap-dashboard-head">
                    <h3>${escapeHtml(group.dimension)}</h3>
                    <div class="gap-counts">
                        ${severityButton("critical", group.criticalCount)}
                        ${severityButton("moderate", group.moderateCount)}
                        ${severityButton("low", group.lowCount)}
                    </div>
                </div>
                <section class="gap-content-panel definitions">
                    <h4>Gap</h4>
                    ${gapDefinitions.length
                        ? `<ul>${gapDefinitions.map(definition => `<li>${escapeHtml(definition)}</li>`).join("")}</ul>`
                        : `<p class="gap-empty-message">No gap analysis has been added for this filter.</p>`}
                </section>
                <section class="gap-content-panel recommendations">
                    <h4>Recommendations</h4>
                    ${recommendations.length
                        ? `<ul>${recommendations.map(recommendation => `<li>${escapeHtml(recommendation)}</li>`).join("")}</ul>`
                        : `<p class="gap-empty-message">No recommendations have been added for this filter.</p>`}
                </section>
            </article>`;
    }).join("");
}

// Questions must match database question_bank (IDs 1-50)
const DEFAULT_EXAMS = {
    Hiring: {
        title: "Hiring System",
        startQuestionId: 1,
        questions: [
            "Job postings explicitly state that candidates with disabilities are encouraged to apply.",
            "Job descriptions include only essential functions, avoiding criteria that may inadvertently screen out qualified candidates with disabilities.",
            "The online job application platform has been audited for accessibility and meets a recognized standard (e.g., WCAG 2.1).",
            "Recruiting communications (email, interview invitations, assessments) are accessible to candidates using assistive technology.",
            "The organization has established measurable goals for recruiting employees with disabilities.",
            "A needs assessment or gap analysis is conducted to identify roles where diverse talent, including people with disabilities, is underrepresented.",
            "The organization actively partners with disability-focused organizations, job boards, or vocational programs to source candidates.",
            "Pre-employment assessments and testing tools are reviewed for accessibility before use.",
            "Equal employment opportunity statements in all postings and diversity policies explicitly mention disability inclusion.",
            "Hiring managers receive training on inclusive interviewing techniques for candidates with disabilities."
        ]
    },
    Onboarding: {
        title: "Onboarding",
        startQuestionId: 11,
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
        startQuestionId: 21,
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
        startQuestionId: 31,
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
        startQuestionId: 41,
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

const exams = Object.keys(window.IIS_ACTIVE_EXAMS || {}).length
    ? window.IIS_ACTIVE_EXAMS
    : DEFAULT_EXAMS;

const PREFERRED_DIMENSION_ORDER = ["Hiring", "Onboarding", "Accommodation", "Retention", "Culture"];
const DIMENSION_ORDER = [
    ...PREFERRED_DIMENSION_ORDER.filter(dim => exams[dim]),
    ...Object.keys(exams).filter(dim => !PREFERRED_DIMENSION_ORDER.includes(dim))
];
const STORAGE_NAMESPACE = window.IIS_ASSESSMENT_STORAGE_NAMESPACE || "guest";
const ANSWER_STORAGE_KEY = `iis_answers:${STORAGE_NAMESPACE}`;
const ANSWER_SIGNATURE_KEY = `iis_answers_signature:${STORAGE_NAMESPACE}`;

/* == STATE == */
let userAnswers = {};  // { "Hiring": [4,3,2,...], "Onboarding": [...], ... }
let currentExam = "";
let questionIndex = 0;
let diagnosticOpen = false;
let subNavVisible = false;
let isLoggedIn = false;
let assessmentLock = window.IIS_ASSESSMENT_LOCK || {
    locked: false,
    reason: "",
    next_eligible: null
};

function isAssessmentLocked() {
    return Boolean(assessmentLock && assessmentLock.locked);
}

function getAssessmentLockMessage() {
    if (!isAssessmentLocked()) return "";
    if (assessmentLock.reason === "reassessment" && assessmentLock.next_eligible) {
        return `Reassessment locked until ${assessmentLock.next_eligible}.`;
    }
    return "Assessment access is currently locked.";
}

/* == INIT == */
window.onload = function() {
    loadFromLocalStorage();
    renderExamMenu();
    showPage("dashboard");
};

/* == LOCAL STORAGE (for testing without login) == */
function saveToLocalStorage() {
    localStorage.setItem(ANSWER_STORAGE_KEY, JSON.stringify(userAnswers));
    localStorage.setItem(ANSWER_SIGNATURE_KEY, getExamSignature());
}

function loadFromLocalStorage() {
    try {
        const savedSignature = localStorage.getItem(ANSWER_SIGNATURE_KEY);
        const currentSignature = getExamSignature();

        if (savedSignature && savedSignature !== currentSignature) {
            clearLocalStorage();
            return;
        }

        const saved = localStorage.getItem(ANSWER_STORAGE_KEY);
        if (saved) userAnswers = JSON.parse(saved);
    } catch(e) {}
}

function clearLocalStorage() {
    userAnswers = {};
    localStorage.removeItem(ANSWER_STORAGE_KEY);
    localStorage.removeItem(ANSWER_SIGNATURE_KEY);
}

function getExamSignature() {
    return DIMENSION_ORDER.map(dim => {
        const questionIds = exams[dim].questions.map((question, index) =>
            getQuestionId(question, `${dim}-${index}`)
        );
        return `${dim}:${questionIds.join(",")}`;
    }).join("|");
}

/* == SCORING (mirrors backend logic) == */
function maturityLevel(score) {
    if (score <= 25) return "Emerging";
    if (score <= 50) return "Developing";
    if (score <= 75) return "Advancing";
    if (score <= 90) return "Leading";
    return "Exemplar";
}

function getSeverity(score) {
    if (score <= 25) return "critical";
    if (score <= 50) return "moderate";
    return "none";
}

function getAnswerScore(answer) {
    if (answer && typeof answer === "object") return Number(answer.score);
    return Number(answer);
}

function getAnswerChoiceId(answer) {
    if (answer && typeof answer === "object") return answer.choiceId || null;
    return null;
}

function getQuestionText(question) {
    return question && typeof question === "object" ? question.text : question;
}

function getQuestionChoices(question) {
    return question && typeof question === "object" && question.choices
        ? question.choices
        : CHOICES;
}

function getQuestionId(question, fallbackId) {
    return question && typeof question === "object" ? question.id : fallbackId;
}

function hasCurrentAnswer() {
    const answers = userAnswers[currentExam] || [];
    return answers[questionIndex] !== null && answers[questionIndex] !== undefined;
}

function escapeText(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll("\"", "&quot;")
        .replaceAll("'", "&#039;");
}

function computeLocalScores() {
    const result = { dimensions: {}, overall: 0, completedCount: 0 };
    let total = 0;

    DIMENSION_ORDER.forEach(dim => {
        const answers = userAnswers[dim];
        if (!answers || answers.length !== exams[dim].questions.length || !answers.every(isAnsweredAnswer)) {
            result.dimensions[dim] = null;
            return;
        }
        const raw = answers.reduce((sum, v) => sum + getAnswerScore(v), 0);
        const maxRaw = exams[dim].questions.length * 4;
        const score = (raw / maxRaw) * 100;
        result.dimensions[dim] = {
            score: score,
            raw: raw,
            maturity: maturityLevel(score),
            severity: getSeverity(score)
        };
        total += score;
        result.completedCount++;
    });

    if (result.completedCount > 0) {
        result.overall = total / result.completedCount;
        result.maturity = maturityLevel(result.overall);
    }
    result.isComplete = result.completedCount === DIMENSION_ORDER.length;
    return result;
}

/* == PROGRESS (questionnaire completion, NOT score) == */
function getProgress(dim) {
    const answers = userAnswers[dim];
    if (!answers) return 0;
    const answered = answers.filter(isAnsweredAnswer).length;
    return Math.round((answered / exams[dim].questions.length) * 100);
}

function getStatus(dim) {
    const answers = userAnswers[dim];
    if (!answers) return "Not Started";
    const answered = answers.filter(isAnsweredAnswer).length;
    if (answered === 0) return "Not Started";
    if (answered === exams[dim].questions.length) return "Completed";
    return "In Progress";
}

/* == SUB-NAV == */
function showSubNav() { document.getElementById("diagnosticSubNav").style.display = "block"; subNavVisible = true; }
function hideSubNav() { document.getElementById("diagnosticSubNav").style.display = "none"; subNavVisible = false; }
function setActiveSubBtn(type) {
    document.querySelectorAll(".sub-nav-btn").forEach(b => b.classList.remove("active-sub"));
    if (type) { const el = document.getElementById("sub"+type); if(el) el.classList.add("active-sub"); }
}

/* == LOGOUT == */
function openLogoutModal() { document.getElementById("logoutModal").style.display = "flex"; }
function closeLogoutModal() { document.getElementById("logoutModal").style.display = "none"; }

/* == PAGE SYSTEM == */
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
    const map = { dashboard:"dashboardBtn", diagnostic:"diagnosticBtn", profile:"profileBtn", contact:"contactBtn" };
    if (map[id]) document.getElementById(map[id]).classList.add("active-sidebar");
    if (id === "dashboard") loadDashboard();
}

const requestedPage = new URLSearchParams(window.location.search).get("page");
if (["dashboard", "profile", "contact"].includes(requestedPage)) {
    window.addEventListener("load", () => showPage(requestedPage));
}

/* == DIAGNOSTIC == */
function openDiagnostic() {
    if (isAssessmentLocked()) {
        diagnosticOpen = true;
        hideSubNav();
        setActiveSubBtn(null);
        document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
        document.getElementById("diagnostic").classList.add("active");
        clearSidebarActive();
        document.getElementById("diagnosticBtn").classList.add("active-sidebar");
        renderDiagnosticLockedState();
        return;
    }

    if (diagnosticOpen) {
        if (subNavVisible) hideSubNav(); else showSubNav();
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

function resetDiagnosticState() {
    if (isAssessmentLocked()) {
        renderDiagnosticLockedState();
        return;
    }

    document.getElementById("examMenuWrapper").style.display = "flex";
    document.getElementById("diagnosticSubtitle").textContent = "Please select an assessment type.";
    document.getElementById("questionBox").innerHTML = "";
    document.getElementById("submitSection").innerHTML = "";
    currentExam = "";
    questionIndex = 0;
    renderExamMenu();
    renderSubmitButton();
}

function renderDiagnosticLockedState() {
    document.getElementById("examMenuWrapper").style.display = "none";
    document.getElementById("diagnosticSubtitle").textContent = "Assessment is currently locked.";
    document.getElementById("questionBox").innerHTML = `
        <div class="lock-notice">
            ${escapeHtml(getAssessmentLockMessage())}
        </div>
        <div class="no-data">
            <div class="big-icon">Locked</div>
            <p>Your organization can view the dashboard, but a new diagnostic assessment is not available yet.</p>
            ${assessmentLock.next_eligible ? `<p style="font-size:13px;">Next eligible date: <strong>${escapeHtml(assessmentLock.next_eligible)}</strong></p>` : ''}
        </div>`;
    document.getElementById("submitSection").innerHTML = "";
    currentExam = "";
    questionIndex = 0;
}

/* == EXAM TILES (shows PROGRESS %) == */
function renderExamMenu() {
    const grid = document.getElementById("examGrid");
    if (!grid) return;

    if (isAssessmentLocked()) {
        grid.innerHTML = `
            <div class="lock-notice" style="grid-column:1 / -1;">
                ${escapeHtml(getAssessmentLockMessage())}
            </div>`;
        return;
    }

    grid.innerHTML = DIMENSION_ORDER.map(dim => {
        const prog = getProgress(dim);
        const status = getStatus(dim);
        return `
            <button type="button" class="exam-tile" onclick="startExam('${dim}')" aria-label="Start ${escapeHtml(exams[dim].title)} assessment. ${prog}% complete.">
                <div class="exam-tile-title">${exams[dim].title}</div>
                <div class="exam-tile-status">${status}</div>
                <div class="exam-progress-row">
                    <div class="exam-progress-wrap">
                        <div class="exam-progress-bar" style="width:${prog}%"></div>
                    </div>
                    <span class="exam-pct-label">${prog}%</span>
                </div>
            </button>`;
    }).join("");
}

function renderSubmitButton() {
    const section = document.getElementById("submitSection");
    if (isAssessmentLocked()) {
        section.innerHTML = "";
        return;
    }

    const scores = computeLocalScores();

    if (scores.isComplete) {
        section.innerHTML = `
            <button type="button" class="submit-all-btn" onclick="submitAssessment()" aria-disabled="${isSubmittingAssessment}">
                ${isSubmittingAssessment ? "Submitted - processing..." : "Submit Assessment to Server"}
            </button>
            <p style="text-align:center;font-size:12px;color:#888;margin-top:8px;">
                All ${DIMENSION_ORDER.length} dimensions completed. Click to save your assessment.
            </p>`;
    } else {
        section.innerHTML = `
            <p style="text-align:center;font-size:13px;color:#888;margin-top:16px;">
                Complete all ${DIMENSION_ORDER.length} dimensions to submit your assessment (${scores.completedCount}/${DIMENSION_ORDER.length} done).
            </p>`;
    }
}

/* == START EXAM == */
function startExam(dim) {
    if (isAssessmentLocked()) {
        renderDiagnosticLockedState();
        return;
    }

    document.getElementById("examMenuWrapper").style.display = "none";
    document.getElementById("submitSection").innerHTML = "";
    document.getElementById("diagnosticSubtitle").textContent = EXAM_INSTRUCTION;
    currentExam = dim;
    questionIndex = 0;
    if (!userAnswers[dim]) userAnswers[dim] = new Array(exams[dim].questions.length).fill(null);
    showSubNav();
    setActiveSubBtn(dim);
    loadQuestion();
}

function startExamFromSidebar(dim) {
    if (isAssessmentLocked()) {
        openDiagnostic();
        return;
    }

    document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
    document.getElementById("diagnostic").classList.add("active");
    clearSidebarActive();
    document.getElementById("diagnosticBtn").classList.add("active-sidebar");
    diagnosticOpen = true;
    startExam(dim);
}

/* == QUESTIONS == */
function loadQuestion() {
    const exam = exams[currentExam];
    const question = exam.questions[questionIndex];
    const qText = getQuestionText(question);
    const choices = getQuestionChoices(question);
    const answers = userAnswers[currentExam] || [];
    const canContinue = hasCurrentAnswer();

    document.getElementById("questionBox").innerHTML = `
        <div class="question-card" tabindex="-1" style="margin-bottom:18px;">
            <div style="font-size:13px;color:#888;margin-bottom:8px;">
                Question ${questionIndex + 1} of ${exam.questions.length}
            </div>
            <div style="background:#f4f8fb;border-left:4px solid ${TEAL};padding:16px 18px;border-radius:8px;font-size:15px;line-height:1.6;color:#0E2240;">
                ${escapeText(qText)}
            </div>
        </div>
        <div class="answer-group" role="group" aria-label="Answer choices for question ${questionIndex + 1}">
        ${choices.map((c, i) => {
            const currentAnswer = answers[questionIndex];
            const currentChoiceId = getAnswerChoiceId(currentAnswer);
            const sel = currentChoiceId ? currentChoiceId === c.id : getAnswerScore(currentAnswer) === c.score;
            return `
                <button type="button" class="answer-btn${sel?' selected':''}" id="opt${i}"
                    aria-pressed="${sel}"
                    onclick="selectAnswer(${c.score}, ${i}, ${c.id || 'null'})"
                    onkeydown="handleAnswerKeydown(event, ${i})"
                    style="${sel ? `background:${TEAL};border-color:${TEAL};color:white;` : ''}">
                    <span class="choice-badge" style="background:${sel?'rgba(255,255,255,.25)':'#e0edf3'};color:${sel?'#fff':TEAL};">
                        ${c.letter}
                    </span>
                    ${escapeText(c.text)}
                </button>`;
        }).join("")}
        </div>
        <div class="nav-buttons">
            ${questionIndex > 0 ? `<button type="button" class="nav-btn" onclick="prevQuestion()">Back</button>` : ''}
            <button type="button" class="nav-btn primary-nav" id="nextQuestionBtn" onclick="nextOrFinish()" ${canContinue ? '' : 'disabled'}>
                ${questionIndex === exam.questions.length - 1 ? 'Finish' : 'Next'}
            </button>
        </div>`;

    requestAnimationFrame(() => {
        const focusTarget = document.querySelector(".answer-btn.selected") || document.querySelector(".answer-btn");
        if (focusTarget) focusTarget.focus();
    });
}

function selectAnswer(score, optIndex, choiceId = null) {
    if (!userAnswers[currentExam]) userAnswers[currentExam] = new Array(exams[currentExam].questions.length).fill(null);
    userAnswers[currentExam][questionIndex] = choiceId ? { score, choiceId } : score;
    saveToLocalStorage();

    getQuestionChoices(exams[currentExam].questions[questionIndex]).forEach((c, i) => {
        const btn = document.getElementById(`opt${i}`);
        if (!btn) return;
        const badge = btn.querySelector(".choice-badge");
        if (i === optIndex) {
            btn.classList.add("selected");
            btn.setAttribute("aria-pressed", "true");
            btn.style.cssText = `background:${TEAL};border-color:${TEAL};color:white;`;
            if (badge) { badge.style.background = "rgba(255,255,255,.25)"; badge.style.color = "#fff"; }
        } else {
            btn.classList.remove("selected");
            btn.setAttribute("aria-pressed", "false");
            btn.style.cssText = "";
            if (badge) { badge.style.background = "#e0edf3"; badge.style.color = TEAL; }
        }
    });

    const nextButton = document.getElementById("nextQuestionBtn");
    if (nextButton) nextButton.disabled = false;
}

function handleAnswerKeydown(event, optIndex) {
    const choices = getQuestionChoices(exams[currentExam].questions[questionIndex]);
    if (!["ArrowDown", "ArrowRight", "ArrowUp", "ArrowLeft"].includes(event.key)) return;

    event.preventDefault();
    const direction = event.key === "ArrowDown" || event.key === "ArrowRight" ? 1 : -1;
    const nextIndex = (optIndex + direction + choices.length) % choices.length;
    const nextButton = document.getElementById(`opt${nextIndex}`);
    if (nextButton) nextButton.focus();
}

function nextOrFinish() {
    if (!hasCurrentAnswer()) return;

    if (questionIndex < exams[currentExam].questions.length - 1) {
        questionIndex++;
        loadQuestion();
    } else {
        finishExam();
    }
}

function prevQuestion() {
    if (questionIndex > 0) { questionIndex--; loadQuestion(); }
}

function finishExam() {
    setActiveSubBtn(null);
    resetDiagnosticState();
}

function setAssessmentSubmitting(isSubmitting) {
    isSubmittingAssessment = isSubmitting;
    const submitButton = document.querySelector(".submit-all-btn");
    if (submitButton) {
        submitButton.setAttribute("aria-disabled", String(isSubmitting));
        submitButton.textContent = isSubmitting ? "Submitted - processing..." : "Submit Assessment to Server";
    }
}

function cleanSubmitErrorMessage(text) {
    const cleaned = String(text || "")
        .replace(/<script[\s\S]*?<\/script>/gi, " ")
        .replace(/<style[\s\S]*?<\/style>/gi, " ")
        .replace(/<[^>]*>/g, " ")
        .replace(/\s+/g, " ")
        .trim();

    return cleaned || "Unable to submit assessment.";
}

/* == SUBMIT TO BACKEND == */
function submitAssessment() {
    if (isSubmittingAssessment) {
        alert(ASSESSMENT_ALREADY_SUBMITTED_MESSAGE);
        return;
    }

    if (isAssessmentLocked()) {
        alert(getAssessmentLockMessage());
        renderDiagnosticLockedState();
        return;
    }

    const scores = computeLocalScores();
    if (!scores.isComplete) {
        alert("Please complete all 5 dimensions first.");
        return;
    }

    const formData = new FormData();
    let canSubmitToServer = true;

    DIMENSION_ORDER.forEach(dim => {
        const startId = exams[dim].startQuestionId;
        userAnswers[dim].forEach((answer, idx) => {
            const question = exams[dim].questions[idx];
            const questionId = getQuestionId(question, startId + idx);
            const choiceId = getAnswerChoiceId(answer);

            if (!choiceId) {
                canSubmitToServer = false;
                return;
            }

            formData.append(`answer_${questionId}`, choiceId);
        });
    });

    if (canSubmitToServer) {
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        if (csrfMeta) {
            formData.append('csrf_token', csrfMeta.getAttribute('content'));
        }

        setAssessmentSubmitting(true);
        fetch('/submit_assessment', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
        .then(response => {
            if (response.redirected) {
                window.location.href = response.url;
                return;
            }

            return response.text().then(text => {
                if (response.ok) {
                    alert("Assessment submitted successfully.");
                    clearLocalStorage();
                    showPage('dashboard');
                } else {
                    alert(cleanSubmitErrorMessage(text));
                }
            });
        })
        .catch(() => {
            alert("Unable to submit assessment. Please check your connection and try again.");
        })
        .finally(() => {
            setAssessmentSubmitting(false);
        });
        return;
    }

    setAssessmentSubmitting(true);
    fetch('/api/submit-assessment', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
        },
        body: JSON.stringify({ answers: userAnswers })
    })
    .then(r => {
        if (r.status === 404) {
            // API endpoint doesn't exist yet, show local results
            alert("Assessment is saved on this device. Connect to the server to sync it.");
            showPage('dashboard');
            return null;
        }
        return r.json();
    })
    .then(data => {
        if (!data) return;
        if (data.success) {
            alert("Assessment submitted successfully!");
            clearLocalStorage();
            showPage('dashboard');
        } else if (data.error === 'not_logged_in') {
            alert("Please log in to submit your assessment.");
        } else if (data.error === 'locked') {
            alert(`Assessment locked until ${data.next_eligible}.`);
        } else {
            alert("Error: " + (data.error || "Unknown error"));
        }
    })
    .catch(() => {
        // Network error or no backend - show local results
        alert("Assessment saved locally. Connect to server to sync.");
        showPage('dashboard');
    })
    .finally(() => {
        setAssessmentSubmitting(false);
    });
}

/* == DASHBOARD == */
function loadDashboard() {
    const container = document.getElementById("imdContent");
    container.innerHTML = `<div class="no-data"><div class="big-icon">...</div><p>Loading...</p></div>`;

    // Try backend API first
    fetch('/api/dashboard-data')
        .then(r => {
            if (!r.ok) throw new Error('API error');
            return r.json();
        })
        .then(data => {
            isLoggedIn = true;
            assessmentLock = {
                locked: data.can_reassess === false,
                reason: data.can_reassess === false ? "reassessment" : "",
                next_eligible: data.next_eligible || null
            };
            if (isAssessmentLocked()) hideSubNav();
            if (data.has_data) {
                renderDashboardFromAPI(data);
            } else {
                renderNoServerAssessmentDashboard();
            }
        })
        .catch(() => {
            isLoggedIn = false;
            renderDashboardLocal();
        });
}

function renderDashboardFromAPI(data) {
    const container = document.getElementById("imdContent");
    const { latest, dimensions, gaps, history, can_reassess, next_eligible } = data;
    latestDashboardData = data;

    let html = "";

    // Lock notice
    if (!can_reassess && next_eligible) {
        html += `<div class="lock-notice">Reassessment locked until <strong>${next_eligible}</strong>.</div>`;
    }

    // Overall score
    html += `
        <div class="imd-overall">
            <div class="imd-score-circle">
                <span class="big-num">${Math.round(latest.overall)}</span>
                <span class="pct">/ 100</span>
            </div>
            <div class="imd-overall-text">
                <h3>Overall Inclusion Score</h3>
                <p>Cycle ${latest.cycle} - ${latest.type} - ${latest.date}</p>
            </div>
            <div class="imd-actions">
                <div class="imd-badge">${latest.maturity}</div>
                ${renderReportActions(latest.id)}
            </div>
        </div>`;

    html += `<div class="imd-insight-grid">
        ${renderScoreMeaningPanel(latest.overall, latest.maturity)}
        ${renderPriorityPanel(dimensions, gaps || [])}
    </div>`;

    html += renderActionRoadmap(gaps || []);

    // Timeline
    html += renderTimeline(history || [{ cycle: latest.cycle, type: latest.type, date: latest.date, overall: latest.overall }]);

    // Dimension scores
    html += `<div class="imd-section-title">Per-Dimension Scores</div><div class="dim-grid">`;
    dimensions.forEach(d => {
        html += `
            <div class="dim-card">
                <h4>${d.name}</h4>
                <div class="dim-score">${Math.round(d.score)}%</div>
                <div class="dim-level">${d.maturity}</div>
                <div class="dim-bar-track"><div class="dim-bar-fill" style="width:${d.score}%"></div></div>
                <div class="dim-severity ${d.severity}">${d.severity === 'critical' ? 'Critical gap' : d.severity === 'moderate' ? 'Moderate gap' : 'On track'}</div>
            </div>`;
    });
    html += `</div>`;

    // Gaps
    if (gaps && gaps.length > 0) {
        html += `
            <div class="imd-section-title">Gaps and Recommendations by Dimension</div>
            <div class="gap-dashboard-list">
                ${renderDashboardGapGroups(gaps)}
            </div>`;
    }

    container.innerHTML = html;
    container.querySelectorAll(".gap-filter-button").forEach(button => {
        button.addEventListener("click", () => {
            const dimension = button.dataset.dimension;
            const severity = button.dataset.severity;
            dashboardSeverityFilters[dimension] =
                dashboardSeverityFilters[dimension] === severity ? "all" : severity;
            renderDashboardFromAPI(latestDashboardData);
        });
    });
}

function renderNoServerAssessmentDashboard() {
    const container = document.getElementById("imdContent");
    container.innerHTML = `
        <div class="no-data">
            <div class="big-icon">+</div>
            <p>No completed assessments yet.</p>
            <p style="font-size:13px;">Complete all ${DIMENSION_ORDER.length} dimensions in the Diagnostic Engine to see scores here.</p>
        </div>
        ${renderTimeline([])}`;
}

function renderDashboardLocal() {
    const container = document.getElementById("imdContent");
    const scores = computeLocalScores();

    // Check for any progress
    if (scores.completedCount === 0) {
        renderNoServerAssessmentDashboard();
        return;
    }

    let html = "";

    // Overall (even if partial)
    html += `
        <div class="imd-overall">
            <div class="imd-score-circle">
                <span class="big-num">${Math.round(scores.overall)}</span>
                <span class="pct">/ 100</span>
            </div>
            <div class="imd-overall-text">
                <h3>${scores.isComplete ? 'Overall Inclusion Score' : 'Current Progress'}</h3>
                <p>${scores.completedCount} of 5 dimensions completed${!isLoggedIn ? ' (Local mode)' : ''}</p>
            </div>
            <div class="imd-badge">${scores.maturity || 'N/A'}</div>
        </div>`;

    // Timeline
    html += renderScoreMeaningPanel(scores.overall, scores.maturity);
    html += renderTimeline([]);

    // Dimension cards
    html += `<div class="imd-section-title">Per-Dimension Scores</div><div class="dim-grid">`;
    DIMENSION_ORDER.forEach(dim => {
        const d = scores.dimensions[dim];
        if (d) {
            html += `
                <div class="dim-card">
                    <h4>${exams[dim].title}</h4>
                    <div class="dim-score">${Math.round(d.score)}%</div>
                    <div class="dim-level">${d.maturity}</div>
                    <div class="dim-bar-track"><div class="dim-bar-fill" style="width:${d.score}%"></div></div>
                    <div class="dim-severity ${d.severity}">${d.severity === 'critical' ? 'Critical gap' : d.severity === 'moderate' ? 'Moderate gap' : 'On track'}</div>
                </div>`;
        } else {
            html += `
                <div class="dim-card">
                    <h4>${exams[dim].title}</h4>
                    <div style="color:#ccc;font-size:13px;padding:20px 0;">Not completed</div>
                </div>`;
        }
    });
    html += `</div>`;

    if (!isLoggedIn) {
        html += `<p style="text-align:center;font-size:12px;color:#888;margin-top:20px;">Log in to save your assessment to the server.</p>`;
    }

    container.innerHTML = html;
}

/* == ASSESSMENT TIMELINE == */
function renderTimeline(history) {
    const steps = [
        { label: "Initial Assessment", month: 0 },
        { label: "6-Month Assessment", month: 6 },
        { label: "12-Month Assessment", month: 12 }
    ];

    let html = `<div class="imd-section-title">Assessment Timeline</div><div class="timeline-container"><div class="timeline-row">`;

    steps.forEach((step, idx) => {
        const record = history[idx];
        let circleClass = "locked";
        let dateText = "Locked";
        let scoreText = "";

        if (record) {
            circleClass = "completed";
            dateText = record.date || "";
            scoreText = `${Math.round(record.overall)}%`;
        } else if (idx === history.length) {
            circleClass = "current";
            dateText = "Ready";
        }

        html += `
            <div class="timeline-step">
                <div class="timeline-circle ${circleClass}">${step.month}</div>
                <div class="timeline-label">${step.label}</div>
                <div class="timeline-date">${dateText}</div>
                ${scoreText ? `<div class="timeline-score-badge">${scoreText}</div>` : ''}
            </div>`;
    });

    html += `</div></div>`;
    return html;
}