/* =========================================
   IIS - DIAGNOSTIC ENGINE PROTOTYPE
========================================= */

/* -----------------------------
   EXAM QUESTION BANK
------------------------------ */
const exams = {

    /* =========================
       HIRING (UNCHANGED)
    ========================= */
    Hiring: {
        title: "Hiring Assessment",
        instructions: `
For each question, select the ONE answer that best describes your organization's current state.

All questions are required.

If unsure, choose closest to reality (not aspiration).
        `,
        questions: [
            {
                q: "How are your job postings designed to attract candidates with disabilities?",
                options: [
                    { text: "All postings explicitly welcome PWD applicants and state accommodations.", score: 4 },
                    { text: "Most postings include equal opportunity and mention accommodations.", score: 3 },
                    { text: "Generic equal opportunity clause only.", score: 2 },
                    { text: "No disability inclusion mentioned.", score: 1 }
                ]
            },
            {
                q: "How accessible is your job application process?",
                options: [
                    { text: "Fully accessible (WCAG compliant) with multiple formats.", score: 4 },
                    { text: "Mostly accessible; alternatives available.", score: 3 },
                    { text: "Online only; not audited.", score: 2 },
                    { text: "No accessibility review.", score: 1 }
                ]
            }
            // keep your remaining hiring questions here
        ]
    },

    /* =========================
       ONBOARDING
    ========================= */
    Onboarding: {
        title: "Onboarding Assessment",
        instructions: `
For each question, select the ONE answer that best describes your organization's current state.
All questions are required.
If unsure, choose closest to reality (not aspiration).
        `,
        questions: [
            {
                q: "How does your organization prepare PWD new hires before Day 1?",
                options: [
                    { text: "Structured checklist (workstation, assistive tech, buddy, access needs).", score: 4 },
                    { text: "Basic preparation without formal checklist.", score: 3 },
                    { text: "Case-by-case preparation only.", score: 2 },
                    { text: "No specific preparation.", score: 1 }
                ]
            },
            {
                q: "How accessible are onboarding materials?",
                options: [
                    { text: "Fully accessible (WCAG) with multiple formats and testing.", score: 4 },
                    { text: "Mostly accessible; alternatives on request.", score: 3 },
                    { text: "Not audited for accessibility.", score: 2 },
                    { text: "Not accessible or reviewed.", score: 1 }
                ]
            },
            {
                q: "Is a buddy or mentor assigned to PWD hires?",
                options: [
                    { text: "Trained inclusion buddy with structured check-ins.", score: 4 },
                    { text: "Buddy assigned but informal.", score: 3 },
                    { text: "General buddy system only.", score: 2 },
                    { text: "No buddy system.", score: 1 }
                ]
            },
            {
                q: "How quickly are accommodations handled during onboarding?",
                options: [
                    { text: "Resolved within 5 days with coordinator.", score: 4 },
                    { text: "Resolved within 2 weeks.", score: 3 },
                    { text: "No clear timeline.", score: 2 },
                    { text: "Not tracked.", score: 1 }
                ]
            },
            {
                q: "Are managers trained for onboarding PWD employees?",
                options: [
                    { text: "Mandatory, tracked training before Day 1.", score: 4 },
                    { text: "General awareness training.", score: 3 },
                    { text: "Optional training only.", score: 2 },
                    { text: "No training.", score: 1 }
                ]
            },
            {
                q: "How are role expectations set?",
                options: [
                    { text: "Structured 30-60-90 plans with HR review.", score: 4 },
                    { text: "Plans used with adjustments.", score: 3 },
                    { text: "Verbal expectations only.", score: 2 },
                    { text: "No clear expectations.", score: 1 }
                ]
            },
            {
                q: "How accessible is workplace orientation?",
                options: [
                    { text: "Fully personalized accessibility orientation.", score: 4 },
                    { text: "General orientation with adjustments.", score: 3 },
                    { text: "Standard tour only.", score: 2 },
                    { text: "No orientation.", score: 1 }
                ]
            },
            {
                q: "Are digital tools accessible from Day 1?",
                options: [
                    { text: "Pre-configured with IT support.", score: 4 },
                    { text: "Configured upon request.", score: 3 },
                    { text: "Employee configures themselves.", score: 2 },
                    { text: "Delayed setup/no review.", score: 1 }
                ]
            },
            {
                q: "How are PWD hires introduced to teams?",
                options: [
                    { text: "Structured inclusive introduction protocol.", score: 4 },
                    { text: "Informal reminders.", score: 3 },
                    { text: "Manager-led only.", score: 2 },
                    { text: "No structured approach.", score: 1 }
                ]
            },
            {
                q: "How is onboarding experience monitored?",
                options: [
                    { text: "Structured Day 7/30/90 check-ins.", score: 4 },
                    { text: "At least one HR check-in.", score: 3 },
                    { text: "Informal manager check-ins.", score: 2 },
                    { text: "No monitoring.", score: 1 }
                ]
            }
        ]
    },

    /* =========================
       ACCOMMODATION
    ========================= */
    Accommodation: {
        title: "Accommodation Assessment",
        instructions: `
For each question, select the ONE answer that best describes your organization's current state.
All questions are required.
If unsure, choose closest to reality (not aspiration).
        `,
        questions: [
            {
                q: "Does your organization have a formal accommodation policy?",
                options: [
                    { text: "Comprehensive, reviewed annually, widely communicated.", score: 4 },
                    { text: "Policy exists but not regularly communicated.", score: 3 },
                    { text: "Informal practices only.", score: 2 },
                    { text: "No policy.", score: 1 }
                ]
            },
            {
                q: "How clear is the accommodation request process?",
                options: [
                    { text: "Clear, documented, accessible step-by-step process.", score: 4 },
                    { text: "Documented but low awareness.", score: 3 },
                    { text: "Unclear and inconsistent.", score: 2 },
                    { text: "No formal process.", score: 1 }
                ]
            },
            {
                q: "What is the typical response time?",
                options: [
                    { text: "Resolved within 10 days; tracked.", score: 4 },
                    { text: "Resolved within 3 weeks.", score: 3 },
                    { text: "4–6 weeks and inconsistent.", score: 2 },
                    { text: "Unpredictable or unresolved.", score: 1 }
                ]
            },
            {
                q: "Are managers trained on accommodations?",
                options: [
                    { text: "Mandatory annual training.", score: 4 },
                    { text: "Available but not mandatory.", score: 3 },
                    { text: "General awareness only.", score: 2 },
                    { text: "No training.", score: 1 }
                ]
            },
            {
                q: "How accessible are office spaces?",
                options: [
                    { text: "100% accessible with full infrastructure.", score: 4 },
                    { text: "Mostly accessible with minor gaps.", score: 3 },
                    { text: "Partially accessible.", score: 2 },
                    { text: "Not assessed or largely inaccessible.", score: 1 }
                ]
            },
            {
                q: "Are digital tools accessibility-audited?",
                options: [
                    { text: "Fully audited annually with remediation.", score: 4 },
                    { text: "Key tools assessed.", score: 3 },
                    { text: "Informal checks only.", score: 2 },
                    { text: "No assessment.", score: 1 }
                ]
            },
            {
                q: "How is assistive technology supported?",
                options: [
                    { text: "Catalog + fast provision + IT support.", score: 4 },
                    { text: "Provided on request.", score: 3 },
                    { text: "Unclear/slow process.", score: 2 },
                    { text: "No process.", score: 1 }
                ]
            },
            {
                q: "Is flexible work used as accommodation?",
                options: [
                    { text: "Formal, stigma-free policy.", score: 4 },
                    { text: "Case-by-case approval.", score: 3 },
                    { text: "Rarely granted.", score: 2 },
                    { text: "Not recognized.", score: 1 }
                ]
            },
            {
                q: "How is confidentiality protected?",
                options: [
                    { text: "Strict protocols with consent.", score: 4 },
                    { text: "Handled by HR informally.", score: 3 },
                    { text: "Inconsistent practices.", score: 2 },
                    { text: "No protocols.", score: 1 }
                ]
            },
            {
                q: "Are accommodations reviewed over time?",
                options: [
                    { text: "Annual reviews with employee.", score: 4 },
                    { text: "Reviewed when needed.", score: 3 },
                    { text: "Rarely reviewed.", score: 2 },
                    { text: "Never reviewed.", score: 1 }
                ]
            }
        ]
    },

    /* =========================
       RETENTION
    ========================= */
    Retention: {
        title: "Retention Assessment",
        instructions: `
For each question, select the ONE answer that best describes your organization's current state.
All questions are required.
If unsure, choose closest to reality (not aspiration).
        `,
        questions: [
            {
                q: "How does PWD attrition compare to overall attrition?",
                options: [
                    { text: "Equal or lower; tracked quarterly.", score: 4 },
                    { text: "Slightly higher; monitored annually.", score: 3 },
                    { text: "Significantly higher; no plan.", score: 2 },
                    { text: "Not tracked or very high.", score: 1 }
                ]
            },
            {
                q: "Access to career development?",
                options: [
                    { text: "Equal participation; tracked.", score: 4 },
                    { text: "Available but not tracked.", score: 3 },
                    { text: "Barriers exist.", score: 2 },
                    { text: "Not monitored.", score: 1 }
                ]
            },
            {
                q: "Are promotions equitable?",
                options: [
                    { text: "Tracked and gaps addressed.", score: 4 },
                    { text: "Process is objective.", score: 3 },
                    { text: "No data.", score: 2 },
                    { text: "Not analyzed.", score: 1 }
                ]
            },
            {
                q: "Is performance management fair?",
                options: [
                    { text: "Bias-reviewed and inclusive.", score: 4 },
                    { text: "Managers aware.", score: 3 },
                    { text: "Standard only.", score: 2 },
                    { text: "Not reviewed.", score: 1 }
                ]
            },
            {
                q: "Mentoring programs?",
                options: [
                    { text: "Formal and inclusive with tracking.", score: 4 },
                    { text: "Available to all.", score: 3 },
                    { text: "Informal only.", score: 2 },
                    { text: "None.", score: 1 }
                ]
            },
            {
                q: "Use of exit interview data?",
                options: [
                    { text: "PWD-specific insights drive action.", score: 4 },
                    { text: "General trends reviewed.", score: 3 },
                    { text: "Not analyzed by disability.", score: 2 },
                    { text: "Not used.", score: 1 }
                ]
            },
            {
                q: "Return-to-work support?",
                options: [
                    { text: "Formal structured program.", score: 4 },
                    { text: "Case-by-case support.", score: 3 },
                    { text: "Informal only.", score: 2 },
                    { text: "No process.", score: 1 }
                ]
            },
            {
                q: "Psychological safety?",
                options: [
                    { text: "Measured regularly; action taken.", score: 4 },
                    { text: "General surveys only.", score: 3 },
                    { text: "No data.", score: 2 },
                    { text: "Not measured.", score: 1 }
                ]
            },
            {
                q: "Inclusion in team activities?",
                options: [
                    { text: "Accessibility reviewed for all events.", score: 4 },
                    { text: "Considered but not consistent.", score: 3 },
                    { text: "Employee must raise issues.", score: 2 },
                    { text: "Not considered.", score: 1 }
                ]
            },
            {
                q: "Long-term retention commitment?",
                options: [
                    { text: "Executive ownership + tracked metrics.", score: 4 },
                    { text: "Informal tracking.", score: 3 },
                    { text: "Manager-level only.", score: 2 },
                    { text: "No focus.", score: 1 }
                ]
            }
        ]
    },

    /* =========================
       CULTURE
    ========================= */
    Culture: {
        title: "Culture Assessment",
        instructions: `
For each question, select the ONE answer that best describes your organization's current state.
All questions are required.
If unsure, choose closest to reality (not aspiration).
        `,
        questions: [
            {
                q: "Do leaders champion disability inclusion?",
                options: [
                    { text: "Highly visible and consistent leadership action.", score: 4 },
                    { text: "Some leaders active.", score: 3 },
                    { text: "HR-led only.", score: 2 },
                    { text: "Not a priority.", score: 1 }
                ]
            },
            {
                q: "Is there a disability inclusion policy?",
                options: [
                    { text: "Formal, reviewed, with accountability.", score: 4 },
                    { text: "General DEI policy.", score: 3 },
                    { text: "Generic policy only.", score: 2 },
                    { text: "None.", score: 1 }
                ]
            },
            {
                q: "How is inclusive language promoted?",
                options: [
                    { text: "Formal guide + enforcement.", score: 4 },
                    { text: "General guidelines.", score: 3 },
                    { text: "Informal only.", score: 2 },
                    { text: "No guidance.", score: 1 }
                ]
            },
            {
                q: "Employee disability awareness training?",
                options: [
                    { text: "Mandatory annual training.", score: 4 },
                    { text: "Available but not required.", score: 3 },
                    { text: "Low participation.", score: 2 },
                    { text: "None.", score: 1 }
                ]
            },
            {
                q: "PWD ERG or affinity group?",
                options: [
                    { text: "Formal, funded, executive-backed.", score: 4 },
                    { text: "Exists but limited.", score: 3 },
                    { text: "Planned only.", score: 2 },
                    { text: "None.", score: 1 }
                ]
            },
            {
                q: "Disability awareness events?",
                options: [
                    { text: "Structured annual programming.", score: 4 },
                    { text: "Occasional events.", score: 3 },
                    { text: "Informal recognition.", score: 2 },
                    { text: "None.", score: 1 }
                ]
            },
            {
                q: "PWD feedback collection?",
                options: [
                    { text: "Tracked, shared, acted on.", score: 4 },
                    { text: "General surveys only.", score: 3 },
                    { text: "Informal feedback.", score: 2 },
                    { text: "None.", score: 1 }
                ]
            },
            {
                q: "Supplier inclusion?",
                options: [
                    { text: "Embedded in procurement.", score: 4 },
                    { text: "Preferred when possible.", score: 3 },
                    { text: "Internal only.", score: 2 },
                    { text: "Not considered.", score: 1 }
                ]
            },
            {
                q: "Recognition of PWD employees?",
                options: [
                    { text: "Actively highlighted with consent.", score: 4 },
                    { text: "General recognition.", score: 3 },
                    { text: "Rarely highlighted.", score: 2 },
                    { text: "Not considered.", score: 1 }
                ]
            },
            {
                q: "How is inclusion culture measured?",
                options: [
                    { text: "Formal benchmarking + improvement plan.", score: 4 },
                    { text: "General surveys.", score: 3 },
                    { text: "Informal reviews.", score: 2 },
                    { text: "Not measured.", score: 1 }
                ]
            }
        ]
    }
};

