window.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("registrationForm");
  const passwordInput = document.getElementById("password");
  const confirmPasswordInput = document.getElementById("confirmPassword");
  const matchMessage = document.getElementById("passwordMatchMessage");

  if (!form || !passwordInput || !confirmPasswordInput || !matchMessage) {
    return;
  }

  function validatePasswordMatch() {
    const hasConfirmation = confirmPasswordInput.value.length > 0;
    const passwordsMatch = passwordInput.value === confirmPasswordInput.value;

    confirmPasswordInput.classList.remove("password-match", "password-mismatch");
    matchMessage.classList.remove("success", "error");

    if (!hasConfirmation) {
      confirmPasswordInput.setCustomValidity("");
      matchMessage.textContent = "";
      return true;
    }

    if (!passwordsMatch) {
      confirmPasswordInput.setCustomValidity("Passwords do not match.");
      confirmPasswordInput.classList.add("password-mismatch");
      matchMessage.classList.add("error");
      matchMessage.textContent = "Passwords do not match.";
      return false;
    }

    confirmPasswordInput.setCustomValidity("");
    confirmPasswordInput.classList.add("password-match");
    matchMessage.classList.add("success");
    matchMessage.textContent = "Passwords match.";
    return true;
  }

  passwordInput.addEventListener("input", validatePasswordMatch);
  confirmPasswordInput.addEventListener("input", validatePasswordMatch);

  form.addEventListener("submit", event => {
    if (!validatePasswordMatch()) {
      event.preventDefault();
      confirmPasswordInput.reportValidity();
      confirmPasswordInput.focus();
    }
  });
});
