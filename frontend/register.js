const roleSelect = document.getElementById('role-select');
const orgSelect = document.getElementById('organization-select');
const notice = document.getElementById('notice');
let roles = [];

function renderRoles() {
  const orgId = Number(orgSelect.value);
  roleSelect.innerHTML = '';
  roles.filter((role) => role.organization_id === orgId).forEach((role) => {
    const option = document.createElement('option');
    option.value = role.id;
    option.textContent = `${role.name} — ${money(role.base_salary)}`;
    roleSelect.appendChild(option);
  });
}

async function loadBootstrap() {
  const data = await api('/api/bootstrap');
  orgSelect.innerHTML = '';
  data.organizations.forEach((org) => {
    const option = document.createElement('option');
    option.value = org.id;
    option.textContent = org.name;
    orgSelect.appendChild(option);
  });

  roles = data.roles.map((role) => ({
    ...role,
    organization_id: data.organizations.find((org) => org.name === role.organization).id,
  }));
  renderRoles();
}

orgSelect.addEventListener('change', renderRoles);

document.getElementById('register-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    const payload = Object.fromEntries(new FormData(event.target).entries());
    payload.organization_id = Number(payload.organization_id);
    payload.role_id = Number(payload.role_id);
    if (!payload.custom_salary) delete payload.custom_salary;
    else payload.custom_salary = Number(payload.custom_salary);

    const member = await api('/api/register', { method: 'POST', body: JSON.stringify(payload) });
    setNotice(notice, `Conta criada com sucesso: ${member.account.account_number}`);
    event.target.reset();
    await loadBootstrap();
  } catch (error) {
    setNotice(notice, error.message, true);
  }
});

loadBootstrap().catch((error) => setNotice(notice, error.message, true));
