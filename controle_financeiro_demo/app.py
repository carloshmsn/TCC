
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import math
from pathlib import Path
from datetime import date

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "financeiro.db"

app = Flask(__name__)
app.secret_key = "demo-local-troque-esta-chave"

CATEGORIES = [
    "Salário",
    "Trabalho extra",
    "Alimentação",
    "Transporte",
    "Moradia",
    "Lazer",
    "Compras",
    "Saúde",
    "Educação",
    "Outros",
]


# =========================
# BASE DE DADOS
# =========================

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def money_to_cents(value):
    """Converte valores como 12,50 ou 12.50 em centavos."""
    value = (value or "").strip()
    value = value.replace("R$", "").replace(" ", "")

    if not value:
        raise ValueError("O valor é obrigatório.")

    if "," in value:
        value = value.replace(".", "").replace(",", ".")

    amount = float(value)

    if not math.isfinite(amount) or amount <= 0:
        raise ValueError("O valor deve ser maior que zero.")

    return int(round(amount * 100))


def format_brl(cents):
    value = (cents or 0) / 100
    formatted = (
        f"{value:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
    return f"R$ {formatted}"


def init_db():
    with db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount_cents INTEGER NOT NULL
                    CHECK(amount_cents > 0),
                kind TEXT NOT NULL
                    CHECK(kind IN ('income', 'expense')),
                category TEXT NOT NULL,
                transaction_date TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                limit_cents INTEGER NOT NULL
                    CHECK(limit_cents > 0),
                month TEXT NOT NULL,
                UNIQUE(category, month)
            );

            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                target_cents INTEGER NOT NULL
                    CHECK(target_cents > 0),
                saved_cents INTEGER NOT NULL DEFAULT 0
                    CHECK(saved_cents >= 0),
                deadline TEXT
            );
        """)

        # Dados fictícios apenas quando ainda não existem movimentações.
        count = conn.execute(
            "SELECT COUNT(*) FROM transactions"
        ).fetchone()[0]

        if count == 0:
            today = date.today()
            month_start = today.replace(day=1).isoformat()

            samples = [
                (
                    "Salário",
                    150000,
                    "income",
                    "Salário",
                    month_start,
                ),
                (
                    "Passe de transporte",
                    18000,
                    "expense",
                    "Transporte",
                    today.isoformat(),
                ),
                (
                    "Mercado",
                    23500,
                    "expense",
                    "Alimentação",
                    today.isoformat(),
                ),
                (
                    "Cinema",
                    6500,
                    "expense",
                    "Lazer",
                    today.isoformat(),
                ),
            ]

            conn.executemany("""
                INSERT INTO transactions
                (description, amount_cents, kind, category, transaction_date)
                VALUES (?, ?, ?, ?, ?)
            """, samples)

            month = today.strftime("%Y-%m")

            conn.executemany("""
                INSERT OR IGNORE INTO budgets
                (category, limit_cents, month)
                VALUES (?, ?, ?)
            """, [
                ("Transporte", 20000, month),
                ("Alimentação", 30000, month),
                ("Lazer", 10000, month),
                ("Compras", 8000, month),
            ])

            conn.execute("""
                INSERT INTO goals
                (name, target_cents, saved_cents, deadline)
                VALUES (?, ?, ?, ?)
            """, (
                "Comprar um celular",
                200000,
                60000,
                None,
            ))


@app.template_filter("brl")
def brl_filter(cents):
    return format_brl(cents)


# =========================
# DASHBOARD
# =========================

@app.route("/")
def dashboard():
    today = date.today()
    month = today.strftime("%Y-%m")

    with db() as conn:
        transactions = conn.execute("""
            SELECT *
            FROM transactions
            ORDER BY transaction_date DESC, id DESC
            LIMIT 8
        """).fetchall()

        income = conn.execute("""
            SELECT COALESCE(SUM(amount_cents), 0)
            FROM transactions
            WHERE kind = 'income'
              AND substr(transaction_date, 1, 7) = ?
        """, (month,)).fetchone()[0]

        expenses = conn.execute("""
            SELECT COALESCE(SUM(amount_cents), 0)
            FROM transactions
            WHERE kind = 'expense'
              AND substr(transaction_date, 1, 7) = ?
        """, (month,)).fetchone()[0]

        budgets = conn.execute("""
            SELECT
                b.*,
                COALESCE(SUM(t.amount_cents), 0) AS spent_cents
            FROM budgets b
            LEFT JOIN transactions t
                ON t.category = b.category
                AND t.kind = 'expense'
                AND substr(t.transaction_date, 1, 7) = b.month
            WHERE b.month = ?
            GROUP BY b.id
            ORDER BY b.category
        """, (month,)).fetchall()

        goals = conn.execute("""
            SELECT *
            FROM goals
            ORDER BY id DESC
        """).fetchall()

        category_rows = conn.execute("""
            SELECT category, SUM(amount_cents) AS total
            FROM transactions
            WHERE kind = 'expense'
              AND substr(transaction_date, 1, 7) = ?
            GROUP BY category
            ORDER BY total DESC
        """, (month,)).fetchall()

    total_budget = sum(b["limit_cents"] for b in budgets)
    total_budget_spent = sum(b["spent_cents"] for b in budgets)

    return render_template(
        "index.html",
        income=income,
        expenses=expenses,
        balance=income - expenses,
        transactions=transactions,
        budgets=budgets,
        goals=goals,
        categories=CATEGORIES,
        month=month,
        today=today.isoformat(),
        total_budget=total_budget,
        total_budget_spent=total_budget_spent,
        category_rows=category_rows,
    )


# =========================
# ADICIONAR RECEITA / DESPESA
# =========================

@app.route("/transactions/add", methods=["POST"])
def add_transaction():
    description = request.form.get("description", "").strip()
    kind = request.form.get("kind", "").strip()
    category = request.form.get("category", "").strip()
    transaction_date = request.form.get("transaction_date", "").strip()

    try:
        amount_cents = money_to_cents(
            request.form.get("amount")
        )

        if not description or len(description) > 100:
            raise ValueError("Descrição inválida.")

        if kind not in ("income", "expense"):
            raise ValueError("Tipo inválido.")

        if category not in CATEGORIES:
            raise ValueError("Categoria inválida.")

        date.fromisoformat(transaction_date)

        with db() as conn:
            conn.execute("""
                INSERT INTO transactions
                (description, amount_cents, kind, category, transaction_date)
                VALUES (?, ?, ?, ?, ?)
            """, (
                description,
                amount_cents,
                kind,
                category,
                transaction_date,
            ))

        flash("Movimentação registada com sucesso!", "success")

    except (ValueError, TypeError, OverflowError, sqlite3.Error):
        flash(
            "Não foi possível registar. Verifica os dados e o valor.",
            "error",
        )

    return redirect(url_for("dashboard"))


# =========================
# AJUSTAR SALDO
# =========================


@app.route("/balance/adjust", methods=["POST"])
def adjust_balance():
    target_text = (
        request.form.get("target_balance", "")
        .strip()
        .replace("R$", "")
        .replace(" ", "")
    )

    try:
        # Permite ajustar o saldo para zero.
        if "," in target_text:
            target_text = target_text.replace(".", "")
            target_text = target_text.replace(",", ".")

        target_cents = int(round(float(target_text) * 100))

        with db() as conn:
            month = date.today().strftime("%Y-%m")

            income = conn.execute(
                """
                SELECT COALESCE(SUM(amount_cents), 0)
                FROM transactions
                WHERE kind = 'income'
                  AND substr(transaction_date, 1, 7) = ?
                """,
                (month,)
            ).fetchone()[0]

            expenses = conn.execute(
                """
                SELECT COALESCE(SUM(amount_cents), 0)
                FROM transactions
                WHERE kind = 'expense'
                  AND substr(transaction_date, 1, 7) = ?
                """,
                (month,)
            ).fetchone()[0]

            current_balance = income - expenses
            difference = target_cents - current_balance

            if difference == 0:
                flash("O saldo já corresponde ao valor indicado.", "success")
                return redirect(url_for("dashboard"))

            kind = "income" if difference > 0 else "expense"

            conn.execute(
                """
                INSERT INTO transactions
                (description, amount_cents, kind, category, transaction_date)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "Ajuste de saldo",
                    abs(difference),
                    kind,
                    "Outros",
                    date.today().isoformat()
                )
            )

        flash("Saldo ajustado e alteração registada no histórico.", "success")

    except (ValueError, TypeError):
        flash("Indica um saldo válido.", "error")

    return redirect(url_for("dashboard"))

