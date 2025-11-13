# Requisitos de Instalação - Concilie v2.0

## Pré-requisitos Obrigatórios

### 1. Python 3.8 ou superior
- **Download:** https://www.python.org/downloads/
- **Versão mínima:** Python 3.8
- **Versão recomendada:** Python 3.11 ou 3.12
- **Importante:** Durante a instalação, marque a opção **"Add Python to PATH"**

**Verificar instalação:**
```bash
python --version
```

### 2. pip (Gerenciador de Pacotes Python)
- Geralmente já vem instalado com Python
- **Versão mínima:** pip 21.0+
- **Recomendado:** Atualizar para a versão mais recente

**Verificar instalação:**
```bash
pip --version
```

**Atualizar pip (recomendado antes da instalação):**
```bash
python -m pip install --upgrade pip
```

> **Nota:** O instalador `install.py` faz upgrade do pip automaticamente

## Pré-requisitos Opcionais (Modo Deploy)

### 3. MySQL Server 5.7+ (Apenas para modo multiusuário)
- **Windows:** https://dev.mysql.com/downloads/installer/
- **Linux:** `sudo apt install mysql-server` (Debian/Ubuntu)
- **Não necessário para modo singleuser (SQLite)**

## Instalação do Concilie

### Passo 1: Extrair o ZIP
Extraia o arquivo `Concilie_v2.0_Distribuicao_*.zip` em uma pasta de sua escolha.

### Passo 2: Executar o Instalador
Abra o terminal/prompt na pasta extraída e execute:

```bash
python install.py
```

O instalador irá:
- ✅ Verificar versão do Python (3.8+)
- ✅ Criar estrutura de diretórios
- ✅ Instalar dependências Python (requirements.txt)
- ✅ Criar banco de dados SQLite
- ✅ Criar usuário admin padrão

**Tempo estimado:** 2-5 minutos (depende da velocidade da internet)

### Passo 3: Iniciar o Sistema
```bash
python main.py --mode singleuser
```

**Credenciais padrão:**
- Usuário: `admin`
- Senha: `admin123`

## Dependências Python (instaladas automaticamente)

O `install.py` instalará as seguintes bibliotecas:

### Core
- panel==1.5.4 - Framework web interativo
- pandas==2.3.0 - Manipulação de dados
- sqlalchemy==2.0.41 - ORM de banco de dados

### Visualização
- plotly==5.23.1 - Gráficos interativos
- matplotlib==3.10.0 - Gráficos estáticos
- Pillow==11.0.0 - Manipulação de imagens

### Banco de Dados
- PyMySQL==1.1.1 - Conector MySQL
- cryptography==44.0.0 - Criptografia

### Utilitários
- openpyxl==3.1.5 - Leitura/escrita Excel
- XlsxWriter==3.2.0 - Geração de Excel
- python-dotenv==1.0.1 - Variáveis de ambiente
- pdfkit==1.0.0 - Geração de PDF

**Total de dependências:** ~73 pacotes (incluindo sub-dependências)

## Requisitos de Sistema

### Mínimo
- **RAM:** 2 GB
- **Disco:** 500 MB livres
- **Processador:** Dual-core 1.5 GHz
- **Sistema Operacional:** Windows 10, Linux, macOS

### Recomendado
- **RAM:** 4 GB ou mais
- **Disco:** 1 GB livres
- **Processador:** Quad-core 2.0 GHz
- **Sistema Operacional:** Windows 10/11, Ubuntu 20.04+

## Portas de Rede

### Modo Singleuser (Padrão)
- **Porta:** 5006 (localhost apenas)
- Não requer configuração de firewall

### Modo Deploy (Multiusuário)
- **Porta Web:** 5006 (configurável)
- **Porta MySQL:** 3306 (se usar banco remoto)
- Pode requerer liberação no firewall

## Resolução de Problemas

### Erro: "python não é reconhecido como comando"
**Solução:** Python não está no PATH. Reinstale marcando "Add to PATH" ou adicione manualmente.

### Erro: "pip install failed"
**Solução:** Execute como administrador ou use:
```bash
python -m pip install --upgrade pip
```

### Erro: "Permission denied" ao criar diretórios
**Solução:** Execute o terminal como administrador (Windows) ou use `sudo` (Linux).

### Erro ao importar módulos
**Solução:** Verifique se o ambiente virtual foi criado corretamente:
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate      # Linux/Mac
pip install -r requirements.txt
```

## Suporte

- **Documentação:** README.md no pacote
- **Issues:** https://github.com/danilopiske/concilie/issues
- **Email:** (adicionar email de suporte)

## Próximos Passos Após Instalação

1. ✅ Acesse http://localhost:5006
2. ✅ Faça login com admin/admin123
3. ✅ **IMPORTANTE:** Altere a senha padrão em Gestão > Usuários
4. ✅ Configure empresas/estabelecimentos
5. ✅ Importe planilhas de vendas e lançamentos
6. ✅ Gere relatórios de conciliação

---
**Versão:** 2.0  
**Data:** Novembro 2025  
**Modo:** Dual (SQLite Singleuser + MySQL Deploy)
