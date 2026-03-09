const notice = document.getElementById('notice');

document.getElementById('login-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    const payload = Object.fromEntries(new FormData(event.target).entries());
    const member = await api('/api/login', { method: 'POST', body: JSON.stringify(payload) });
    BANK.session = { ...member, auth: payload };
    window.location.href = '/dashboard';
  } catch (error) {
    setNotice(notice, error.message, true);
  }
});
