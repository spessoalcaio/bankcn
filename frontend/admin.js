const notice = document.getElementById('notice');
const orgSelect = document.getElementById('organization-select');

async function loadOrganizations() {
  const data = await api('/api/bootstrap');
  orgSelect.innerHTML = '';
  data.organizations.forEach((org) => {
    const option = document.createElement('option');
    option.value = org.id;
    option.textContent = org.name;
    orgSelect.appendChild(option);
  });
}

document.getElementById('deposit-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    const payload = Object.fromEntries(new FormData(event.target).entries());
    const token = payload.admin_token;
    delete payload.admin_token;
    payload.member_id = Number(payload.member_id);
    payload.amount = Number(payload.amount);
    await api('/api/admin/deposit', {
      method: 'POST',
      headers: { 'X-Admin-Token': token },
      body: JSON.stringify(payload),
    });
    setNotice(notice, 'Depósito realizado.');
  } catch (error) {
    setNotice(notice, error.message, true);
  }
});

document.getElementById('role-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    const payload = Object.fromEntries(new FormData(event.target).entries());
    const token = payload.admin_token;
    delete payload.admin_token;
    payload.organization_id = Number(payload.organization_id);
    payload.base_salary = Number(payload.base_salary);
    await api('/api/admin/roles', {
      method: 'POST',
      headers: { 'X-Admin-Token': token },
      body: JSON.stringify(payload),
    });
    setNotice(notice, 'Novo cargo criado.');
  } catch (error) {
    setNotice(notice, error.message, true);
  }
});

loadOrganizations().catch((error) => setNotice(notice, error.message, true));
