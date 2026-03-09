import os
import sqlite3
from datetime import datetime
from pathlib import Path
from functools import wraps

from flask import Flask, g, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "rpg_bank.db"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "admin-rpg-2026")

app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

ORGANS = [
    "Câmara dos Deputados",
    "STF",
    "Poder Executivo",
    "Polícia Federal",
    "MPU",
]

DEFAULT_ROLES = [
    ("Câmara dos Deputados", "Deputado Federal", 41234.70),
    ("Câmara dos Deputados", "Assessor Parlamentar", 13500.00),
    ("STF", "Ministro do STF", 46800.00),
    ("STF", "Analista Judiciário", 13202.62),
    ("Poder Executivo", "Presidente", 46800.00),
    ("Poder Executivo", "Ministro de Estado", 41850.92),
    ("Polícia Federal", "Delegado PF", 23800.00),
    ("Polícia Federal", "Agente PF", 13000.00),
    ("MPU", "Procurador da República", 39200.00),
    ("MPU", "Analista MPU", 12800.00),
]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.headers.get("X-Admin-Token")
        if token != ADMIN_TOKEN:
            return jsonify({"error": "Acesso administrativo negado."}), 403
        return func(*args, **kwargs)

    return wrapper


def init_db():
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            base_salary REAL NOT NULL,
            UNIQUE (organization_id, name),
            FOREIGN KEY (organization_id) REFERENCES organizations(id)
        );

        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            organization_id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            custom_salary REAL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (organization_id) REFERENCES organizations(id),
            FOREIGN KEY (role_id) REFERENCES roles(id)
        );

        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER UNIQUE NOT NULL,
            account_number TEXT UNIQUE NOT NULL,
            balance REAL NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (member_id) REFERENCES members(id)
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            related_account_id INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (account_id) REFERENCES accounts(id),
            FOREIGN KEY (related_account_id) REFERENCES accounts(id)
        );

        CREATE TABLE IF NOT EXISTS pix_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            key_type TEXT NOT NULL,
            key_value TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        );
        """
    )

    for org in ORGANS:
        db.execute("INSERT OR IGNORE INTO organizations(name) VALUES (?)", (org,))

    for org_name, role_name, salary in DEFAULT_ROLES:
        row = db.execute("SELECT id FROM organizations WHERE name = ?", (org_name,)).fetchone()
        if row:
            db.execute(
                """INSERT OR IGNORE INTO roles(organization_id, name, base_salary)
                   VALUES (?, ?, ?)""",
                (row["id"], role_name, salary),
            )
    db.commit()


def row_to_member_payload(member_id: int):
    db = get_db()
    row = db.execute(
        """
        SELECT m.id, m.full_name, m.username, m.custom_salary,
               o.name AS organization, r.name AS role, r.base_salary,
               a.id AS account_id, a.account_number, a.balance
        FROM members m
        JOIN organizations o ON o.id = m.organization_id
        JOIN roles r ON r.id = m.role_id
        JOIN accounts a ON a.member_id = m.id
        WHERE m.id = ?
        """,
        (member_id,),
    ).fetchone()
    if not row:
        return None

    salary = row["custom_salary"] if row["custom_salary"] is not None else row["base_salary"]
    return {
        "id": row["id"],
        "full_name": row["full_name"],
        "username": row["username"],
        "organization": row["organization"],
        "role": row["role"],
        "salary": salary,
        "account": {
            "id": row["account_id"],
            "account_number": row["account_number"],
            "balance": row["balance"],
        },
    }

with app.app_context():
    init_db()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})


@app.route("/api/bootstrap", methods=["GET"])
def bootstrap():
    db = get_db()
    orgs = db.execute("SELECT id, name FROM organizations ORDER BY name").fetchall()
    roles = db.execute(
        """
        SELECT r.id, r.name, r.base_salary, o.name AS organization
        FROM roles r
        JOIN organizations o ON o.id = r.organization_id
        ORDER BY o.name, r.name
        """
    ).fetchall()
    return jsonify(
        {
            "organizations": [dict(r) for r in orgs],
            "roles": [dict(r) for r in roles],
        }
    )


@app.route("/api/register", methods=["POST"])
def register_member():
    data = request.get_json(force=True)
    required = ["full_name", "username", "password", "organization_id", "role_id"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400

    db = get_db()
    try:
        now = datetime.utcnow().isoformat()
        cur = db.execute(
            """
            INSERT INTO members(full_name, username, password_hash, organization_id, role_id, custom_salary, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["full_name"],
                data["username"],
                generate_password_hash(data["password"]),
                data["organization_id"],
                data["role_id"],
                data.get("custom_salary"),
                now,
            ),
        )
        member_id = cur.lastrowid
        account_number = f"RPG{member_id:06d}"
        db.execute(
            "INSERT INTO accounts(member_id, account_number, balance, created_at) VALUES (?, ?, 0, ?)",
            (member_id, account_number, now),
        )
        db.commit()
    except sqlite3.IntegrityError as exc:
        return jsonify({"error": f"Não foi possível cadastrar: {exc}"}), 400

    return jsonify(row_to_member_payload(member_id)), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "Informe username e password."}), 400

    db = get_db()
    row = db.execute("SELECT id, password_hash FROM members WHERE username = ?", (username,)).fetchone()
    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify({"error": "Credenciais inválidas."}), 401

    payload = row_to_member_payload(row["id"])
    return jsonify(payload)


