function isLoggedIn() {
  return localStorage.getItem("loggedIn") === "true";
}

function handleAuth() {
  if (isLoggedIn()) {
    localStorage.setItem("loggedIn", "false");
    window.location.reload();
    return;
  }

  window.location.href = "/login";
}

function goToAssessment() {
  window.location.href = isLoggedIn() ? "/assessment" : "/login";
}

function updateUI() {
  const loginButton = document.querySelector(".login-btn");
  const startButton = document.getElementById("startBtn");
  const assessmentButton = document.getElementById("assessmentBtn");

  if (isLoggedIn()) {
    if (loginButton) loginButton.textContent = "Logout";
    if (startButton) startButton.textContent = "Start Assessment";
    if (assessmentButton) assessmentButton.textContent = "Start Assessment";
  } else {
    if (loginButton) loginButton.textContent = "Login";
    if (startButton) startButton.textContent = "Login to Start Assessment";
    if (assessmentButton) assessmentButton.textContent = "Login to Start Assessment";
  }
}

window.addEventListener("DOMContentLoaded", function () {
  updateUI();

  const startButton = document.getElementById("startBtn");
  const assessmentButton = document.getElementById("assessmentBtn");

  if (startButton) {
    startButton.addEventListener("click", goToAssessment);
  }

  if (assessmentButton) {
    assessmentButton.addEventListener("click", goToAssessment);
  }
});
