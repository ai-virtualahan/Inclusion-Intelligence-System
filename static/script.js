
/* =========================================
   IIS - LEVEL 2 DIAGNOSTIC ENGINE (UPGRADED)
========================================= */

/* -----------------------------
   EXAM QUESTION BANK (UPGRADED HIRING ONLY)
------------------------------ */
const exams = {
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
                    { text: "All postings explicitly welcome PWD applicants, state accommodations, and are published on inclusive platforms.", score: 4 },
                    { text: "Most postings include equal opportunity statement and mention accommodations upon request.", score: 3 },
                    { text: "Generic equal opportunity clause only; no active communication of accommodations.", score: 2 },
                    { text: "No disability inclusion or accommodation mention.", score: 1 }
                ]
            },
            {
                q: "How accessible is your job application process?",
                options: [
                    { text: "Fully WCAG 2.1 AA accessible; multiple formats (online, email, phone).", score: 4 },
                    { text: "Mostly accessible; alternative formats available upon request.", score: 3 },
                    { text: "Online only; not audited for accessibility.", score: 2 },
                    { text: "No accessibility review done.", score: 1 }
                ]
            },
            {
                q: "What measures prevent disability bias during screening?",
                options: [
                    { text: "Blind CV screening; structured rubrics; disability fields removed.", score: 4 },
                    { text: "Structured rubrics and bias training; disability visible.", score: 3 },
                    { text: "General bias training only.", score: 2 },
                    { text: "No bias prevention system.", score: 1 }
                ]
            },
            {
                q: "How are interviews made accessible and fair?",
                options: [
                    { text: "Interviewers trained; accommodations proactively offered; structured interviews.", score: 4 },
                    { text: "Accommodations provided when requested.", score: 3 },
                    { text: "Only reactive accommodations.", score: 2 },
                    { text: "No accommodation process.", score: 1 }
                ]
            },
            {
                q: "How are job criteria reviewed for fairness?",
                options: [
                    { text: "Roles reviewed for essential vs non-essential functions; accommodation considered.", score: 4 },
                    { text: "HR reviews obvious exclusions only.", score: 3 },
                    { text: "No formal review process.", score: 2 },
                    { text: "No inclusion lens applied.", score: 1 }
                ]
            },
            {
                q: "Does your organization set PWD hiring targets?",
                options: [
                    { text: "Formal targets with quarterly reporting.", score: 4 },
                    { text: "Informal targets with annual tracking.", score: 3 },
                    { text: "Aware but no formal targets.", score: 2 },
                    { text: "No targets.", score: 1 }
                ]
            },
            {
                q: "How do you source candidates with disabilities?",
                options: [
                    { text: "Active partnerships + job fairs + disability org engagement.", score: 4 },
                    { text: "1–2 partnerships.", score: 3 },
                    { text: "General job boards only.", score: 2 },
                    { text: "No sourcing strategy.", score: 1 }
                ]
            },
            {
                q: "How are assessments made accessible?",
                options: [
                    { text: "Accessible by default + alternative formats always available.", score: 4 },
                    { text: "Available upon request.", score: 3 },
                    { text: "Only adjusted when requested.", score: 2 },
                    { text: "Not reviewed for accessibility.", score: 1 }
                ]
            },
            {
                q: "How is the offer stage handled?",
                options: [
                    { text: "Proactive accommodation discussion + flexible onboarding planning.", score: 4 },
                    { text: "Discussed if candidate raises it.", score: 3 },
                    { text: "Discussed during onboarding only.", score: 2 },
                    { text: "No discussion at any stage.", score: 1 }
                ]
            },
            {
                q: "How is disability hiring data tracked?",
                options: [
                    { text: "Full pipeline tracking + quarterly reporting.", score: 4 },
                    { text: "Annual tracking only.", score: 3 },
                    { text: "Collected but not analyzed.", score: 2 },
                    { text: "No tracking.", score: 1 }
                ]
            }
        ]
    },

    /* PLACEHOLDER STRUCTURE (unchanged for now) */
    Onboarding: ["Onboarding accessibility?", "Training inclusivity?", "New hire support system?"],
    Accommodation: ["Ease of requesting accommodations?", "Assistive tech availability?", "HR responsiveness?"],
    Retention: ["Employee inclusion tracking?", "Accessibility support retention?", "Feedback system effectiveness?"],
    Culture: ["Inclusive workplace culture?", "Diversity respect level?", "Psychological safety?"]
};


/* -----------------------------
   STATE MANAGEMENT
------------------------------ */
let currentExam = "";
let questionIndex = 0;
let score = 0;
let answers = [];

/* -----------------------------
   PAGE SYSTEM
------------------------------ */
function showPage(pageId){

    const pages = document.querySelectorAll(".page");

    pages.forEach(page => {
        page.classList.remove("active");
    });

    const target = document.getElementById(pageId);
    if(target){
        target.classList.add("active");
    }
}

/* -----------------------------
   START EXAM
------------------------------ */
function startExam(type){

    currentExam = type;
    questionIndex = 0;
    score = 0;
    answers = [];

    showPage("diagnostic");
    loadQuestion();
}

/* -----------------------------
   LOAD QUESTION (UPGRADED)
------------------------------ */
function loadQuestion(){

    const exam = exams[currentExam];

    // SAFE CHECK (important)
    if (!exam.questions) {
        document.getElementById("questionBox").innerHTML = `
            <p>This exam is not yet fully configured.</p>
        `;
        return;
    }

    const question = exam.questions[questionIndex];

    document.getElementById("questionBox").innerHTML = `
        <h3>${exam.title}</h3>

        <p style="color:#94a3b8; margin-bottom:15px;">
            ${exam.instructions}
        </p>

        <h4>${question.q}</h4>

        ${question.options.map(opt => `
            <button onclick="answer(${opt.score})">
                ${opt.text}
            </button>
        `).join("")}

        <p style="margin-top:10px; color:#94a3b8;">
            Question ${questionIndex + 1} of ${exam.questions.length}
        </p>
    `;
}

/* -----------------------------
   ANSWER HANDLER
------------------------------ */
function answer(value){

    answers.push(value);
    score += value;

    questionIndex++;

    if(questionIndex < exams[currentExam].questions.length){
        loadQuestion();
    } else {
        finishExam();
    }
}

/* -----------------------------
   FINISH EXAM
------------------------------ */
function finishExam(){

    const total = exams[currentExam].questions.length;
    const finalScore = (score / (total * 4)) * 100;

    const payload = {
        answers,
        company: currentExam + "_Assessment",
        score: finalScore
    };

    fetch('/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {

        document.getElementById("resultBox").innerHTML = `
            <h2>${currentExam} Result</h2>

            <h1 style="font-size:42px; color:#00B8A0;">
                ${data.score.toFixed(2)}
            </h1>

            <p>
                Level:
                ${
                    data.score >= 80 ? "Exemplar" :
                    data.score >= 60 ? "Leading" :
                    data.score >= 40 ? "Advancing" :
                    data.score >= 20 ? "Developing" :
                    "Emerging"
                }
            </p>

            <button onclick="showPage('dashboard')">
                Back to Dashboard
            </button>
        `;

        document.getElementById("scoreDisplay").innerText = data.score.toFixed(2);

        showPage("results");
    })
    .catch(err => {
        console.error(err);
        alert("Error submitting results to server");
    });
}

/* -----------------------------
   BACKWARD COMPATIBILITY
------------------------------ */
function startAssessment(){
    showPage("examSelect");
}

/* -----------------------------
   INIT
------------------------------ */
window.onload = function(){
    showPage("dashboard");
};