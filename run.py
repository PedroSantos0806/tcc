# run.py
from tcc_app import create_app  # Importando a função create_app da aplicação

# Criando a instância do app
app = create_app()

if __name__ == '__main__':
    # Rodando a aplicação em modo de debug
    app.run(debug=True)
