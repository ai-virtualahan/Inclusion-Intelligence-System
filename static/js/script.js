/* =========================================
   IIS - DIAGNOSTIC ENGINE PROTOTYPE
========================================= */

/* -----------------------------
   EXAM QUESTION BANK
------------------------------ */
const exams = {

     /* =========================
       HIRING 
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
            },
            {
                q: "What measures are in place to prevent disability bias during candidate screening?",
                options: [
                    { text: "Blind CV screening; structured rubrics used.", score: 4 },
                    { text: "Structured rubrics used; some bias awareness.", score: 3 },
                    { text: "General unconscious bias training only.", score: 2 },
                    { text: "No structured screening process.", score: 1 }
                ]
            },
            {
                q: "How does your organization ensure interviews are accessible and bias-free for PWD candidates?",
                options: [
                    { text: "Mandatory training + proactive accommodations + structured interviews.", score: 4 },
                    { text: "Accommodations provided when requested.", score: 3 },
                    { text: "Only when requested; no training.", score: 2 },
                    { text: "No process or training.", score: 1 }
                ]
            },
            {
                q: "How does your organization ensure selection criteria do not unfairly exclude PWD candidates?",
                options: [
                    { text: "Validated against essential job functions and reviewed for bias.", score: 4 },
                    { text: "HR checks obvious exclusions.", score: 3 },
                    { text: "Set by managers only.", score: 2 },
                    { text: "Never reviewed for bias.", score: 1 }
                ]
            },
            {
                q: "Does your organization set and track hiring targets for persons with disabilities?",
                options: [
                    { text: "Formal targets tracked and reported quarterly.", score: 4 },
                    { text: "Informal yearly tracking.", score: 3 },
                    { text: "No formal targets yet.", score: 2 },
                    { text: "No targets at all.", score: 1 }
                ]
            },
            {
                q: "How does your organization source candidates with disabilities?",
                options: [
                    { text: "Active partnerships with disability orgs and job fairs.", score: 4 },
                    { text: "1–2 partnerships occasionally used.", score: 3 },
                    { text: "General job boards only.", score: 2 },
                    { text: "No sourcing strategy.", score: 1 }
                ]
            },
            {
                q: "How are pre-employment assessments made accessible?",
                options: [
                    { text: "Accessible by design + alternatives always available.", score: 4 },
                    { text: "Available upon request.", score: 3 },
                    { text: "Only adjusted if requested.", score: 2 },
                    { text: "No accessibility review.", score: 1 }
                ]
            },
            {
                q: "How does your organization handle the offer stage for PWD candidates?",
                options: [
                    { text: "Proactive accommodation discussion + flexible start support.", score: 4 },
                    { text: "Discussed if raised by candidate.", score: 3 },
                    { text: "Only during onboarding.", score: 2 },
                    { text: "Not discussed at all.", score: 1 }
                ]
            },
            {
                q: "How does your organization track disability hiring data?",
                options: [
                    { text: "Tracked across pipeline + reported quarterly.", score: 4 },
                    { text: "Annual tracking only.", score: 3 },
                    { text: "Collected but not analyzed.", score: 2 },
                    { text: "Not tracked.", score: 1 }
                ]
            }
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
            q: "How does your organization prepare for the arrival of a PWD new hire before their first day?",
            options: [
                { text: "A structured pre-boarding checklist is completed (workstation assessed, assistive tech installed, buddy assigned, access needs confirmed).", score: 4 },
                { text: "We confirm accommodation needs before Day 1 and make basic preparations, but no formal checklist is used.", score: 3 },
                { text: "We prepare for PWD new hires on a case-by-case basis with no standard process.", score: 2 },
                { text: "No specific pre-boarding preparation is made beyond standard onboarding.", score: 1 }
            ]
        },
        {
            q: "How accessible are your orientation and onboarding materials to employees with disabilities?",
            options: [
                { text: "All materials meet WCAG 2.1 AA standards, are multi-format (captioned, screen-reader friendly, large print), and tested by PWD users.", score: 4 },
                { text: "Most materials are accessible and alternative formats are available upon request.", score: 3 },
                { text: "Materials are digital but have not been audited for accessibility.", score: 2 },
                { text: "Materials are not reviewed for accessibility.", score: 1 }
            ]
        },
        {
            q: "Does your organization assign a buddy or mentor to PWD new hires during onboarding?",
            options: [
                { text: "All PWD hires are assigned a trained inclusion buddy with weekly check-ins for 90 days.", score: 4 },
                { text: "We assign a buddy but training and structure are informal.", score: 3 },
                { text: "A buddy is assigned to all new hires, but no PWD-specific support exists.", score: 2 },
                { text: "No buddy or mentor system exists.", score: 1 }
            ]
        },
        {
            q: "How quickly are accommodation needs addressed during onboarding?",
            options: [
                { text: "All requests are resolved within 5 business days with a dedicated coordinator.", score: 4 },
                { text: "Resolved within 2 weeks; HR manages process.", score: 3 },
                { text: "Handled inconsistently with no defined timeline.", score: 2 },
                { text: "No structured process for onboarding accommodations.", score: 1 }
            ]
        },
        {
            q: "Are managers trained and prepared to onboard employees with disabilities?",
            options: [
                { text: "Mandatory disability inclusion training is completed before Day 1 for relevant managers.", score: 4 },
                { text: "Training exists but is not timed to hiring and not mandatory.", score: 3 },
                { text: "Training is optional and not consistently completed.", score: 2 },
                { text: "No disability-specific manager training exists.", score: 1 }
            ]
        },
        {
            q: "How does your organization ensure PWD new hires have clear role expectations and goals from Day 1?",
            options: [
                { text: "Structured 30-60-90 day plans co-created and reviewed by HR.", score: 4 },
                { text: "Plans exist for most hires with some adjustments for PWD.", score: 3 },
                { text: "Expectations are communicated verbally only.", score: 2 },
                { text: "No structured onboarding goals or plans exist.", score: 1 }
            ]
        },
        {
            q: "How does your organization ensure workplace orientation is accessible?",
            options: [
                { text: "Personalized orientation including accessible routes, emergency plans, and assistive equipment setup.", score: 4 },
                { text: "Standard tour with adjustments when needed.", score: 3 },
                { text: "Same tour for all employees with no adaptation.", score: 2 },
                { text: "No formal workplace orientation exists.", score: 1 }
            ]
        },
        {
            q: "How does your organization ensure access to systems and tools from Day 1?",
            options: [
                { text: "All systems pre-configured for accessibility; IT provides personalized setup within first week.", score: 4 },
                { text: "Standard setup with accessibility adjustments on request.", score: 3 },
                { text: "Employees adjust accessibility settings themselves.", score: 2 },
                { text: "No accessibility review of systems/tools.", score: 1 }
            ]
        },
        {
            q: "How does your organization introduce PWD new hires to their team?",
            options: [
                { text: "Structured inclusion protocol; team briefed on respectful communication before Day 1.", score: 4 },
                { text: "Informal reminders about respectful communication.", score: 3 },
                { text: "Introductions depend on manager with no standard process.", score: 2 },
                { text: "No structured approach to introductions.", score: 1 }
            ]
        },
        {
            q: "How does your organization monitor onboarding experience of PWD new hires?",
            options: [
                { text: "Structured check-ins at Day 7, 30, and 90 with HR + manager and documented follow-ups.", score: 4 },
                { text: "At least one HR check-in within first 30 days.", score: 3 },
                { text: "Informal manager check-ins only.", score: 2 },
                { text: "No formal onboarding feedback process.", score: 1 }
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
            q: "How does your organization's voluntary attrition rate for PWD employees compare to the overall employee attrition rate?",
            options: [
                { text: "PWD voluntary attrition is at or below overall attrition; tracked quarterly with review triggers.", score: 4 },
                { text: "PWD attrition is slightly higher (up to 10% above average) and monitored annually.", score: 3 },
                { text: "PWD attrition is 10–25% higher; gap known but no intervention plan.", score: 2 },
                { text: "PWD attrition is more than 25% higher or not tracked by disability status.", score: 1 }
            ]
        },
        {
            q: "How does your organization ensure PWD employees have equitable access to career development and growth opportunities?",
            options: [
                { text: "Participation is tracked; PWD access matches non-PWD; gaps trigger outreach.", score: 4 },
                { text: "Programs are available to all; no disability-specific tracking.", score: 3 },
                { text: "Access exists but informal barriers (timing, format, awareness) remain.", score: 2 },
                { text: "No monitoring of PWD career development access.", score: 1 }
            ]
        },
        {
            q: "Are PWD employees promoted at a rate equitable to non-PWD peers at similar performance levels?",
            options: [
                { text: "Promotion equity is tracked; gaps are investigated and corrected.", score: 4 },
                { text: "Promotions are designed to be objective; no disability breakdown tracked.", score: 3 },
                { text: "Equity assumed but not measured.", score: 2 },
                { text: "No analysis of promotion equity by disability status.", score: 1 }
            ]
        },
        {
            q: "How does your organization ensure performance management is fair and accessible to PWD employees?",
            options: [
                { text: "Annual bias review; accommodations included in goal-setting; manager training exists.", score: 4 },
                { text: "Standard process applies; managers informally consider accommodations.", score: 3 },
                { text: "Standardized process; no disability adjustments considered.", score: 2 },
                { text: "No accessibility review of performance system.", score: 1 }
            ]
        },
        {
            q: "Does your organization provide mentoring or sponsorship programs inclusive of PWD employees?",
            options: [
                { text: "Formal program with disability inclusion focus, training, and tracking.", score: 4 },
                { text: "Open mentoring program; no specific PWD tracking.", score: 3 },
                { text: "Informal mentoring through networks only.", score: 2 },
                { text: "No mentoring or sponsorship programs exist.", score: 1 }
            ]
        },
        {
            q: "How does your organization use exit interview data to understand PWD employee turnover?",
            options: [
                { text: "PWD exit data is tracked separately and used to drive retention interventions.", score: 4 },
                { text: "Exit interviews are conducted; disability trends occasionally reviewed.", score: 3 },
                { text: "Exit interviews exist but disability data is not analyzed.", score: 2 },
                { text: "Exit interviews are inconsistent or not analyzed.", score: 1 }
            ]
        },
        {
            q: "How does your organization support PWD employees returning after disability-related or medical absence?",
            options: [
                { text: "Formal return-to-work program with phased plans and accommodation review.", score: 4 },
                { text: "Handled case-by-case by HR.", score: 3 },
                { text: "Employees return without structured support.", score: 2 },
                { text: "No return-to-work process exists.", score: 1 }
            ]
        },
        {
            q: "How does your organization measure psychological safety for PWD employees?",
            options: [
                { text: "PWD-specific surveys tracked; leadership acts on results.", score: 4 },
                { text: "General surveys include inclusion questions.", score: 3 },
                { text: "No formal measurement, only assumptions.", score: 2 },
                { text: "No mechanism exists.", score: 1 }
            ]
        },
        {
            q: "How does your organization ensure PWD employees are included in team activities and social events?",
            options: [
                { text: "Accessibility is reviewed before events; employees are consulted.", score: 4 },
                { text: "Accessibility considered when issues arise.", score: 3 },
                { text: "Employees must raise accessibility concerns themselves.", score: 2 },
                { text: "No consideration of accessibility in events.", score: 1 }
            ]
        },
        {
            q: "How does your organization demonstrate long-term commitment to retaining PWD employees?",
            options: [
                { text: "Executive-owned retention goals with tracked 12–24 month retention rates.", score: 4 },
                { text: "Retention is valued informally with limited tracking.", score: 3 },
                { text: "Retention handled by individual managers.", score: 2 },
                { text: "No organizational focus on long-term retention.", score: 1 }
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
            q: "How visibly do senior leaders champion disability inclusion in your organization?",
            options: [
                { text: "Leaders actively champion inclusion publicly and internally; inclusion is part of leadership agenda.", score: 4 },
                { text: "Some leaders support inclusion informally; occasional visibility at leadership level.", score: 3 },
                { text: "Inclusion is delegated to HR with limited leadership visibility.", score: 2 },
                { text: "No visible leadership commitment to disability inclusion.", score: 1 }
            ]
        },
        {
            q: "Does your organization have a formal Disability Inclusion or DEI policy that specifically addresses disability?",
            options: [
                { text: "Formal disability-specific policy exists, is reviewed annually, and has clear accountability.", score: 4 },
                { text: "General DEI policy includes disability; limited review frequency.", score: 3 },
                { text: "Equal opportunity policy exists; disability is not explicitly addressed.", score: 2 },
                { text: "No formal DEI or disability inclusion policy exists.", score: 1 }
            ]
        },
        {
            q: "How does your organization promote and enforce inclusive language related to disability?",
            options: [
                { text: "Disability-specific inclusive language guide exists and is actively enforced.", score: 4 },
                { text: "General communication guidelines exist but are not disability-specific.", score: 3 },
                { text: "Inclusive language is encouraged informally without enforcement.", score: 2 },
                { text: "No guidance on disability-inclusive language exists.", score: 1 }
            ]
        },
        {
            q: "What disability awareness training do employees receive?",
            options: [
                { text: "Mandatory annual training for all employees covering disability awareness, bias, and inclusion.", score: 4 },
                { text: "Training is available; most employees complete it but it is not mandatory.", score: 3 },
                { text: "Training exists but participation is low and not tracked.", score: 2 },
                { text: "No disability awareness training is provided.", score: 1 }
            ]
        },
        {
            q: "Does your organization have a Disability Employee Resource Group (ERG) or affinity group?",
            options: [
                { text: "Active ERG with budget, executive sponsorship, and influence in decision-making.", score: 4 },
                { text: "Informal or emerging ERG with limited support.", score: 3 },
                { text: "Interest exists but no formal ERG has been formed.", score: 2 },
                { text: "No disability ERG or affinity group exists.", score: 1 }
            ]
        },
        {
            q: "How does your organization recognize disability awareness events (e.g., International Day of Persons with Disabilities)?",
            options: [
                { text: "Structured annual programming with events, speakers, and measurable outcomes.", score: 4 },
                { text: "Key dates are acknowledged with communications and occasional events.", score: 3 },
                { text: "Awareness dates are informally recognized by some teams.", score: 2 },
                { text: "No recognition of disability awareness events.", score: 1 }
            ]
        },
        {
            q: "How does your organization collect and act on feedback from PWD employees about workplace culture?",
            options: [
                { text: "PWD-specific feedback is collected, analyzed, and acted on with transparent reporting.", score: 4 },
                { text: "General surveys include inclusion questions but are not disaggregated.", score: 3 },
                { text: "Feedback is collected informally without structured analysis.", score: 2 },
                { text: "No mechanism exists to collect PWD cultural feedback.", score: 1 }
            ]
        },
        {
            q: "How does your organization extend disability inclusion to suppliers and external partners?",
            options: [
                { text: "Inclusion standards are embedded in supplier selection and partner evaluation.", score: 4 },
                { text: "Inclusive suppliers are preferred but not formally required.", score: 3 },
                { text: "Inclusion applies internally only.", score: 2 },
                { text: "No consideration of disability inclusion in supplier relationships.", score: 1 }
            ]
        },
        {
            q: "How does your organization recognize and celebrate contributions of PWD employees?",
            options: [
                { text: "PWD contributions are highlighted (with consent) in recognition programs and communications.", score: 4 },
                { text: "PWD employees are included in general recognition programs.", score: 3 },
                { text: "PWD employees are rarely featured in recognition programs.", score: 2 },
                { text: "Disability inclusion is not considered in recognition programs.", score: 1 }
            ]
        },
        {
            q: "How does your organization measure and improve disability inclusion culture over time?",
            options: [
                { text: "Annual structured measurement with benchmarking and formal improvement plans.", score: 4 },
                { text: "General engagement surveys include inclusion insights.", score: 3 },
                { text: "Informal cultural reviews with no structured measurement.", score: 2 },
                { text: "No measurement of disability inclusion culture.", score: 1 }
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