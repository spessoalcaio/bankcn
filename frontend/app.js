const logs = document.getElementById('logs');
const roleSelect = document.getElementById('role-select');
const orgSelect = document.getElementById('organization-select');

let roles = [];

function log(data) {
  logs.textContent = `${new Date().toLocaleTimeString()} - ${data}\n` + logs.textContent;
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || 'Erro na API');
  return json;
}

function renderRoles() {
  const orgId = Number(orgSelect.value);
  roleSelect.innerHTML = '';
  roles
    .filter((r) => r.organization_id === orgId)
    .forEach((r) => {
      const opt = document.createElement('option');
      opt.value = r.id;
      opt.textContent = `${r.name} - R$ ${r.base_salary.toFixed(2)}`;
      roleSelect.appendChild(opt);
    });
}

async function loadBootstrap() {
  const data = await api('/api/bootstrap');
  orgSelect.innerHTML = '';
  data.organizations.forEach((org) => {
    const opt = document.createElement('option');
    opt.value = org.id;
    opt.textContent = org.name;
    orgSelect.appendChild(opt);
  });
  roles = data.roles.map((r) => ({ ...r, organization_id: data.organizations.find((o) => o.name === r.organization).id }));
  renderRoles();
}

orgSelect.addEventListener('change', renderRoles);

document.getElementById('register-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const payload = Object.fromEntries(fd.entries());
  payload.organization_id = Number(payload.organization_id);
  payload.role_id = Number(payload.role_id);
  if (!payload.custom_salary) delete payload.custom_salary;
  else payload.custom_salary = Number(payload.custom_salary);
  const member = await api('/api/register', { method: 'POST', body: JSON.stringify(payload) });
  log(`Membro cadastrado: ${member.full_name} | Conta ${member.account.account_number}`);
  e.target.reset();
  await loadBootstrap();
});

document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const payload = Object.fromEntries(new FormData(e.target).entries());
  const member = await api('/api/login', { method: 'POST', body: JSON.stringify(payload) });
  document.getElementById('account-panel').classList.remove('hidden');
  document.getElementById('account-data').textContent = JSON.stringify(member, null, 2);
  log(`Login bem-sucedido: ${member.full_name}`);
});

document.getElementById('transfer-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const payload = Object.fromEntries(new FormData(e.target).entries());
  payload.sender_member_id = Number(payload.sender_member_id);
  payload.amount = Number(payload.amount);
  const res = await api('/api/transfer', { method: 'POST', body: JSON.stringify(payload) });
  log(res.message);
});

document.getElementById('deposit-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const payload = {
    member_id: Number(fd.get('member_id')),
    amount: Number(fd.get('amount')),
    description: 'Depósito de administração',
  };
  const token = fd.get('admin_token');
  const res = await api('/api/admin/deposit', {
    method: 'POST',
    headers: { 'X-Admin-Token': token },
    body: JSON.stringify(payload),
  });
  log(res.message);
});

loadBootstrap().catch((err) => log(`Falha no bootstrap: ${err.message}`));
