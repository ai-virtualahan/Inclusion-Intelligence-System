function openEmailLogModal(recipient, type, subject, message, status, sentAt, triggeredBy, errorMessage) {
  document.getElementById("modalRecipient").textContent = recipient;
  document.getElementById("modalSubject").textContent = subject;
  document.getElementById("modalMessage").textContent = message || "—";
  document.getElementById("modalError").textContent = errorMessage || "No error";

  document.getElementById("emailLogModal").style.display = "flex";
}

function closeEmailLogModal() {
  document.getElementById("emailLogModal").style.display = "none";
}


const searchInput = document.getElementById("emailSearchInput");

const statusFilter = document.getElementById("statusFilter");

function filterEmailLogs() {

  const searchValue =
    searchInput.value.toLowerCase();

  const statusValue =
    statusFilter.value.toLowerCase();

  document.querySelectorAll(".data-table tbody tr")
    .forEach(row => {

      const rowText =
        row.textContent.toLowerCase();

      const rowStatus =
        row.dataset.status.toLowerCase();

      const matchesSearch =
        rowText.includes(searchValue);

      const matchesStatus =
        statusValue === "" ||
        rowStatus === statusValue;

      row.style.display =
        matchesSearch && matchesStatus
          ? ""
          : "none";
    });
}

searchInput.addEventListener(
  "input",
  filterEmailLogs
);

statusFilter.addEventListener(
  "change",
  filterEmailLogs
);