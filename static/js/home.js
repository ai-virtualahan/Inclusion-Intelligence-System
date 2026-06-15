window.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("[data-target-url]").forEach(button => {
    button.addEventListener("click", () => {
      window.location.href = button.dataset.targetUrl;
    });
  });
});
