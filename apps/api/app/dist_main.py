# ... imports kept ... (will be fully rewritten in block below)
import sys
import os
import webbrowser
import uvicorn
import multiprocessing
import threading
import http.server
import socketserver
from pathlib import Path

# Adicionar o diretório atual ao path para garantir que imports funcionem
if getattr(sys, 'frozen', False):
    # Se estiver rodando como exe (PyInstaller)
    base_dir = Path(sys.executable).parent
    sys.path.insert(0, str(base_dir))
    bundle_dir = Path(sys._MEIPASS)
else:
    # Se estiver rodando como script
    base_dir = Path(__file__).resolve().parent.parent
    bundle_dir = base_dir

# --- Configuração de Ambiente ---
app_data_dir = Path(os.getenv('APPDATA')) / 'FinancialChecker'
app_data_dir.mkdir(parents=True, exist_ok=True)

# Lógica de Seeding (Preenchimento inicial do banco)
db_path = app_data_dir / "financial.db"

if not db_path.exists():
    print("✨ Primeira execução detectada (Banco de dados ausente).")
    # Tentar encontrar o banco seed (concilie.db) empacotado
    seed_db_path = bundle_dir / "data" / "concilie.db"
    
    if seed_db_path.exists():
        print(f"📦 Copiando banco de dados modelo de {seed_db_path}...")
        try:
            import shutil
            shutil.copy2(seed_db_path, db_path)
            print("✅ Banco de dados inicializado com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao copiar banco de dados: {e}")
    else:
        print(f"⚠️  Banco modelo não encontrado em {seed_db_path}. Iniciando vazio.")

os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

# Importar settings e configurar DB
from app.core.config import settings
settings.DATABASE_TYPE = "sqlite"
settings.SQLITE_DB_PATH = str(db_path)

# Importar app FastAPI
from app.main import app

# --- Configuração do Frontend (Porta 3000) ---
static_dir = bundle_dir / "web_dist"
if not static_dir.exists():
    print(f"⚠️ AVISO: Diretório do frontend não encontrado em {static_dir}")
    # Fallback dev
    static_dir = Path(__file__).parent.parent.parent / "web" / "out"

class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(static_dir), **kwargs)

    def do_GET(self):
        # 1. Tentar resolver o path real
        path = self.translate_path(self.path)
        
        # 2. Se não existir, verificar fallback
        if not os.path.exists(path):
            # Se parece um arquivo (tem extensão), retorna 404 (evita loop em assets)
            if "." in self.path.split("/")[-1]:
                 super().do_GET()
                 return
            
            # Se for rota (sem extensão), serve index.html
            self.path = "/"
            
        super().do_GET()

def start_frontend_server():
    """Roda servidor estático na porta 3000"""
    PORT = 3000
    try:
        with socketserver.TCPServer(("", PORT), SPAHandler) as current_httpd:
            print(f"🌍 Frontend rodando em: http://localhost:{PORT}")
            current_httpd.serve_forever()
    except OSError as e:
        print(f"❌ Erro ao iniciar frontend na porta {PORT}: {e}")

def open_browser():
    """Abre o navegador na porta do Frontend"""
    time.sleep(2)
    print("🚀 Abrindo navegador...")
    webbrowser.open("http://localhost:3000")

def main():
    multiprocessing.freeze_support()
    
    print(f"📂 Diretório de Dados: {app_data_dir}")
    print(f"📂 Banco de Dados: {db_path}")

    if static_dir.exists():
        # Iniciar Frontend em Thread separada
        t_frontend = threading.Thread(target=start_frontend_server, daemon=True)
        t_frontend.start()
        
        # Agendar abertura do browser
        t_browser = threading.Thread(target=open_browser, daemon=True)
        t_browser.start()
    else:
        print("❌ Frontend não encontrado. Rodando apenas API.")

    # Iniciar API (Backend) na porta 8000
    print("🔌 Iniciando API na porta 8000...")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    main()