# =========================
# EXCLUIR MOVIMENTAÇÃO
# =========================

@app.route(
    "/transactions/<int:transaction_id>/delete",
    methods=["POST"],
)
def delete_transaction(transaction_id):
    with db() as conn:
        conn.execute(
            "DELETE FROM transactions WHERE id = ?",
            (transaction_id,),
        )

    flash("Movimentação excluída.", "success")
    return redirect(url_for("dashboard"))


# =========================
# ORÇAMENTOS
# =========================

@app.route("/budgets/add", methods=["POST"])
def add_budget():
    category = request.form.get("category", "").strip()
    month = request.form.get("month", "").strip()

    try:
        limit_cents = money_to_cents(
            request.form.get("limit")
        )

        if category not in CATEGORIES:
            raise ValueError("Categoria inválida.")

        if len(month) != 7:
            raise ValueError("Mês inválido.")

        date.fromisoformat(month + "-01")

        with db() as conn:
            conn.execute("""
                INSERT INTO budgets
                (category, limit_cents, month)
                VALUES (?, ?, ?)
                ON CONFLICT(category, month)
                DO UPDATE SET limit_cents = excluded.limit_cents
            """, (
                category,
                limit_cents,
                month,
            ))

        flash("Orçamento guardado!", "success")

    except (ValueError, TypeError, OverflowError, sqlite3.Error):
        flash(
            "Não foi possível guardar o orçamento. Verifica os dados.",
            "error",
        )

    return redirect(url_for("dashboard"))


