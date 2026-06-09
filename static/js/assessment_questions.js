let currentQuestionId = null;
let currentQuestionNumber = null;
let currentChoices = [];
let choicesEditMode = false;
let questionEditMode = null;
let originalQuestionText = "";

function csrfToken() {
  const tokenMeta = document.querySelector('meta[name="csrf-token"]');
  return tokenMeta ? tokenMeta.getAttribute("content") : "";
}

function parseJsonDatasetValue(value) {
  try {
    return JSON.parse(value || "\"\"");
  } catch (error) {
    return value || "";
  }
}

function openChoicesModalFromButton(button) {
  currentQuestionNumber = button.dataset.questionNumber;
  openChoicesModal(
    button.dataset.questionId,
    parseJsonDatasetValue(button.dataset.questionText),
    {
      questionNumber: button.dataset.questionNumber,
      version: button.dataset.questionVersion
    }
  );
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("\"", "&quot;")
    .replaceAll("'", "&#039;");
}

function openChoicesModal(questionId, questionText, meta = {}) {
  currentQuestionId = questionId;
  currentQuestionNumber = meta.questionNumber || currentQuestionNumber;

  const questionTextarea = document.getElementById("modalQuestionText");
  const versionContext = document.getElementById("modalVersionContext");

  questionTextarea.value = questionText || "";
  originalQuestionText = questionTextarea.value;
  resetQuestionEditor();
  choicesEditMode = false;
  updateChoicesButton();

  if (versionContext) {
    const qNumber = currentQuestionNumber ? `Q${currentQuestionNumber}` : "Question";
    const version = meta.version ? `Version ${meta.version}` : "";
    versionContext.textContent = [qNumber, version].filter(Boolean).join(" - ");
  }

  fetch(`/super-admin/question/${questionId}/choices-data`)
    .then(response => response.json())
    .then(data => {
      currentChoices = data.choices || [];
      renderChoicesTable();
      document.getElementById("choicesModal").style.display = "flex";
    });
}

function closeChoicesModal() {
  document.getElementById("choicesModal").style.display = "none";
}

function updateChoicesButton() {
  const button = document.getElementById("editChoicesBtn");
  if (!button) return;
  button.textContent = choicesEditMode ? "Save Choices" : "Edit Choices";
  button.classList.toggle("edit-btn", choicesEditMode);
  button.classList.toggle("secondary-btn", !choicesEditMode);
}

function renderChoicesTable() {
  const tbody = document.getElementById("choicesTableBody");
  tbody.innerHTML = "";

  currentChoices.forEach(choice => {
    const scoreValue = Number(choice.choice_score);
    const recommendationSeverity = choice.recommendation_severity === "optional"
      ? "low"
      : choice.recommendation_severity || severityFromScore(scoreValue);
    const recommendationText = choice.recommendation_text || "";
    tbody.innerHTML += choicesEditMode
      ? `
        <tr data-choice-id="${escapeHtml(choice.id)}">
          <td>${escapeHtml(choice.choice_letter)}</td>
          <td>
            <textarea class="choice-edit-text" rows="3">${escapeHtml(choice.choice_text)}</textarea>
          </td>
          <td>
            <input class="choice-edit-score" type="number" step="0.01" min="0" max="4" value="${escapeHtml(scoreValue)}">
          </td>
          <td>
            <select class="choice-edit-rec-severity">
              ${renderSeverityOptions(recommendationSeverity)}
            </select>
          </td>
          <td>
            <textarea class="choice-edit-rec" rows="3">${escapeHtml(recommendationText)}</textarea>
          </td>
        </tr>
      `
      : `
        <tr>
          <td>${escapeHtml(choice.choice_letter)}</td>
          <td>${escapeHtml(choice.choice_text)}</td>
          <td>${escapeHtml(scoreValue)}</td>
          <td>${escapeHtml(formatSeverityLabel(recommendationSeverity))}</td>
          <td>${recommendationText ? escapeHtml(recommendationText) : '<span class="empty-rec">None</span>'}</td>
        </tr>
      `;
  });
}

function severityFromScore(scoreValue) {
  if (scoreValue <= 1) return "critical";
  if (scoreValue <= 2) return "moderate";
  if (scoreValue <= 3) return "low";
  return "none";
}

function formatSeverityLabel(severity) {
  const labels = {
    none: "None",
    low: "Low",
    moderate: "Moderate",
    critical: "Critical"
  };
  return labels[severity] || "None";
}

