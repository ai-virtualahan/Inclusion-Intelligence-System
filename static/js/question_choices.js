function openEditChoiceModal(choiceId, questionId, choiceText, choiceScore) {
  const form = document.getElementById("editChoiceForm");

  form.action = `/super-admin/choice/${choiceId}/edit`;

  document.getElementById("editQuestionId").value = questionId;
  document.getElementById("editChoiceText").value = choiceText;
  document.getElementById("editChoiceScore").value = choiceScore;

  document.getElementById("editChoiceModal").style.display = "flex";
}

function closeEditChoiceModal() {
  document.getElementById("editChoiceModal").style.display = "none";
}