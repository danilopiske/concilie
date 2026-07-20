
import os
import subprocess
import shutil
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    print(f"Executing: {cmd} in {cwd or '.'}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f"Error executing command: {cmd}")
        sys.exit(1)

def remove_readonly(func, path, excinfo):
    import stat
    os.chmod(path, stat.S_IWRITE)
    func(path)

def robust_rmtree(path):
    path = Path(path)
    if path.exists():
        try:
            shutil.rmtree(path, onerror=remove_readonly)
        except Exception as e:
            print(f"⚠️ Failed to remove {path}: {e}")
            try:
                import time
                ts = int(time.time())
                new_name = path.parent / f"{path.name}_trash_{ts}"
                path.rename(new_name)
                print(f"✅ Renamed locked directory to: {new_name}")
            except Exception as e2:
                print(f"❌ Failed to rename: {e2}")
                # Don't exit, try to continue (mkdir might fail if not renamed)

def main():
    # Force UTF-8 encoding for Windows consoles to prevent emoticon crashes
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass

    root_dir = Path(__file__).parent
    web_dir = root_dir / "apps" / "web"
    api_dir = root_dir / "apps" / "api"
    dist_output_dir = root_dir / "dist_v18"
    
    # Limpar dist anterior
    if dist_output_dir.exists():
        robust_rmtree(dist_output_dir)
    dist_output_dir.mkdir()

    # 1. Build Frontend
    if os.getenv("SKIP_FRONTEND") != "true":
        print("\n--- Building Frontend ---")
        # Verificar se node_modules existe, senão instalar
        if not (web_dir / "node_modules").exists():
             run_command("pnpm install", cwd=web_dir)
        
        web_out_dir = web_dir / "out"
        
        # Always clean previous build to ensure fresh artifacts
        if web_out_dir.exists():
            print("Cleaning previous frontend build...")
            robust_rmtree(web_out_dir)

        # Build e Export
        run_command("pnpm run build", cwd=web_dir)
        
        # Verificar se output existe
        if not web_out_dir.exists():
            print("Erro: Diretório apps/web/out não foi criado. Verifique se 'output: export' está no next.config.ts")
            sys.exit(1)
    else:
        print("\n--- Skipping Frontend Build (SKIP_FRONTEND=true) ---")
        web_out_dir = web_dir / "out"
        if not web_out_dir.exists():
             print("❌ Error: SKIP_FRONTEND is set but apps/web/out does not exist.")
             sys.exit(1)

    # 2. Build Backend (PyInstaller)
    print("\n--- Building Backend (PyInstaller) ---")
    
    # Instalar PyInstaller se não estiver no ambiente (assumindo que o usuário já rodou poetry install/add)
    # Mas vamos usar 'poetry run pyinstaller'
    
    # Definir separador de path correto para --add-data
    sep = ";" if os.name == 'nt' else ":"
    
    base_name = "Financial"
    entry_point = api_dir / "app" / "dist_main.py"

    # --- Resolve API Python Environment (MOVED UP) ---
    # We need to know which python to use for both dependency checking AND PyInstaller
    venv_python = sys.executable # Default fallback
    try:
        # Get path to poetry environment for apps/api
        print(f"Resolving API environment path via poetry in {api_dir}...")
        # Use shell=True for windows consistency with poetry
        api_env_path = subprocess.check_output(
            ["poetry", "env", "info", "--path"], 
            cwd=api_dir, 
            text=True,
            shell=True
        ).strip()
        
        print(f"📦 Found API Environment base at: {api_env_path}")
        
        if sys.platform == "win32":
             candidate_python = str(Path(api_env_path) / "Scripts" / "python.exe")
        else:
             candidate_python = str(Path(api_env_path) / "bin" / "python")
             
        if not os.path.exists(candidate_python):
            print(f"⚠️ Warning: Python executable not found at {candidate_python}")
        else:
            print(f"✅ Using API Python: {candidate_python}")
            venv_python = candidate_python
            
    except Exception as e:
        print(f"⚠️ Failed to resolve API venv path: {e}")
        print("Fallback to current python executable...")
    
    # Obter paths de dependencias manuais
    manual_deps = ["pydantic_settings", "typing_inspection", "dotenv", "typing_extensions"]
    dep_paths = {}

    for dep in manual_deps:
        try:
            # Para o dotenv, o nome do pacote é python-dotenv mas o import é dotenv
            pkg_name = "python-dotenv" if dep == "dotenv" else dep.replace("_", "-")
            
            # Tentar importar e pegar o path
            cmd = f"import {dep}; import os; print(os.path.dirname({dep}.__file__))"
            path = subprocess.check_output(
                [venv_python, "-c", cmd],
                cwd=api_dir,
                text=True
            ).strip()
            dep_paths[dep] = path
            print(f"📦 Found {dep} at: {path}")
        except Exception as e:
            print(f"⚠️ Could not resolve {dep} path: {e}")

    # Comando PyInstaller
    # --onefile: arquivo único .exe
    # --name: nome do executável
    # --add-data: incluir pasta do frontend buildado dentro do executável na pasta 'web_dist'
    # --hidden-import: imports que o PyInstaller pode não detectar automaticamente (drivers DB, uvicorn, etc)
    
    add_data_args = f"--add-data \"{web_out_dir}{sep}web_dist\" "
    
    for dep, path in dep_paths.items():
        if path:
            add_data_args += f"--add-data \"{path}{sep}{dep}\" "
    
    # Include 'conf' directory
    conf_dir = root_dir / "conf"
    if conf_dir.exists():
         print(f"📦 Found conf directory at: {conf_dir}")
         add_data_args += f"--add-data \"{conf_dir}{sep}conf\" "
    else:
         print(f"⚠️ Warning: conf directory not found at {conf_dir}")

    # Include 'proc' directory (Required for legacy import logic)
    proc_dir = root_dir / "proc"
    if proc_dir.exists():
         print(f"📦 Found proc directory at: {proc_dir}")
         add_data_args += f"--add-data \"{proc_dir}{sep}proc\" "
    else:
         print(f"⚠️ Warning: proc directory not found at {proc_dir}")

    # Include seed database (data/concilie.db)
    seed_db = root_dir / "data" / "concilie.db"
    if seed_db.exists():
        print(f"📦 Found seed database at: {seed_db}")
        add_data_args += f"--add-data \"{seed_db}{sep}data\" "
    else:
        print(f"⚠️ Warning: Seed database not found at {seed_db}")

    # Use API python path to ensure correct environment
    # (MOVED UP - Logic already executed and stored in venv_python)
    
    pyinstaller_cmd = (
        f"\"{venv_python}\" -m PyInstaller "
        f"--noconfirm "
        f"--onedir "
        f"--clean "
        f"--name \"{base_name}\" "
        f"{add_data_args} "
        f"--hidden-import=pymysql "
        f"--hidden-import=uvicorn.logging "
        f"--hidden-import=uvicorn.loops "
        f"--hidden-import=uvicorn.loops.auto "
        f"--hidden-import=uvicorn.protocols "
        f"--hidden-import=uvicorn.protocols.http "
        f"--hidden-import=uvicorn.protocols.http.auto "
        f"--hidden-import=uvicorn.protocols.websockets "
        f"--hidden-import=uvicorn.protocols.websockets.auto "
        f"--hidden-import=uvicorn.lifespan.on "
        f"--hidden-import=engineio.async_drivers.asgi "
        f"--hidden-import=pydantic "
        f"--log-level=WARN "
        f"\"{entry_point}\""
    )
    
    run_command(pyinstaller_cmd, cwd=api_dir)
    
    # 3. Mover diretório gerado para raiz/dist
    # PyInstaller cria pasta 'dist' dentro do diretório de trabalho (apps/api/dist)
    # Com --onedir, o output será uma pasta chamada 'Financial'
    
    src_dir = api_dir / "dist" / f"{base_name}"
    dst_dir = dist_output_dir / f"{base_name}"
    
    if src_dir.exists():
        if dst_dir.exists():
             robust_rmtree(dst_dir)
             
        shutil.move(str(src_dir), str(dst_dir))
        print(f"\n✅ Build concluído com sucesso!")
        print(f"==================================================")
        print(f"🚀 NOVA VERSÃO GERADA EM: {dst_dir}")
        print(f"👉 EXECUTE ESTE ARQUIVO: {dst_dir / f'{base_name}.exe'}")
        print(f"==================================================")
        
        # Validation Step
        print("\n--- Validating Executable ---")
        exe_path = dst_dir / f"{base_name}.exe"
        try:
             # Run for 5 seconds to check for immediate crashes (ImportErrors)
             import time
             print("Iniciando teste de execução (5s)...")
             process = subprocess.Popen([str(exe_path)], cwd=dst_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
             time.sleep(5)
             
             if process.poll() is not None:
                 print("❌ ERRO: O executável fechou inesperadamente!")
                 stdout, stderr = process.communicate()
                 print("STDOUT:", stdout.decode(errors='replace'))
                 print("STDERR:", stderr.decode(errors='replace'))
                 sys.exit(1)
             else:
                 print("✅ Teste passou: Executável continua rodando após 5s.")
                 process.terminate()
        except Exception as e:
            print(f"⚠️ Erro ao validar executável: {e}")

        # 4. Create ZIP package
        print("\n--- Creating ZIP Package ---")
        zip_path = dist_output_dir / f"{base_name}_v1.8" # Output path without extension
        print(f"Compressing {dst_dir} to {zip_path}.zip...")
        shutil.make_archive(str(zip_path), 'zip', root_dir=dist_output_dir, base_dir=base_name)
        print(f"✅ ZIP gerado com sucesso: {zip_path}.zip")

    else:
        print("❌ Erro: Diretório de build não encontrado.")
        sys.exit(1)

if __name__ == "__main__":
    main()
