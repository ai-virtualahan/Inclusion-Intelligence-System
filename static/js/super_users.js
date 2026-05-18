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
  document.getElementById("editUserRole").value = role || "org_admin";
  document.getElementById("editUserStatus").value = status || "approved";
  document.getElementById("editUserPosition").value = position || "";
  document.getElementById("editUserNumber").value = number || "";

  document.getElementById("editUserModal").style.display = "flex";
}

function closeEditUserModal() {
  document.getElementById("editUserModal").style.display = "none";
}