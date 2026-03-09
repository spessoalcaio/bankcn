# Banco RPG Virtual (3 Poderes)

Sistema bancário para RPG virtual com backend, frontend e banco de dados, pronto para hospedagem web.

## Órgãos suportados inicialmente
- Câmara dos Deputados
- STF
- Poder Executivo
- Polícia Federal (PF)
- MPU

## Funcionalidades implementadas
- Cadastro de membros por órgão/cargo
- Salário base por cargo (valores aproximados da vida real) e opção de salário customizado
- Criação automática de conta bancária
- Login de membro
- Saldo e dados da conta
- Extrato de transações
- Transferências internas
- Cadastro/listagem de chaves Pix
- Painel administrativo (depósito e criação de cargos com token)

## Frontend (páginas separadas)
- `/` Portal inicial
- `/login` Página de login
- `/register` Página de registro
- `/dashboard` Painel individual do usuário
- `/admin` Painel administrativo

## Stack
- **Backend**: Flask + SQLite
- **Frontend**: HTML/CSS/JS multipágina
- **Banco de dados**: SQLite (arquivo local `rpg_bank.db`)
- **Deploy**: Gunicorn + Docker

## Como rodar localmente
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Acesse: `http://localhost:8000`

## Rodar com Docker
```bash
docker compose up --build
```

## API principal
- `GET /api/bootstrap`
- `POST /api/register`
- `POST /api/login`
- `GET /api/accounts/<member_id>/statement`
- `POST /api/transfer`
- `POST /api/pix`
- `GET /api/pix/<member_id>`
- `POST /api/admin/deposit` (header `X-Admin-Token`)
- `POST /api/admin/roles` (header `X-Admin-Token`)

## Observações de segurança para produção
- Trocar `ADMIN_TOKEN` por segredo forte
- Usar HTTPS e proxy reverso (Nginx/Cloudflare)
- Separar banco para PostgreSQL em escala maior
- Implementar autenticação com JWT/sessões e controle de permissão por perfil
