# 🎵 Spotify Music Downloader

Aplicativo desktop para baixar músicas, álbuns e playlists do Spotify usando **spotdl**.

## 📋 Pré-requisitos

- Python 3.8 ou superior
- FFmpeg instalado no sistema

### Instalando FFmpeg

#### Windows:
1. Baixe o FFmpeg: https://ffmpeg.org/download.html
2. Extraia o arquivo e adicione a pasta `bin` ao PATH do sistema
3. Ou use Chocolatey: `choco install ffmpeg`

#### Linux:
```bash
sudo apt install ffmpeg
```

#### macOS:
```bash
brew install ffmpeg
```

## 🚀 Instalação

1. Clone ou baixe este projeto

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## 💻 Como Usar

1. Execute o aplicativo:
```bash
python app.py
```

2. Na interface:
   - **Cole a URL** da música, álbum ou playlist do Spotify
   - **Escolha a pasta** onde deseja salvar as músicas
   - **Selecione o formato** de áudio (mp3, flac, ogg, opus, m4a)
   - **Escolha a qualidade** (128k, 192k, 256k, 320k)
   - Clique em **"⬇️ Baixar Música/Playlist"**

3. Acompanhe o progresso no log de download

## ✨ Funcionalidades

- ✅ Download de músicas individuais
- ✅ Download de álbuns completos
- ✅ Download de playlists inteiras
- ✅ Múltiplos formatos de áudio (mp3, flac, ogg, opus, m4a)
- ✅ Qualidade configurável (128k a 320k)
- ✅ Interface gráfica moderna e intuitiva
- ✅ Log de download em tempo real
- ✅ Tema escuro (dark mode)

## 🎯 Como Obter URLs do Spotify

1. Abra o Spotify (web ou desktop)
2. Navegue até a música, álbum ou playlist desejada
3. Clique nos três pontos (...) ao lado do título
4. Selecione **"Compartilhar"** → **"Copiar link"**
5. Cole a URL no aplicativo

### Exemplos de URLs válidas:
- Música: `https://open.spotify.com/track/XXXXX`
- Álbum: `https://open.spotify.com/album/XXXXX`
- Playlist: `https://open.spotify.com/playlist/XXXXX`

## 📁 Estrutura de Arquivos

```
spotify_downloader/
│
├── app.py              # Aplicativo principal
├── requirements.txt    # Dependências Python
└── README.md          # Este arquivo
```

## ⚙️ Configurações Recomendadas

- **Formato**: MP3 (mais compatível)
- **Qualidade**: 320k (melhor qualidade)

### Comparação de Formatos:

| Formato | Qualidade | Tamanho | Compatibilidade |
|---------|-----------|---------|-----------------|
| MP3     | Boa       | Médio   | ⭐⭐⭐⭐⭐ |
| FLAC    | Excelente | Grande  | ⭐⭐⭐ |
| OGG     | Boa       | Pequeno | ⭐⭐⭐⭐ |
| OPUS    | Excelente | Pequeno | ⭐⭐⭐ |
| M4A     | Boa       | Médio   | ⭐⭐⭐⭐ |

## 🔧 Solução de Problemas

### Erro: "spotdl não encontrado"
```bash
pip install spotdl
```

### Erro: "FFmpeg não encontrado"
Certifique-se de que o FFmpeg está instalado e no PATH do sistema.

### Download muito lento
- Verifique sua conexão com a internet
- Tente usar um formato com menor qualidade
- Feche outros programas que usam internet

### Músicas não encontradas
- Verifique se a URL está correta
- Algumas músicas podem não estar disponíveis em todas as regiões
- Playlists privadas não podem ser baixadas

## ⚠️ Aviso Legal

Este aplicativo é apenas para fins educacionais. Certifique-se de:
- Respeitar os direitos autorais
- Ter permissão para baixar o conteúdo
- Usar apenas para backup pessoal de músicas que você já possui

O download de músicas protegidas por direitos autorais sem permissão é ilegal em muitos países.

## 🛠️ Tecnologias Utilizadas

- **Python 3** - Linguagem de programação
- **customtkinter** - Interface gráfica moderna
- **spotdl** - Ferramenta de download do Spotify
- **FFmpeg** - Processamento de áudio

## 📝 Licença

Este projeto é livre para uso pessoal e educacional.

## 🤝 Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para:
- Reportar bugs
- Sugerir novas funcionalidades
- Melhorar a documentação
- Enviar pull requests

## 📧 Suporte

Se encontrar problemas ou tiver dúvidas, abra uma issue no repositório.

---

**Desenvolvido com ❤️ usando Python**
