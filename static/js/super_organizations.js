function openContactModal(name, email, number, position, status) {
  document.getElementById("modalName").textContent = name || "N/A";
  document.getElementById("modalEmail").textContent = email || "N/A";
  document.getElementById("modalNumber").textContent = number || "N/A";
  document.getElementById("modalPosition").textContent = position || "N/A";
  document.getElementById("modalStatus").textContent = status || "N/A";

  document.getElementById("contactModal").style.display = "flex";
}

function closeContactModal() {
  document.getElementById("contactModal").style.display = "none";
}

function openEditOrgModal(id, companyName, industry, companySize, companyNumber, status) {
  const form = document.getElementById("editOrgForm");

  form.action = `/super-admin/organizations/edit/${id}`;

  document.getElementById("editCompanyName").value = companyName || "";
  document.getElementById("editIndustry").value = industry || "";
  document.getElementById("editCompanySize").value = companySize || "";
  document.getElementById("editCompanyNumber").value = companyNumber || "";
  document.getElementById("editStatus").value = status || "approved";

  document.getElementById("editOrgModal").style.display = "flex";
}

function closeEditOrgModal() {
  document.getElementById("editOrgModal").style.display = "none";
}