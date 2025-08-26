from functools import wraps
from flask import session, redirect, url_for
from datetime import datetime, timedelta
from pathlib import Path
import csv, random

# ----------------------------
# ARMAZENAMENTO EM MEMÓRIA
# ----------------------------
MEM = {
    "usuarios": [],       # {id, nome, email, senha}
    "produtos": [],       # {id, nome, preco, preco_custo, preco_venda, quantidade, categoria, subcategoria, tamanho, data_chegada(str), usuario_id}
    "vendas": [],         # {id, usuario_id, data(datetime)}
    "itens_venda": []     # {id, venda_id, produto_id, quantidade, preco_unitario}
}
COUNTERS = {"usuarios": 1, "produtos": 1, "vendas": 1, "itens_venda": 1}
def _next_id(table):
    COUNTERS[table] += 1
    return COUNTERS[table] - 1

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return decorated_function

# ----------------------------
# HELPERS DE DADOS
# ----------------------------
def find_usuario_by_email(email: str):
    return next((u for u in MEM["usuarios"] if u["email"].lower() == email.lower()), None)

def get_usuario(usuario_id: int):
    return next((u for u in MEM["usuarios"] if u["id"] == usuario_id), None)

def get_produto(produto_id: int):
    return next((p for p in MEM["produtos"] if p["id"] == produto_id), None)

def add_usuario(nome: str, email: str, senha: str):
    if find_usuario_by_email(email):
        return None
    novo = {"id": _next_id("usuarios"), "nome": nome, "email": email, "senha": senha}
    MEM["usuarios"].append(novo)
    return novo

def add_produto(dados: dict):
    dados = dict(dados)
    if "id" not in dados:
        dados["id"] = _next_id("produtos")
    MEM["produtos"].append(dados)
    return dados

def add_venda(usuario_id: int, data_iso: str | datetime):
    data = datetime.fromisoformat(data_iso) if isinstance(data_iso, str) else data_iso
    v = {"id": _next_id("vendas"), "usuario_id": usuario_id, "data": data}
    MEM["vendas"].append(v)
    return v

def add_item_venda(venda_id: int, produto_id: int, quantidade: int, preco_unitario: float, _id=None):
    item = {
        "id": _id if _id is not None else _next_id("itens_venda"),
        "venda_id": venda_id,
        "produto_id": produto_id,
        "quantidade": int(quantidade),
        "preco_unitario": float(preco_unitario)
    }
    MEM["itens_venda"].append(item)
    return item

