# [MOD] Novo script para popular o banco com vendas fictícias
import random
import datetime as dt

from tcc_app.db import get_db_connection

def gerar_vendas_ficticias():
  conn = get_db_connection()
  cur = conn.cursor(dictionary=True)

  # pega todos os usuários
  cur.execute("SELECT id FROM usuarios")
  usuarios = cur.fetchall()

  inicio = dt.date(2025, 1, 1)
  fim = dt.date(2025, 11, 18)
  dias_total = (fim - inicio).days + 1

  for u in usuarios:
    uid = u["id"]

    # produtos desse usuário
    cur.execute("SELECT id, preco_venda FROM produtos WHERE usuario_id = %s", (uid,))
    produtos = cur.fetchall()
    if not produtos:
      continue

    print(f"Gerando vendas fictícias para usuario {uid} ({len(produtos)} produtos)")

    # para cada dia, chance de ter de 0 a 3 vendas
    for offset in range(dias_total):
      dia = inicio + dt.timedelta(days=offset)

      num_vendas = random.choices([0, 1, 2, 3], weights=[40, 35, 20, 5])[0]
      for _ in range(num_vendas):
        # cria venda
        cur.execute(
          "INSERT INTO vendas (usuario_id, data) VALUES (%s, %s)",
          (uid, dia)
        )
        venda_id = cur.lastrowid

        # escolhe de 1 a 4 itens
        itens = random.randint(1, min(4, len(produtos)))
        prods_escolhidos = random.sample(produtos, itens)

        for p in prods_escolhidos:
          qtd = random.randint(1, 5)
          cur.execute(
            """
            INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_unitario)
            VALUES (%s, %s, %s, %s)
            """,
            (venda_id, p["id"], qtd, float(p["preco_venda"] or 0.0))
          )

  conn.commit()
  cur.close()
  conn.close()
  print("Vendas fictícias geradas com sucesso.")

if __name__ == "__main__":
  gerar_vendas_ficticias()