/* -----------------------------
   STATE
------------------------------ */
let currentExam = "";
let questionIndex = 0;
let score = 0;

/* -----------------------------
   PAGE SYSTEM
------------------------------ */
function showPage(id){
    document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
    document.getElementById(id).classList.add("active");
}

/* -----------------------------
   START EXAM
------------------------------ */
function startExam(type){
    currentExam = type;
    questionIndex = 0;
    score = 0;
    showPage("diagnostic");
    loadQuestion();
}

/* -----------------------------
   LOAD QUESTION
------------------------------ */
function loadQuestion(){
    const exam = exams[currentExam];
    const q = exam.questions[questionIndex];

    document.getElementById("questionBox").innerHTML = `
        <h3>${exam.title}</h3>
        <p>${exam.instructions}</p>
        <h4>${q.q}</h4>
        ${q.options.map(o => `
            <button onclick="answer(${o.score})">${o.text}</button>
        `).join("")}
        <p>Question ${questionIndex + 1} of ${exam.questions.length}</p>
    `;
}

/* -----------------------------
   ANSWER
------------------------------ */
function answer(val){
    score += val;
    questionIndex++;
    if(questionIndex < exams[currentExam].questions.length){
        loadQuestion();
    } else {
        finishExam();
    }
}

/* -----------------------------
   FINISH (NO BACKEND)
------------------------------ */
function finishExam(){
    const total = exams[currentExam].questions.length;
    const finalScore = (score / (total * 4)) * 100;

    document.getElementById("resultBox").innerHTML = `
        <h2>${currentExam} Result</h2>
        <h1>${finalScore.toFixed(2)}</h1>
        <p>
            ${
                finalScore >= 80 ? "Exemplar" :
                finalScore >= 60 ? "Leading" :
                finalScore >= 40 ? "Advancing" :
                finalScore >= 20 ? "Developing" :
                "Emerging"
            }
        </p>
        <button onclick="showPage('dashboard')">Back</button>
    `;

    showPage("results");
}

/* -----------------------------
   INIT
------------------------------ */
window.onload = () => showPage("dashboard");