function renderSeverityOptions(selectedSeverity) {
  return ["none", "low", "moderate", "critical"].map(severity => `
    <option value="${severity}" ${severity === selectedSeverity ? "selected" : ""}>
      ${formatSeverityLabel(severity)}
    </option>
  `).join("");
}

function collectEditableChoices() {
  return Array.from(document.querySelectorAll("#choicesTableBody tr")).map(row => ({
    id: Number(row.dataset.choiceId),
    choice_text: row.querySelector(".choice-edit-text").value,
    choice_score: row.querySelector(".choice-edit-score").value,
    recommendation_severity: row.querySelector(".choice-edit-rec-severity").value,
    recommendation_text: row.querySelector(".choice-edit-rec").value
  }));
}

function toggleChoicesEdit() {
  if (!choicesEditMode) {
    choicesEditMode = true;
    updateChoicesButton();
    renderChoicesTable();
    return;
  }

  const choices = collectEditableChoices();

  fetch(`/super-admin/question/${currentQuestionId}/choices/edit`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken()
    },
    body: JSON.stringify({ choices })
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        currentChoices = data.choices || [];
        choicesEditMode = false;
        updateChoicesButton();
        renderChoicesTable();
      } else {
        alert(data.error || "Unable to save choices.");
      }
    })
    .catch(() => {
      alert("Unable to save choices.");
    });
}

function resetQuestionEditor() {
  const textarea = document.getElementById("modalQuestionText");
  const viewActions = document.getElementById("questionViewActions");
  const editActions = document.getElementById("questionEditActions");
  const versionNote = document.getElementById("versionNote");

  questionEditMode = null;
  textarea.setAttribute("readonly", true);
  viewActions.hidden = false;
  editActions.hidden = true;
  versionNote.textContent = "Edit this version directly or create a new version while keeping the previous version for reference.";
}

function startQuestionEdit(editMode) {
  const textarea = document.getElementById("modalQuestionText");
  const viewActions = document.getElementById("questionViewActions");
  const editActions = document.getElementById("questionEditActions");
  const saveButton = document.getElementById("saveQuestionBtn");
  const versionNote = document.getElementById("versionNote");

  questionEditMode = editMode;
  originalQuestionText = textarea.value;
  textarea.removeAttribute("readonly");
  textarea.focus();
  viewActions.hidden = true;
  editActions.hidden = false;

  if (editMode === "same_version") {
    saveButton.textContent = "Save Same Version";
    versionNote.textContent = "This updates the current question without changing its version number.";
  } else {
    saveButton.textContent = "Save as New Version";
    versionNote.textContent = "This creates the next version and keeps the previous version inactive for reference.";
  }
}

function cancelQuestionEdit() {
  const textarea = document.getElementById("modalQuestionText");
  textarea.value = originalQuestionText;
  resetQuestionEditor();
}

function saveQuestionEdit() {
  const textarea = document.getElementById("modalQuestionText");
  const questionText = textarea.value.trim();

  if (!questionText) {
    alert("Question text is required.");
    return;
  }

  const formData = new FormData();
  formData.append("question_text", questionText);
  formData.append("edit_mode", questionEditMode);
  formData.append("csrf_token", csrfToken());

  fetch(`/super-admin/question/${currentQuestionId}/edit`, {
    method: "POST",
    body: formData
  })
    .then(async response => {
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Unable to save question.");
      return data;
    })
    .then(data => {
      if (data.created_new_version) {
        const url = new URL(window.location.href);
        url.searchParams.set("open_question_id", data.question_id);
        window.location.href = url.toString();
        return;
      }

      textarea.value = data.question_text;
      originalQuestionText = data.question_text;
      resetQuestionEditor();

      const rowButton = document.querySelector(`[data-question-id="${data.question_id}"]`);
      if (rowButton) {
        rowButton.dataset.questionText = JSON.stringify(data.question_text);
        rowButton.closest("tr").children[2].textContent = data.question_text;
      }
    })
    .catch(error => {
      alert(error.message || "Unable to save question.");
    });
}

document.addEventListener("DOMContentLoaded", () => {
  const openQuestionId = document.getElementById("openQuestionId")?.value;
  if (!openQuestionId) return;

  const questionButton = document.querySelector(`[data-question-id="${openQuestionId}"]`);
  if (questionButton) openChoicesModalFromButton(questionButton);
});
