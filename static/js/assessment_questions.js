let currentQuestionId = null;
let currentQuestionNumber = null;
let currentChoices = [];
let choicesEditMode = false;

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
  const editQuestionBtn = document.getElementById("editQuestionBtn");
  const versionContext = document.getElementById("modalVersionContext");

  questionTextarea.value = questionText || "";
  questionTextarea.setAttribute("readonly", true);
  editQuestionBtn.textContent = "Create New Version";
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
        </tr>
      `
      : `
        <tr>
          <td>${escapeHtml(choice.choice_letter)}</td>
          <td>${escapeHtml(choice.choice_text)}</td>
          <td>${escapeHtml(scoreValue)}</td>
        </tr>
      `;
  });
}

function collectEditableChoices() {
  return Array.from(document.querySelectorAll("#choicesTableBody tr")).map(row => ({
    id: Number(row.dataset.choiceId),
    choice_text: row.querySelector(".choice-edit-text").value,
    choice_score: row.querySelector(".choice-edit-score").value
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

function toggleQuestionEdit() {
  const textarea = document.getElementById("modalQuestionText");
  const button = document.getElementById("editQuestionBtn");

  if (textarea.hasAttribute("readonly")) {
    textarea.removeAttribute("readonly");
    textarea.focus();
    button.textContent = "Save as New Version";
  } else {
    const formData = new FormData();
    formData.append("question_text", textarea.value);
    formData.append("csrf_token", csrfToken());

    fetch(`/super-admin/question/${currentQuestionId}/edit`, {
      method: "POST",
      body: formData
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          currentQuestionId = data.question_id;
          textarea.setAttribute("readonly", true);
          button.textContent = "Create New Version";

          textarea.value = data.question_text;

          const rowButton = document.querySelector(`[data-question-id="${data.old_question_id}"]`);
          if (rowButton) {
            rowButton.dataset.questionId = data.question_id;
            rowButton.dataset.questionVersion = data.version;
            rowButton.dataset.questionText = JSON.stringify(data.question_text);
            const row = rowButton.closest("tr");
            const questionCell = row.children[2];
            const versionCell = row.querySelector(".version-cell");
            const statusCell = row.querySelector(".status-cell");

            questionCell.textContent = data.question_text;
            row.classList.add("new-version-row");
            if (versionCell) {
              versionCell.innerHTML = `
                <span class="version-badge version-badge-new">
                  Version ${data.version}
                </span>
              `;
            }
            if (statusCell) {
              statusCell.innerHTML = `
                <span class="record-status status-approved">
                  Active
                </span>
              `;
            }
          }

          openChoicesModal(data.question_id, data.question_text, {
            questionNumber: currentQuestionNumber,
            version: data.version
          });
        }
      });
  }
}
