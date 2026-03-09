const notice = document.getElementById('notice');
const session = BANK.session;

if (!session) {
  window.location.href = '/login';
}

function paintMember() {
  document.getElementById('m-name').textContent = `${session.full_name} (${session.role})`;
  document.getElementById('m-account').textContent = session.account.account_number;
  document.getElementById('m-balance').textContent = money(session.account.balance);
}

function renderStatement(rows) {
  const body = document.getElementById('statement-body');
  body.innerHTML = '';
  rows.forEach((row) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${new Date(row.created_at).toLocaleString('pt-BR')}</td><td>${row.type}</td><td>${money(row.amount)}</td><td>${row.description || '-'} ${row.related_account ? `(${row.related_account})` : ''}</td>`;
    body.appendChild(tr);
  });
}

function renderPix(rows) {
  const body = document.getElementById('pix-body');
  body.innerHTML = '';
  rows.forEach((row) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${row.key_type}</td><td>${row.key_value}</td>`;
    body.appendChild(tr);
  });
}

async function refreshData() {
  const [statement, pix] = await Promise.all([
    api(`/api/accounts/${session.id}/statement`),
    api(`/api/pix/${session.id}`),
  ]);
  renderStatement(statement);
  renderPix(pix);
}

document.getElementById('transfer-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    const payload = Object.fromEntries(new FormData(event.target).entries());
    payload.sender_member_id = session.id;
    payload.amount = Number(payload.amount);
    await api('/api/transfer', { method: 'POST', body: JSON.stringify(payload) });
    const updated = await api('/api/login', {
      method: 'POST',
      body: JSON.stringify(session.auth),
    });
    BANK.session = { ...updated, auth: session.auth };
    Object.assign(session, { ...updated, auth: session.auth });
    paintMember();
    await refreshData();
    setNotice(notice, 'Transferência realizada com sucesso.');
    event.target.reset();
  } catch (error) {
    setNotice(notice, error.message, true);
  }
});

document.getElementById('pix-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    const payload = Object.fromEntries(new FormData(event.target).entries());
    payload.member_id = session.id;
    await api('/api/pix', { method: 'POST', body: JSON.stringify(payload) });
    await refreshData();
    setNotice(notice, 'Chave Pix cadastrada.');
    event.target.reset();
  } catch (error) {
    setNotice(notice, error.message, true);
  }
});

document.getElementById('logout-link').addEventListener('click', (event) => {
  event.preventDefault();
  BANK.clearSession();
  window.location.href = '/login';
});

paintMember();
refreshData().catch((error) => setNotice(notice, error.message, true));
