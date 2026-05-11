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