# ----------------------------
# CSV I/O
# ----------------------------
DATA_DIR = Path(__file__).resolve().parent / "instance" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def generate_synthetic_csv_if_missing(n_users=5, products_per_user=5, days=100):
    users_csv = DATA_DIR / "users.csv"
    products_csv = DATA_DIR / "products.csv"
    sales_csv = DATA_DIR / "sales.csv"
    items_csv = DATA_DIR / "items.csv"
    if users_csv.exists() and products_csv.exists() and sales_csv.exists() and items_csv.exists():
        return  # já existem

    # ---- USERS
    users = [
        {"id": i+1, "nome": n, "email": f"{n.split()[0].lower()}@demo.com", "senha":"123456"}
        for i, n in enumerate(["Admin","Ana","Beto","Camila","Diego"][:n_users])
    ]
    with users_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id","nome","email","senha"]); w.writeheader()
        for u in users: w.writerow(u)

    # ---- PRODUCTS
    base_products = [
        ("Camiseta Tech","Vestuário","Camiseta","M", 99.9, 45.0),
        ("Tênis Runner","Calçados","Tênis","42", 299.9, 170.0),
        ("Moletom Pro","Vestuário","Moletom","G", 189.9, 95.0),
        ("Boné Grip","Acessórios","Boné","U", 59.9, 22.0),
        ("Meia X","Vestuário","Meia","U", 19.9, 6.0),
    ]
    products = []
    pid = 1
    now = datetime.now().date()
    for u in users:
        for i in range(products_per_user):
            name, cat, sub, tam, pv, pc = base_products[i % len(base_products)]
            products.append({
                "id": pid, "nome": name, "preco": pv, "preco_custo": pc, "preco_venda": pv,
                "quantidade": random.randint(30, 80),
                "categoria": cat, "subcategoria": sub, "tamanho": tam,
                "data_chegada": (now - timedelta(days=random.randint(60,150))).isoformat(),
                "usuario_id": u["id"]
            })
            pid += 1
    with products_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id","nome","preco","preco_custo","preco_venda","quantidade","categoria","subcategoria","tamanho","data_chegada","usuario_id"])
        w.writeheader(); [w.writerow(p) for p in products]

    # ---- SALES + ITEMS (com sazonalidade e variância)
    sales = []
    items = []
    sid = 1
    iid = 1
    for u in users:
        start = datetime.now().date() - timedelta(days=days)
        u_products = [p for p in products if p["usuario_id"] == u["id"]]
        for d in range(days):
            day = start + timedelta(days=d)
            dow = (start + timedelta(days=d)).weekday()
            mult = 1.5 if dow >= 5 else 1.0  # fim de semana mais forte
            # nº transações no dia:
            n_tx = max(0, int(random.gauss(2.2*mult, 1)))
            for _ in range(n_tx):
                sales.append({"id": sid, "usuario_id": u["id"], "data": day.isoformat()})
                # cada venda tem 1-3 itens
                for __ in range(random.randint(1,3)):
                    p = random.choice(u_products)
                    q = max(1, int(random.gauss(2, 1)))
                    items.append({"id": iid, "venda_id": sid, "produto_id": p["id"], "quantidade": q, "preco_unitario": p["preco_venda"]})
                    iid += 1
                sid += 1

    with sales_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id","usuario_id","data"]); w.writeheader()
        for s in sales: w.writerow(s)

    with items_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id","venda_id","produto_id","quantidade","preco_unitario"]); w.writeheader()
        for it in items: w.writerow(it)

def load_from_csv():
    # limpa memória
    for k in MEM: MEM[k].clear()
    COUNTERS.update({"usuarios": 1, "produtos": 1, "vendas": 1, "itens_venda": 1})

    users_csv = DATA_DIR / "users.csv"
    products_csv = DATA_DIR / "products.csv"
    sales_csv = DATA_DIR / "sales.csv"
    items_csv = DATA_DIR / "items.csv"

    generate_synthetic_csv_if_missing()

    # USERS
    with users_csv.open(encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            row["id"] = int(row["id"])
            MEM["usuarios"].append(row)
            COUNTERS["usuarios"] = max(COUNTERS["usuarios"], row["id"]+1)

    # PRODUCTS
    with products_csv.open(encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            row["id"] = int(row["id"]); row["preco"] = float(row["preco"])
            row["preco_custo"] = float(row["preco_custo"]); row["preco_venda"] = float(row["preco_venda"])
            row["quantidade"] = int(row["quantidade"]); row["usuario_id"] = int(row["usuario_id"])
            MEM["produtos"].append(row)
            COUNTERS["produtos"] = max(COUNTERS["produtos"], row["id"]+1)

    # SALES
    with sales_csv.open(encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            row["id"] = int(row["id"]); row["usuario_id"] = int(row["usuario_id"])
            row["data"] = datetime.fromisoformat(row["data"])
            MEM["vendas"].append(row)
            COUNTERS["vendas"] = max(COUNTERS["vendas"], row["id"]+1)

    # ITEMS
    with items_csv.open(encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            row["id"] = int(row["id"]); row["venda_id"] = int(row["venda_id"])
            row["produto_id"] = int(row["produto_id"]); row["quantidade"] = int(row["quantidade"])
            row["preco_unitario"] = float(row["preco_unitario"])
            MEM["itens_venda"].append(row)
            COUNTERS["itens_venda"] = max(COUNTERS["itens_venda"], row["id"]+1)

# carregar dados ao importar
load_from_csv()
