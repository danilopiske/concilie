# Instalação do wkhtmltopdf

Para usar a funcionalidade de geração de relatórios em PDF, é necessário instalar o wkhtmltopdf no sistema:

## Windows

1. Baixe o instalador do wkhtmltopdf no site oficial: https://wkhtmltopdf.org/downloads.html
2. Execute o instalador e siga as instruções para completar a instalação
3. Adicione o caminho da pasta bin (normalmente C:\Program Files\wkhtmltopdf\bin) às variáveis de ambiente do sistema

## Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install wkhtmltopdf
```

## macOS (usando Homebrew)

```bash
brew install wkhtmltopdf
```

Após a instalação do wkhtmltopdf, verifique se ele está funcionando corretamente executando:

```bash
wkhtmltopdf --version
```

# Instalação das dependências Python

Instale todas as dependências necessárias para o sistema executando:

```bash
pip install -r requirements.txt
```

# Execução do sistema

Para iniciar o sistema:

```bash
python main.py
```

O servidor será iniciado automaticamente em uma porta disponível (geralmente 8500).