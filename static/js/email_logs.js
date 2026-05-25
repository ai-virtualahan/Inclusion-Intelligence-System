const searchInput = document.getElementById("emailSearchInput");
const statusFilter = document.getElementById("statusFilter");
const typeFilter = document.getElementById("typeFilter");

function filterEmailLogs() {
  const searchValue = searchInput ? searchInput.value.toLowerCase() : "";
  const statusValue = statusFilter ? statusFilter.value.toLowerCase() : "";
  const typeValue = typeFilter ? typeFilter.value.toLowerCase() : "";

  document.querySelectorAll(".data-table tbody tr").forEach(row => {
    const rowText = row.textContent.toLowerCase();
    const rowStatus = row.dataset.status?.toLowerCase() || "";
    const rowType = row.dataset.type?.toLowerCase() || "";

    const matchesSearch = rowText.includes(searchValue);
    const matchesStatus = statusValue === "" || rowStatus === statusValue;
    const matchesType = typeValue === "" || rowType === typeValue;

    row.style.display =
      matchesSearch && matchesStatus && matchesType ? "" : "none";
  });
}

if (searchInput) searchInput.addEventListener("input", filterEmailLogs);
if (statusFilter) statusFilter.addEventListener("change", filterEmailLogs);
if (typeFilter) typeFilter.addEventListener("change", filterEmailLogs);

function openInviteModal() {
    document.getElementById("inviteModal").classList.add("show");
}

function closeInviteModal() {
    document.getElementById("inviteModal").classList.remove("show");
}

window.onclick = function(event) {
    const inviteModal = document.getElementById("inviteModal");
    const emailLogModal = document.getElementById("emailLogModal");

    if (event.target === inviteModal) {
        inviteModal.classList.remove("show");
    }

    if (event.target === emailLogModal) {
        emailLogModal.classList.remove("show");
    }
}

function parseJsonDatasetValue(value) {
  try {
    return JSON.parse(value || "\"\"");
  } catch (error) {
    return value || "";
  }
}

function openEmailLogModalFromButton(button) {
  openEmailLogModal(
    parseJsonDatasetValue(button.dataset.recipient),
    parseJsonDatasetValue(button.dataset.type),
    parseJsonDatasetValue(button.dataset.subject),
    parseJsonDatasetValue(button.dataset.message),
    parseJsonDatasetValue(button.dataset.status),
    parseJsonDatasetValue(button.dataset.sentAt),
    parseJsonDatasetValue(button.dataset.triggeredBy),
    parseJsonDatasetValue(button.dataset.error)
  );
}

function openEmailLogModal(recipient, type, subject, message, status, sentAt, triggeredBy, errorMessage) {
  document.getElementById("modalRecipient").textContent = recipient || "N/A";
  document.getElementById("modalSubject").textContent = subject || "N/A";
  document.getElementById("modalStatus").textContent = status || "N/A";
  document.getElementById("modalMessage").textContent = message || "";
  document.getElementById("modalError").textContent = errorMessage || "";

  const errorCard = document.getElementById("modalErrorCard");
  if (errorCard) {
    errorCard.style.display = errorMessage ? "block" : "none";
  }

  document.getElementById("emailLogModal").classList.add("show");
}

function closeEmailLogModal() {
  document.getElementById("emailLogModal").classList.remove("show");
}
