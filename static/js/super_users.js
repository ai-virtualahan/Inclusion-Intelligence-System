function openAddUserModal() {
  document.getElementById("addUserModal").style.display = "flex";
}

function closeAddUserModal() {
  document.getElementById("addUserModal").style.display = "none";
}

function openEditUserModal(
  id,
  name,
  email,
  role,
  status,
  position,
  number
) {

  const form = document.getElementById("editUserForm");

  form.action = `/super-admin/users/edit/${id}`;

  document.getElementById("editUserName").value = name || "";
  document.getElementById("editUserEmail").value = email || "";
  const roleSelect = document.getElementById("editUserRole");
  if (role && !Array.from(roleSelect.options).some(option => option.value === role)) {
    const option = document.createElement("option");
    option.value = role;
    option.textContent = role;
    roleSelect.appendChild(option);
  }
  roleSelect.value = role || "org_admin";
  document.getElementById("editUserStatus").value = status || "approved";
  document.getElementById("editUserPosition").value = position || "";
  document.getElementById("editUserNumber").value = number || "";

  document.getElementById("editUserModal").style.display = "flex";
}

function closeEditUserModal() {
  document.getElementById("editUserModal").style.display = "none";
}
