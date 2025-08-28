import os
from tcc_app import create_app

app = create_app()

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))
    # Liga o modo debug se FLASK_ENV=development ou ENV=dev no .env
    debug = os.getenv("FLASK_ENV", "").lower() == "development" or os.getenv("ENV", "").lower() == "dev"

    print(f" * Iniciando em http://{host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)