@app.route("/api/accounts/<int:member_id>/statement", methods=["GET"])
def statement(member_id):
    db = get_db()
    account = db.execute("SELECT id FROM accounts WHERE member_id = ?", (member_id,)).fetchone()
    if not account:
        return jsonify({"error": "Conta não encontrada."}), 404

    txs = db.execute(
        """
        SELECT t.id, t.type, t.amount, t.description, t.created_at,
               a.account_number AS related_account
        FROM transactions t
        LEFT JOIN accounts a ON a.id = t.related_account_id
        WHERE t.account_id = ?
        ORDER BY t.id DESC
        LIMIT 50
        """,
        (account["id"],),
    ).fetchall()
    return jsonify([dict(t) for t in txs])


@app.route("/api/transfer", methods=["POST"])
def transfer():
    data = request.get_json(force=True)
    sender_id = data.get("sender_member_id")
    target_account = data.get("target_account_number")
    amount = float(data.get("amount", 0))
    description = data.get("description", "Transferência interna")

    if not sender_id or not target_account or amount <= 0:
        return jsonify({"error": "Parâmetros de transferência inválidos."}), 400

    db = get_db()
    sender = db.execute("SELECT id, balance FROM accounts WHERE member_id = ?", (sender_id,)).fetchone()
    receiver = db.execute(
        "SELECT id, balance FROM accounts WHERE account_number = ?", (target_account,)
    ).fetchone()
    if not sender or not receiver:
        return jsonify({"error": "Conta origem ou destino não encontrada."}), 404
    if sender["id"] == receiver["id"]:
        return jsonify({"error": "Não é permitido transferir para a própria conta."}), 400
    if sender["balance"] < amount:
        return jsonify({"error": "Saldo insuficiente."}), 400

    now = datetime.utcnow().isoformat()
    db.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (amount, sender["id"]))
    db.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, receiver["id"]))
    db.execute(
        """
        INSERT INTO transactions(account_id, type, amount, description, related_account_id, created_at)
        VALUES (?, 'TRANSFER_OUT', ?, ?, ?, ?)
        """,
        (sender["id"], amount, description, receiver["id"], now),
    )
    db.execute(
        """
        INSERT INTO transactions(account_id, type, amount, description, related_account_id, created_at)
        VALUES (?, 'TRANSFER_IN', ?, ?, ?, ?)
        """,
        (receiver["id"], amount, description, sender["id"], now),
    )
    db.commit()

    return jsonify({"message": "Transferência realizada com sucesso."})


@app.route("/api/pix", methods=["POST"])
def create_pix_key():
    data = request.get_json(force=True)
    member_id = data.get("member_id")
    key_type = data.get("key_type")
    key_value = data.get("key_value")
    if not member_id or not key_type or not key_value:
        return jsonify({"error": "Campos de chave Pix incompletos."}), 400

    db = get_db()
    account = db.execute("SELECT id FROM accounts WHERE member_id = ?", (member_id,)).fetchone()
    if not account:
        return jsonify({"error": "Conta não encontrada."}), 404

    try:
        db.execute(
            "INSERT INTO pix_keys(account_id, key_type, key_value, created_at) VALUES (?, ?, ?, ?)",
            (account["id"], key_type, key_value, datetime.utcnow().isoformat()),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Chave Pix já cadastrada."}), 400

    return jsonify({"message": "Chave Pix cadastrada."}), 201


@app.route("/api/pix/<int:member_id>", methods=["GET"])
def list_pix_keys(member_id):
    db = get_db()
    account = db.execute("SELECT id FROM accounts WHERE member_id = ?", (member_id,)).fetchone()
    if not account:
        return jsonify({"error": "Conta não encontrada."}), 404
    keys = db.execute(
        "SELECT id, key_type, key_value, created_at FROM pix_keys WHERE account_id = ? ORDER BY id DESC",
        (account["id"],),
    ).fetchall()
    return jsonify([dict(k) for k in keys])


@app.route("/api/admin/roles", methods=["POST"])
@admin_required
def admin_create_role():
    data = request.get_json(force=True)
    db = get_db()
    try:
        db.execute(
            "INSERT INTO roles(organization_id, name, base_salary) VALUES (?, ?, ?)",
            (data["organization_id"], data["name"], data["base_salary"]),
        )
        db.commit()
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"message": "Cargo criado."}), 201


@app.route("/api/admin/deposit", methods=["POST"])
@admin_required
def admin_deposit():
    data = request.get_json(force=True)
    member_id = data.get("member_id")
    amount = float(data.get("amount", 0))
    description = data.get("description", "Depósito administrativo")
    if not member_id or amount <= 0:
        return jsonify({"error": "Parâmetros inválidos."}), 400

    db = get_db()
    account = db.execute("SELECT id FROM accounts WHERE member_id = ?", (member_id,)).fetchone()
    if not account:
        return jsonify({"error": "Conta não encontrada."}), 404

    now = datetime.utcnow().isoformat()
    db.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, account["id"]))
    db.execute(
        """
        INSERT INTO transactions(account_id, type, amount, description, related_account_id, created_at)
        VALUES (?, 'DEPOSIT', ?, ?, NULL, ?)
        """,
        (account["id"], amount, description, now),
    )
    db.commit()
    return jsonify({"message": "Depósito registrado."})


@app.route("/")
def root():
    return send_from_directory(app.static_folder, "index.html")


@app.route('/login')
def login_page():
    return send_from_directory(app.static_folder, 'login.html')


@app.route('/register')
def register_page():
    return send_from_directory(app.static_folder, 'register.html')


@app.route('/dashboard')
def dashboard_page():
    return send_from_directory(app.static_folder, 'dashboard.html')


@app.route('/admin')
def admin_page():
    return send_from_directory(app.static_folder, 'admin.html')


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(host="0.0.0.0", port=8000, debug=True)
