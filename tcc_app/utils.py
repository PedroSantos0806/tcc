from functools import wraps
from flask import session, redirect, url_for
from datetime import datetime, timedelta
import random

# ----------------------------
# ARMAZENAMENTO EM MEMÓRIA
# ----------------------------
# Estrutura única compartilhada entre módulos
MEM = {
    "usuarios": [],       # {id, nome, email, senha}
    "produtos": [],       # {id, nome, preco, preco_custo, preco_venda, quantidade, categoria, subcategoria, tamanho, data_chegada(str 'YYYY-MM-DD'), usuario_id}
    "vendas": [],         # {id, usuario_id, data (datetime)}
    "itens_venda": []     # {id, venda_id, produto_id, quantidade, preco_unitario}
}

# Geradores simples de ID
COUNTERS = {"usuarios": 1, "produtos": 1, "vendas": 1, "itens_venda": 1}
def _next_id(table):
    COUNTERS[table] += 1
    return COUNTERS[table] - 1

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
    dados["id"] = _next_id("produtos")
    MEM["produtos"].append(dados)
    return dados

def add_venda(usuario_id: int, data_iso: str):
    data = datetime.fromisoformat(data_iso) if isinstance(data_iso, str) else data_iso
    venda = {"id": _next_id("vendas"), "usuario_id": usuario_id, "data": data}
    MEM["vendas"].append(venda)
    return venda

def add_item_venda(venda_id: int, produto_id: int, quantidade: int, preco_unitario: float):
    item = {
        "id": _next_id("itens_venda"),
        "venda_id": venda_id,
        "produto_id": produto_id,
        "quantidade": int(quantidade),
        "preco_unitario": float(preco_unitario)
    }
    MEM["itens_venda"].append(item)
    return item

def reset_and_seed():
    """Reinicia memória e cria usuário/produtos + 90 dias de vendas sintéticas."""
    MEM["usuarios"].clear()
    MEM["produtos"].clear()
    MEM["vendas"].clear()
    MEM["itens_venda"].clear()
    COUNTERS.update({"usuarios": 1, "produtos": 1, "vendas": 1, "itens_venda": 1})

    # Usuário demo
    admin = add_usuario("Admin", "admin@demo.com", "123456")

    # Produtos demo
    p1 = add_produto({
        "nome": "Camiseta Tech",
        "preco": 99.90, "preco_custo": 45.00, "preco_venda": 99.90,
        "quantidade": 50, "categoria": "Vestuário", "subcategoria": "Camiseta",
        "tamanho": "M", "data_chegada": (datetime.now() - timedelta(days=100)).date().isoformat(),
        "usuario_id": admin["id"]
    })
    p2 = add_produto({
        "nome": "Tênis Runner",
        "preco": 299.90, "preco_custo": 170.00, "preco_venda": 299.90,
        "quantidade": 30, "categoria": "Calçados", "subcategoria": "Tênis",
        "tamanho": "42", "data_chegada": (datetime.now() - timedelta(days=120)).date().isoformat(),
        "usuario_id": admin["id"]
    })

    # Vendas sintéticas (90 dias)
    base = datetime.now() - timedelta(days=90)
    for i in range(90):
        d = base + timedelta(days=i)
        mult = 1.6 if d.weekday() >= 5 else 1.0  # mais vendas no fim de semana
        q1 = max(0, int(random.gauss(3 * mult, 1)))
        q2 = max(0, int(random.gauss(2 * mult, 1)))
        if q1 + q2 == 0:
            continue
        v = add_venda(admin["id"], d)
        if q1:
            add_item_venda(v["id"], p1["id"], q1, p1["preco_venda"])
        if q2:
            add_item_venda(v["id"], p2["id"], q2, p2["preco_venda"])

# Executa o seed ao importar o módulo (conveniência para protótipo)
reset_and_seed()

# ----------------------------
# Decorator de login
# ----------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return decorated_function
