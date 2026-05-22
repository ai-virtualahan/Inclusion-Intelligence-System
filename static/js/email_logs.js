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
    const modal = document.getElementById("inviteModal");

    if (event.target === modal) {
        modal.classList.remove("show");
    }
}