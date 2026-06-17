document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".inquiry-action-select").forEach((select) => {
    const targetId = select.dataset.actionTarget;
    const target = document.getElementById(targetId);

    if (!target) {
      return;
    }

    const panels = target.querySelectorAll("[data-action-panel]");

    select.addEventListener("change", () => {
      panels.forEach((panel) => {
        panel.classList.toggle("is-active", panel.dataset.actionPanel === select.value);
      });

      const activePanel = target.querySelector(".inquiry-action-panel.is-active");
      if (activePanel) {
        activePanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    });
  });
});