# =========================
# METAS FINANCEIRAS
# =========================

@app.route("/goals/add", methods=["POST"])
def add_goal():
    name = request.form.get("name", "").strip()
    deadline = request.form.get("deadline", "").strip() or None

    try:
        target = money_to_cents(
            request.form.get("target")
        )

        saved_text = request.form.get("saved", "").strip()

        if saved_text:
            saved = money_to_cents(saved_text)
        else:
            saved = 0

        if not name or len(name) > 100:
            raise ValueError("Nome inválido.")

        if saved > target:
            raise ValueError("O valor poupado excede a meta.")

        if deadline:
            date.fromisoformat(deadline)

        with db() as conn:
            conn.execute("""
                INSERT INTO goals
                (name, target_cents, saved_cents, deadline)
                VALUES (?, ?, ?, ?)
            """, (
                name,
                target,
                saved,
                deadline,
            ))

        flash("Meta criada com sucesso!", "success")

    except (ValueError, TypeError, OverflowError, sqlite3.Error):
        flash(
            "Verifica o nome, os valores e o prazo da meta.",
            "error",
        )

    return redirect(url_for("dashboard"))


@app.route("/goals/<int:goal_id>/contribute", methods=["POST"])
def contribute_goal(goal_id):
    try:
        amount = money_to_cents(
            request.form.get("amount")
        )

        with db() as conn:
            goal = conn.execute(
                "SELECT * FROM goals WHERE id = ?",
                (goal_id,),
            ).fetchone()

            if goal is None:
                flash("Meta não encontrada.", "error")

            elif goal["saved_cents"] + amount > goal["target_cents"]:
                flash(
                    "A contribuição ultrapassa o valor da meta.",
                    "error",
                )

            else:
                conn.execute("""
                    UPDATE goals
                    SET saved_cents = saved_cents + ?
                    WHERE id = ?
                """, (amount, goal_id))

                flash("Contribuição registada!", "success")

    except (ValueError, TypeError, OverflowError, sqlite3.Error):
        flash(
            "Introduz um valor válido para a contribuição.",
            "error",
        )

    return redirect(url_for("dashboard"))


# =========================
# INICIAR A APLICAÇÃO
# =========================

if __name__ == "__main__":
    init_db()
    app.run(debug=True)