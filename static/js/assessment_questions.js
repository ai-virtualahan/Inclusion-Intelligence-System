let currentQuestionId = null;

function openChoicesModal(questionId, questionText) {
  currentQuestionId = questionId;

  document.getElementById("modalQuestionText").textContent = questionText;

  fetch(`/super-admin/question/${questionId}/choices-data`)
    .then(response => response.json())
    .then(data => {
      const tbody = document.getElementById("choicesTableBody");
      tbody.innerHTML = "";

      data.choices.forEach(choice => {
        tbody.innerHTML += `
          <tr>
            <td>${choice.choice_letter}</td>
            <td>${choice.choice_text}</td>
            <td>${choice.choice_score}</td>
            <td>
              <button type="button"
                      class="action-btn edit-btn"
                      onclick="openEditChoiceForm(
                        ${choice.id},
                        '${choice.choice_letter}',
                        \`${choice.choice_text}\`,
                        ${choice.choice_score}
                      )">
                Edit
              </button>
            </td>
          </tr>
        `;
      });

      document.getElementById("choicesModal").style.display = "flex";
    });
}

function closeChoicesModal() {
  document.getElementById("choicesModal").style.display = "none";
}

function openEditChoiceForm(choiceId, letter, text, score) {
  const form = document.getElementById("editChoiceForm");

  form.style.display = "block";
  form.action = `/super-admin/choice/${choiceId}/edit`;

  document.getElementById("editChoiceLetter").value = letter;
  document.getElementById("editChoiceText").value = text;
  document.getElementById("editChoiceScore").value = score;
  document.getElementById("editQuestionId").value = currentQuestionId;
}

document.getElementById("editChoiceForm").addEventListener("submit", function (e) {
  e.preventDefault();

  const form = this;
  const formData = new FormData(form);

  fetch(form.action, {
    method: "POST",
    body: formData
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        form.style.display = "none";

        openChoicesModal(
          data.question_id,
          document.getElementById("modalQuestionText").textContent
        );
      }
    });
});



function toggleQuestionEdit() {
  const textarea = document.getElementById("modalQuestionText");
  const button = document.getElementById("editQuestionBtn");

  if (textarea.hasAttribute("readonly")) {
    textarea.removeAttribute("readonly");
    textarea.focus();
    button.textContent = "Save Question";
  } else {
    const formData = new FormData();
    formData.append("question_text", textarea.value);

    fetch(`/super-admin/question/${currentQuestionId}/edit`, {
      method: "POST",
      body: formData
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          textarea.setAttribute("readonly", true);
          button.textContent = "Edit Question";

          // update visible question title inside modal
          textarea.value = data.question_text;
        }
      });
  }
}