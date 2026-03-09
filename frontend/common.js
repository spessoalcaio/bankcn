const BANK = {
  get session() {
    return JSON.parse(localStorage.getItem('rpg_bank_session') || 'null');
  },
  set session(payload) {
    localStorage.setItem('rpg_bank_session', JSON.stringify(payload));
  },
  clearSession() {
    localStorage.removeItem('rpg_bank_session');
  },
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  const json = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(json.error || 'Erro inesperado na API.');
  return json;
}

function money(value) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value || 0);
}

function setNotice(node, message, isError = false) {
  node.textContent = message;
  node.classList.remove('hidden', 'error');
  if (isError) node.classList.add('error');
}
