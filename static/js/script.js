/* =========================================
   IIS - DIAGNOSTIC ENGINE (CLEAN FULL VERSION)
========================================= */

/* -----------------------------
   EXAM QUESTION BANK (ALL 10 QUESTIONS EACH)
------------------------------ */
const exams = {

    Hiring: {
        title: "Hiring Assessment",
        instructions: "Select the answer that best describes your organization's current state.",
        questions: [
            {
                q: "How are your job postings designed to attract candidates with disabilities?",
                options: [
                    { text: "All postings explicitly welcome PWD applicants and state accommodations.", score: 4 },
                    { text: "Most postings include equal opportunity and mention accommodations upon request.", score: 3 },
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
                q: "Are recruiters trained in disability inclusion?",
                options: [
                    { text: "Mandatory structured training", score: 4 },
                    { text: "Basic awareness training", score: 3 },
                    { text: "Optional training only", score: 2 },
                    { text: "No training", score: 1 }
                ]
            },
            {
                q: "Is accommodation discussed during hiring?",
                options: [
                    { text: "Proactively discussed", score: 4 },
                    { text: "Mentioned if asked", score: 3 },
                    { text: "Rarely discussed", score: 2 },
                    { text: "Never discussed", score: 1 }
                ]
            },
            {
                q: "Are interview processes accessible?",
                options: [
                    { text: "Fully accessible formats available", score: 4 },
                    { text: "Mostly accessible", score: 3 },
                    { text: "Some barriers exist", score: 2 },
                    { text: "Not accessible", score: 1 }
                ]
            },
            {
                q: "Are hiring managers trained on inclusion?",
                options: [
                    { text: "Mandatory training required", score: 4 },
                    { text: "General awareness training", score: 3 },
                    { text: "Optional training", score: 2 },
                    { text: "No training", score: 1 }
                ]
            },
            {
                q: "Is bias checked in hiring decisions?",
                options: [
                    { text: "Formal bias review system", score: 4 },
                    { text: "Informal review", score: 3 },
                    { text: "Rarely checked", score: 2 },
                    { text: "Not checked", score: 1 }
                ]
            },
            {
                q: "Are alternative assessments offered?",
                options: [
                    { text: "Always available", score: 4 },
                    { text: "Sometimes available", score: 3 },
                    { text: "Rarely offered", score: 2 },
                    { text: "Not offered", score: 1 }
                ]
            },
            {
                q: "Is candidate feedback collected?",
                options: [
                    { text: "Systematically collected", score: 4 },
                    { text: "Occasionally collected", score: 3 },
                    { text: "Rarely collected", score: 2 },
                    { text: "Never collected", score: 1 }
                ]
            },
            {
                q: "Is hiring success for PWD tracked?",
                options: [
                    { text: "Tracked and reported", score: 4 },
                    { text: "Partially tracked", score: 3 },
                    { text: "Inconsistent tracking", score: 2 },
                    { text: "Not tracked", score: 1 }
                ]
            }
        ]
    },

    Onboarding: {
        title: "Onboarding Assessment",
        instructions: "Select the answer that best describes your organization's current state.",
        questions: [
            {
                q: "How does your organization prepare PWD hires before Day 1?",
                options: [
                    { text: "Structured onboarding checklist", score: 4 },
                    { text: "Basic preparation", score: 3 },
                    { text: "Case-by-case", score: 2 },
                    { text: "None", score: 1 }
                ]
            },
            {
                q: "How accessible are onboarding materials?",
                options: [
                    { text: "Fully accessible (WCAG + formats)", score: 4 },
                    { text: "Mostly accessible", score: 3 },
                    { text: "Partially accessible", score: 2 },
                    { text: "Not accessible", score: 1 }
                ]
            },
            {
                q: "Is a buddy or mentor assigned?",
                options: [
                    { text: "Structured inclusion buddy", score: 4 },
                    { text: "Informal buddy", score: 3 },
                    { text: "Optional only", score: 2 },
                    { text: "None", score: 1 }
                ]
            },
            {
                q: "How quickly are accommodations handled?",
                options: [
                    { text: "Within 5 days", score: 4 },
                    { text: "Within 2 weeks", score: 3 },
                    { text: "Slow process", score: 2 },
                    { text: "Not tracked", score: 1 }
                ]
            },
            {
                q: "Are managers trained for onboarding PWD?",
                options: [
                    { text: "Mandatory training", score: 4 },
                    { text: "General awareness", score: 3 },
                    { text: "Optional training", score: 2 },
                    { text: "No training", score: 1 }
                ]
            },
            {
                q: "Are expectations clearly set?",
                options: [
                    { text: "Structured 30-60-90 plan", score: 4 },
                    { text: "Mostly clear", score: 3 },
                    { text: "Vague", score: 2 },
                    { text: "Unclear", score: 1 }
                ]
            },
            {
                q: "Is onboarding orientation accessible?",
                options: [
                    { text: "Fully accessible orientation", score: 4 },
                    { text: "Mostly accessible", score: 3 },
                    { text: "Partial support", score: 2 },
                    { text: "Not accessible", score: 1 }
                ]
            },
            {
                q: "Are digital tools ready on Day 1?",
                options: [
                    { text: "Pre-configured IT setup", score: 4 },
                    { text: "Configured upon request", score: 3 },
                    { text: "Delayed setup", score: 2 },
                    { text: "Not ready", score: 1 }
                ]
            },
            {
                q: "Are PWD employees introduced properly?",
                options: [
                    { text: "Structured inclusive intro", score: 4 },
                    { text: "Informal intro", score: 3 },
                    { text: "Manager only", score: 2 },
                    { text: "No structure", score: 1 }
                ]
            },
            {
                q: "Is onboarding experience monitored?",
                options: [
                    { text: "Day 7/30/90 tracking", score: 4 },
                    { text: "Occasional check-ins", score: 3 },
                    { text: "Informal only", score: 2 },
                    { text: "Not monitored", score: 1 }
                ]
            }
        ]
    },

    Accommodation: {
        title: "Accommodation Assessment",
        instructions: "Select the answer that best describes your organization's current state.",
        questions: [
            {
                q: "Do you have a formal accommodation policy?",
                options: [
                    { text: "Comprehensive policy", score: 4 },
                    { text: "Exists but unclear", score: 3 },
                    { text: "Informal only", score: 2 },
                    { text: "None", score: 1 }
                ]
            },
            {
                q: "Is request process clear?",
                options: [
                    { text: "Fully documented", score: 4 },
                    { text: "Somewhat clear", score: 3 },
                    { text: "Unclear", score: 2 },
                    { text: "No process", score: 1 }
                ]
            },
            {
                q: "Response time for accommodations?",
                options: [
                    { text: "Within 10 days", score: 4 },
                    { text: "Within 3 weeks", score: 3 },
                    { text: "Slow", score: 2 },
                    { text: "Unpredictable", score: 1 }
                ]
            },
            {
                q: "Are managers trained?",
                options: [
                    { text: "Mandatory training", score: 4 },
                    { text: "Optional training", score: 3 },
                    { text: "Basic awareness", score: 2 },
                    { text: "None", score: 1 }
                ]
            },
            {
                q: "Are office spaces accessible?",
                options: [
                    { text: "Fully accessible", score: 4 },
                    { text: "Mostly accessible", score: 3 },
                    { text: "Partially accessible", score: 2 },
                    { text: "Not accessible", score: 1 }
                ]
            },
            {
                q: "Are digital tools audited?",
                options: [
                    { text: "Fully audited", score: 4 },
                    { text: "Some tools checked", score: 3 },
                    { text: "Rarely checked", score: 2 },
                    { text: "No audit", score: 1 }
                ]
            },
            {
                q: "Assistive tech support?",
                options: [
                    { text: "Fast + structured", score: 4 },
                    { text: "On request", score: 3 },
                    { text: "Slow", score: 2 },
                    { text: "None", score: 1 }
                ]
            },
            {
                q: "Is flexible work allowed?",
                options: [
                    { text: "Formal policy", score: 4 },
                    { text: "Case-by-case", score: 3 },
                    { text: "Rare", score: 2 },
                    { text: "Not allowed", score: 1 }
                ]
            },
            {
                q: "Is confidentiality protected?",
                options: [
                    { text: "Strict protocols", score: 4 },
                    { text: "Informal HR handling", score: 3 },
                    { text: "Inconsistent", score: 2 },
                    { text: "None", score: 1 }
                ]
            },
            {
                q: "Are accommodations reviewed?",
                options: [
                    { text: "Regular reviews", score: 4 },
                    { text: "Sometimes", score: 3 },
                    { text: "Rarely", score: 2 },
                    { text: "Never", score: 1 }
                ]
            }
        ]
    },

    Retention: {
        title: "Retention Assessment",
        instructions: "Select the answer that best describes your organization's current state.",
        questions: [
            {
                q: "How does your organization's voluntary attrition rate for PWD employees compare to overall attrition?",
                options: [
                    { text: "At or below average; tracked quarterly with action triggers", score: 4 },
                    { text: "Slightly higher (≤10%); monitored annually", score: 3 },
                    { text: "10–25% higher; known but no intervention", score: 2 },
                    { text: ">25% higher or not tracked", score: 1 }
                ]
            },
            {
                q: "How equitable is access to career development for PWD employees?",
                options: [
                    { text: "Tracked with proactive gap intervention", score: 4 },
                    { text: "Available but not tracked", score: 3 },
                    { text: "Informal barriers exist", score: 2 },
                    { text: "Not monitored", score: 1 }
                ]
            },
            {
                q: "Are promotions equitable between PWD and non-PWD employees?",
                options: [
                    { text: "Tracked and gaps investigated", score: 4 },
                    { text: "No disability breakdown", score: 3 },
                    { text: "Assumed fair but unmeasured", score: 2 },
                    { text: "No analysis done", score: 1 }
                ]
            },
            {
                q: "How fair is performance management for PWD employees?",
                options: [
                    { text: "Annual bias review + accommodation-aware system", score: 4 },
                    { text: "Standard system with informal adjustments", score: 3 },
                    { text: "No adjustments for PWD", score: 2 },
                    { text: "Not reviewed for accessibility", score: 1 }
                ]
            },
            {
                q: "How inclusive are mentoring and sponsorship programs?",
                options: [
                    { text: "Formal program with tracked PWD participation", score: 4 },
                    { text: "Open to all employees", score: 3 },
                    { text: "Informal mentoring only", score: 2 },
                    { text: "None exists", score: 1 }
                ]
            },
            {
                q: "How is PWD exit data used?",
                options: [
                    { text: "Tracked separately and used for interventions", score: 4 },
                    { text: "Reviewed occasionally", score: 3 },
                    { text: "Not disaggregated", score: 2 },
                    { text: "Not analyzed", score: 1 }
                ]
            },
            {
                q: "How is return-to-work handled?",
                options: [
                    { text: "Formal structured return-to-work program", score: 4 },
                    { text: "Case-by-case HR support", score: 3 },
                    { text: "Informal support", score: 2 },
                    { text: "No process", score: 1 }
                ]
            },
            {
                q: "How safe do PWD employees feel raising concerns?",
                options: [
                    { text: "Measured via PWD-specific surveys and acted on", score: 4 },
                    { text: "General surveys include inclusion questions", score: 3 },
                    { text: "Assumed safe but unmeasured", score: 2 },
                    { text: "No measurement exists", score: 1 }
                ]
            },
            {
                q: "How inclusive are team activities for PWD employees?",
                options: [
                    { text: "Accessibility reviewed + alternatives provided", score: 4 },
                    { text: "Considered when issues arise", score: 3 },
                    { text: "Employees must self-advocate", score: 2 },
                    { text: "Not considered", score: 1 }
                ]
            },
            {
                q: "How is long-term PWD retention supported?",
                options: [
                    { text: "Executive-owned retention goals + tracked metrics", score: 4 },
                    { text: "Informal tracking", score: 3 },
                    { text: "Manager responsibility only", score: 2 },
                    { text: "No strategy", score: 1 }
                ]
            }
        ]
    },

    Culture: {
        title: "Culture Assessment",
        instructions: "Select the answer that best describes your organization's current state.",
        questions: [
            {
                q: "How visibly do senior leaders champion disability inclusion?",
                options: [
                    { text: "Active public leadership + inclusion embedded in agenda", score: 4 },
                    { text: "Some informal support", score: 3 },
                    { text: "Handled by HR only", score: 2 },
                    { text: "No leadership engagement", score: 1 }
                ]
            },
            {
                q: "Is there a disability-specific inclusion policy?",
                options: [
                    { text: "Formal policy with accountability", score: 4 },
                    { text: "Included in DEI policy", score: 3 },
                    { text: "Generic equal opportunity only", score: 2 },
                    { text: "None", score: 1 }
                ]
            },
            {
                q: "How is inclusive language enforced?",
                options: [
                    { text: "Formal guide + enforcement", score: 4 },
                    { text: "General guidelines", score: 3 },
                    { text: "Informal encouragement", score: 2 },
                    { text: "No guidance", score: 1 }
                ]
            },
            {
                q: "What disability awareness training exists?",
                options: [
                    { text: "Mandatory annual training", score: 4 },
                    { text: "Available but not required", score: 3 },
                    { text: "Low participation", score: 2 },
                    { text: "None", score: 1 }
                ]
            },
            {
                q: "Is there a PWD ERG?",
                options: [
                    { text: "Formal ERG with budget and sponsor", score: 4 },
                    { text: "Informal group", score: 3 },
                    { text: "Interest only", score: 2 },
                    { text: "None", score: 1 }
                ]
            },
            {
                q: "How are disability awareness events handled?",
                options: [
                    { text: "Structured annual programming", score: 4 },
                    { text: "Key dates acknowledged", score: 3 },
                    { text: "Informal recognition", score: 2 },
                    { text: "Not recognized", score: 1 }
                ]
            },
            {
                q: "How is PWD feedback collected?",
                options: [
                    { text: "PWD-specific feedback tracked and acted on", score: 4 },
                    { text: "General surveys include inclusion items", score: 3 },
                    { text: "Informal feedback only", score: 2 },
                    { text: "No feedback system", score: 1 }
                ]
            },
            {
                q: "How inclusive are supplier and partner practices?",
                options: [
                    { text: "Inclusion embedded in procurement", score: 4 },
                    { text: "Preferred when possible", score: 3 },
                    { text: "Internal focus only", score: 2 },
                    { text: "Not considered", score: 1 }
                ]
            },
            {
                q: "How are PWD employees recognized?",
                options: [
                    { text: "Featured in recognition programs (with consent)", score: 4 },
                    { text: "General recognition only", score: 3 },
                    { text: "Rarely highlighted", score: 2 },
                    { text: "Not recognized", score: 1 }
                ]
            },
            {
                q: "How is inclusion culture measured and improved?",
                options: [
                    { text: "Annual benchmarked measurement + action plan", score: 4 },
                    { text: "General engagement surveys", score: 3 },
                    { text: "Informal review only", score: 2 },
                    { text: "Not measured", score: 1 }
                ]
            }
        ]
    }
};

/* -----------------------------
   (REST OF YOUR LOGIC UNCHANGED)
------------------------------ */

let currentExam = "";
let questionIndex = 0;
let score = 0;

function showPage(id){
    document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
    document.getElementById(id).classList.add("active");
}

function startExam(type){
    currentExam = type;
    questionIndex = 0;
    score = 0;
    showPage("diagnostic");
    loadQuestion();
}

function loadQuestion(){
    const exam = exams[currentExam];
    const q = exam.questions[questionIndex];

    document.getElementById("questionBox").innerHTML = `
        <h3>${exam.title}</h3>
        <p>${exam.instructions}</p>
        <h4>${q.q}</h4>
        ${q.options.map(o => `<button onclick="answer(${o.score})">${o.text}</button>`).join("")}
        <p>${questionIndex+1} / ${exam.questions.length}</p>
    `;
}

function answer(val){
    score += val;
    questionIndex++;
    if(questionIndex < exams[currentExam].questions.length){
        loadQuestion();
    } else {
        finishExam();
    }
}

function finishExam(){
    const total = exams[currentExam].questions.length;
    const finalScore = (score/(total*4))*100;

    document.getElementById("resultBox").innerHTML = `
        <h2>${currentExam}</h2>
        <h1>${finalScore.toFixed(2)}%</h1>
    `;

    showPage("results");
}

window.onload = () => showPage("dashboard");