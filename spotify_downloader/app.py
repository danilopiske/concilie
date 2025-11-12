import customtkinter as ctk
from tkinter import filedialog, messagebox
import subprocess
import threading
import os
import time
from pathlib import Path


class SpotifyDownloaderApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Spotify Downloader - spotdl")
        self.root.geometry("700x550")

        # Configurar tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.download_thread = None
        self.is_downloading = False

        self.setup_ui()

    def setup_ui(self):
        # Frame principal
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Título
        title_label = ctk.CTkLabel(
            main_frame,
            text="🎵 Spotify Music Downloader",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title_label.pack(pady=(0, 20))

        # Frame para URL
        url_frame = ctk.CTkFrame(main_frame)
        url_frame.pack(fill="x", pady=10)

        url_label = ctk.CTkLabel(
            url_frame, text="URL do Spotify:", font=ctk.CTkFont(size=14)
        )
        url_label.pack(anchor="w", padx=10, pady=(10, 5))

        self.url_entry = ctk.CTkEntry(
            url_frame,
            placeholder_text="Cole aqui a URL da música, álbum ou playlist do Spotify",
            height=40,
        )
        self.url_entry.pack(fill="x", padx=10, pady=(0, 10))

        # Frame para pasta de destino
        dest_frame = ctk.CTkFrame(main_frame)
        dest_frame.pack(fill="x", pady=10)

        dest_label = ctk.CTkLabel(
            dest_frame, text="Pasta de Destino:", font=ctk.CTkFont(size=14)
        )
        dest_label.pack(anchor="w", padx=10, pady=(10, 5))

        dest_input_frame = ctk.CTkFrame(dest_frame, fg_color="transparent")
        dest_input_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.dest_entry = ctk.CTkEntry(
            dest_input_frame,
            placeholder_text="Selecione a pasta onde salvar as músicas",
            height=40,
        )
        self.dest_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_btn = ctk.CTkButton(
            dest_input_frame,
            text="📁 Procurar",
            command=self.browse_folder,
            width=120,
            height=40,
        )
        browse_btn.pack(side="right")

        # Frame de opções
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill="x", pady=10)

        options_label = ctk.CTkLabel(
            options_frame, text="Opções:", font=ctk.CTkFont(size=14)
        )
        options_label.pack(anchor="w", padx=10, pady=(10, 5))

        # Formato de áudio
        format_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        format_frame.pack(fill="x", padx=10, pady=5)

        format_label = ctk.CTkLabel(format_frame, text="Formato:")
        format_label.pack(side="left", padx=(0, 10))

        self.format_var = ctk.StringVar(value="mp3")
        format_menu = ctk.CTkOptionMenu(
            format_frame,
            values=["mp3", "flac", "ogg", "opus", "m4a"],
            variable=self.format_var,
            width=150,
        )
        format_menu.pack(side="left")

        # Qualidade
        quality_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        quality_frame.pack(fill="x", padx=10, pady=5)

        quality_label = ctk.CTkLabel(quality_frame, text="Qualidade:")
        quality_label.pack(side="left", padx=(0, 10))

        self.quality_var = ctk.StringVar(value="320k")
        quality_menu = ctk.CTkOptionMenu(
            quality_frame,
            values=["128k", "192k", "256k", "320k"],
            variable=self.quality_var,
            width=150,
        )
        quality_menu.pack(side="left", pady=(0, 10))

        # Área de log
        log_frame = ctk.CTkFrame(main_frame)
        log_frame.pack(fill="both", expand=True, pady=10)

        log_label = ctk.CTkLabel(
            log_frame, text="Log de Download:", font=ctk.CTkFont(size=14)
        )
        log_label.pack(anchor="w", padx=10, pady=(10, 5))

        self.log_text = ctk.CTkTextbox(log_frame, height=150, state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Botão de download
        self.download_btn = ctk.CTkButton(
            main_frame,
            text="⬇️ Baixar Música/Playlist",
            command=self.start_download,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#1DB954",
            hover_color="#1ed760",
        )
        self.download_btn.pack(fill="x", pady=10)

        # Definir pasta padrão
        default_folder = str(Path.home() / "Downloads" / "Spotify")
        self.dest_entry.insert(0, default_folder)

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Selecione a pasta de destino")
        if folder:
            self.dest_entry.delete(0, "end")
            self.dest_entry.insert(0, folder)

    def log_message(self, message):
        """Adiciona mensagem ao log"""
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def clear_log(self):
        """Limpa o log"""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def validate_inputs(self):
        """Valida os campos de entrada"""
        url = self.url_entry.get().strip()
        dest = self.dest_entry.get().strip()

        if not url:
            messagebox.showerror("Erro", "Por favor, insira uma URL do Spotify")
            return False

        if "spotify.com" not in url:
            messagebox.showerror("Erro", "URL inválida. Use uma URL do Spotify")
            return False

        if not dest:
            messagebox.showerror("Erro", "Por favor, selecione uma pasta de destino")
            return False

        return True

    def download_music(self):
        """Executa o download em thread separada"""
        url = self.url_entry.get().strip()
        dest = self.dest_entry.get().strip()
        format_type = self.format_var.get()
        quality = self.quality_var.get()

        # Criar pasta de destino se não existir
        os.makedirs(dest, exist_ok=True)

        self.clear_log()
        self.log_message("=== Iniciando Download ===")
        self.log_message(f"URL: {url}")
        self.log_message(f"Destino: {dest}")
        self.log_message(f"Formato: {format_type}")
        self.log_message(f"Qualidade: {quality}")
        self.log_message("")

        # Configuração de retry para erros 502
        max_retries = 3
        retry_delay = 10  # segundos

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    self.log_message(f"")
                    self.log_message(f"🔄 Tentativa {attempt + 1} de {max_retries}...")
                    self.log_message(f"⏳ Aguardando {retry_delay} segundos...")
                    time.sleep(retry_delay)
                    self.log_message("")

                # Construir comando spotdl
                cmd = [
                    "spotdl",
                    "download",
                    url,
                    "--output",
                    dest,
                    "--format",
                    format_type,
                    "--bitrate",
                    quality,
                ]

                self.log_message(f"Executando: {' '.join(cmd)}")
                self.log_message("")

                # Executar spotdl
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                )

                # Capturar output em tempo real
                output_lines = []
                for line in process.stdout:
                    if line.strip():
                        self.log_message(line.strip())
                        output_lines.append(line.strip())

                process.wait()

                # Verificar se foi erro 502
                is_502_error = any(
                    "502 Bad Gateway" in line or "502 Server Error" in line
                    for line in output_lines
                )

                if process.returncode == 0:
                    self.log_message("")
                    self.log_message("✅ Download concluído com sucesso!")
                    messagebox.showinfo(
                        "Sucesso", f"Download concluído!\n\nArquivos salvos em:\n{dest}"
                    )
                    break  # Sucesso, sair do loop
                elif is_502_error and attempt < max_retries - 1:
                    self.log_message("")
                    self.log_message(
                        "⚠️  Erro 502 detectado (servidor do Spotify temporariamente indisponível)"
                    )
                    self.log_message(
                        f"🔄 Tentando novamente em {retry_delay} segundos..."
                    )
                    continue  # Tentar novamente
                else:
                    # Último erro ou erro diferente de 502
                    self.log_message("")
                    if is_502_error:
                        self.log_message(
                            "❌ Erro 502 persistiu após múltiplas tentativas."
                        )
                        self.log_message(
                            "💡 O servidor do Spotify está com problemas. Tente novamente mais tarde."
                        )
                    else:
                        self.log_message("❌ Erro ao baixar. Verifique o log acima.")

                    messagebox.showerror(
                        "Erro",
                        "Ocorreu um erro durante o download.\n\n"
                        + (
                            "Servidor do Spotify temporariamente indisponível (502).\nTente novamente em alguns minutos."
                            if is_502_error
                            else "Verifique o log para mais detalhes."
                        ),
                    )
                    break  # Sair do loop após erro final

            except FileNotFoundError:
                self.log_message("")
                self.log_message("❌ ERRO: spotdl não encontrado!")
                self.log_message("Execute: pip install spotdl")
                messagebox.showerror(
                    "Erro",
                    "spotdl não está instalado!\n\nInstale executando:\npip install spotdl",
                )
                break  # Sair do loop

            except Exception as e:
                self.log_message("")
                self.log_message(f"❌ Erro inesperado: {str(e)}")
                messagebox.showerror("Erro", f"Erro inesperado:\n{str(e)}")
                break  # Sair do loop

        # Sempre resetar estado de download ao final
        self.is_downloading = False
        self.download_btn.configure(text="⬇️ Baixar Música/Playlist", state="normal")

    def start_download(self):
        """Inicia o processo de download"""
        if self.is_downloading:
            messagebox.showwarning("Aviso", "Já há um download em andamento!")
            return

        if not self.validate_inputs():
            return

        self.is_downloading = True
        self.download_btn.configure(text="⏳ Baixando...", state="disabled")

        # Executar download em thread separada
        self.download_thread = threading.Thread(target=self.download_music, daemon=True)
        self.download_thread.start()

    def run(self):
        """Inicia a aplicação"""
        self.root.mainloop()


if __name__ == "__main__":
    app = SpotifyDownloaderApp()
    app.run()
