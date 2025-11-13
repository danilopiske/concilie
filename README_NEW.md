# 💼 CONCILIE - Sistema de Conciliação Financeira

Sistema completo de conciliação de vendas com cartões de crédito/débito desenvolvido em Python.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-2.0-orange.svg)](CHANGELOG.md)

---

## 🎯 Funcionalidades Principais

- ✅ **Importação Multi-Formato** - Cielo, Rede, planilhas genéricas
- ✅ **Cálculo Automático de Taxas** - MDR, Antecipação, Registro de Recebíveis
- ✅ **Relatórios Analíticos** - HTML interativo com gráficos
- ✅ **Gestão Completa** - Clientes, ECs, Taxas, Termos
- ✅ **Dual-Mode** - MySQL (deploy) ou SQLite (singleuser)
- ✅ **Interface Web** - Dashboard moderno com Panel

---

## 🚀 INSTALAÇÃO RÁPIDA (Modo SingleUser)

### Pré-requisitos
- Python 3.8 ou superior
- Windows / Linux / macOS
- 2GB de espaço em disco

### Instalação

```bash
# 1. Clonar/Baixar o repositório
git clone https://github.com/danilopiske/concilie.git
cd concilie

# 2. Executar instalador (cria ambiente, banco SQLite e dependências)
python install.py

# 3. Iniciar o sistema
python main.py --mode singleuser

# 4. Acessar no navegador
# http://localhost:8500
```

### Credenciais Padrão
```
Usuário: admin
Senha: admin123
```

⚠️ **IMPORTANTE:** Altere a senha após o primeiro login!

---

## 📖 MODOS DE OPERAÇÃO

### Modo SingleUser (SQLite)
**Ideal para:** Uso pessoal, testes, pequenas empresas

```bash
python main.py --mode singleuser
```

**Características:**
- ✅ Banco SQLite local (sem servidor)
- ✅ Zero configuração
- ✅ Instalação automática via `install.py`
- ✅ Portátil (tudo em um diretório)

### Modo Deploy (MySQL)
**Ideal para:** Ambientes corporativos, múltiplos usuários

```bash
python main.py --mode deploy
```

**Características:**
- ✅ MySQL Server (multiusuário)
- ✅ Configuração em `conf/conf_bd.py`
- ⚙️ Requer servidor MySQL instalado

**Configurar MySQL:**
```python
# conf/conf_bd.py
USUARIO = "seu_usuario"
SENHA = "sua_senha"
HOST = "localhost"
PORTA = 3306
BANCO = "concilie"
```

---

## 📂 ESTRUTURA DO PROJETO

```
concilie/
├── install.py                 # Script de instalação automática
├── main.py                    # Entry point do sistema
├── requirements.txt           # Dependências Python
│
├── conf/                      # Configurações e funções core
│   ├── db_manager.py          # Gerenciador dual-mode
│   ├── conf_bd.py             # Conexão MySQL
│   ├── conf_bd_sqlite.py      # Conexão SQLite
│   └── funcoesbd.py           # Funções de banco de dados
│
├── modules/                   # Interfaces do sistema
│   ├── ui_importacao.py       # Interface de importação
│   ├── ui_gestao.py           # Gestão de clientes/taxas
│   ├── ui_calculos.py         # Interface de cálculos
│   └── reports.py             # Geração de relatórios
│
├── proc/                      # Processadores de dados
│   ├── proc_importacao.py     # Lógica de importação
│   └── proc_usuarios.py       # Gestão de usuários
│
├── assets/                    # Recursos visuais
│   ├── cabecalho_financial.png
│   └── capa_relatorio.jpg
│
├── data/                      # Dados (criado na instalação)
│   └── concilie.db            # Banco SQLite (singleuser)
│
└── relatorios/                # Relatórios gerados
    └── *.html
```

---

## 🔧 TECNOLOGIAS UTILIZADAS

### Core
- **Python 3.8+** - Linguagem base
- **Panel 1.7.5** - Framework de UI web interativa
- **Pandas 2.3.0** - Processamento de dados
- **SQLAlchemy 2.0.41** - ORM e SQL

### Banco de Dados
- **MySQL 5.7+** (modo deploy)
- **SQLite 3** (modo singleuser)
- **PyMySQL 1.1.1** - Driver MySQL

### Visualização
- **Plotly 5.23.1** - Gráficos interativos
- **Bokeh 3.7.3** - Dashboards

### Processamento
- **openpyxl 3.1.5** - Leitura de Excel
- **numpy 2.3.0** - Computação numérica

---

## 📊 WORKFLOW TÍPICO

```
1. GESTÃO
   └─> Cadastrar Cliente/EC
   └─> Configurar Taxas
   └─> Definir Termos de Classificação

2. IMPORTAÇÃO
   └─> Upload de Planilhas
   └─> Detecção Automática de Formato
   └─> Processamento e Classificação

3. CÁLCULOS
   └─> Selecionar Processamento
   └─> Aplicar Tipo de Taxa
   └─> Gerar Vendas_Calculos

4. RELATÓRIOS
   └─> Relatório de Processamento
   └─> Relatório Mensal
   └─> Demonstrativos
```

---

## 🛠️ FERRAMENTAS AUXILIARES

### Migração MySQL → SQLite
```bash
python migrate_mysql_to_sqlite.py
```
Migra dados completos do MySQL para SQLite (útil para converter deploy→singleuser)

### Comparação de Schemas
```bash
python compare_schemas.py
```
Compara schemas MySQL vs SQLite e gera relatório de diferenças

---

## 📚 DOCUMENTAÇÃO ADICIONAL

- **[COMPATIBILIDADE_SQL.md](COMPATIBILIDADE_SQL.md)** - Compatibilidade MySQL/SQLite
- **[ANALISE_COMPLETA_SISTEMA.md](ANALISE_COMPLETA_SISTEMA.md)** - Análise técnica completa
- **[ESTRUTURA_DISTRIBUICAO.md](ESTRUTURA_DISTRIBUICAO.md)** - Guia de distribuição

---

## ⚙️ REQUISITOS DE SISTEMA

### Mínimos
- **CPU:** Dual-core 1.5 GHz
- **RAM:** 4 GB
- **Disco:** 2 GB livres
- **Python:** 3.8+

### Recomendados (para grandes volumes)
- **CPU:** Quad-core 2.5 GHz+
- **RAM:** 8 GB+
- **Disco:** 10 GB+ livres (SSD preferível)
- **Python:** 3.10+

---

## 🐛 SOLUÇÃO DE PROBLEMAS

### Erro "No module named 'panel'"
```bash
pip install -r requirements.txt
```

### Erro "port 8500 already in use"
O sistema tentará automaticamente portas de 8500 a 8510. Se persistir:
```bash
# Encontrar processo na porta
netstat -ano | findstr :8500

# Matar processo (Windows)
taskkill /PID <PID> /F
```

### Banco SQLite não criado
```bash
# Reexecutar instalador
python install.py
```

### Erro de importação de planilha
- Verifique se o formato está correto (Cielo/Rede/Genérico)
- Confira se há cabeçalho na planilha
- Teste com uma planilha menor primeiro

---

## 🤝 CONTRIBUINDO

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/NovaFuncionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/NovaFuncionalidade`)
5. Abra um Pull Request

---

## 📜 LICENÇA

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 👨‍💻 AUTORES

- **Danilo Piske** - *Desenvolvimento Principal* - [@danilopiske](https://github.com/danilopiske)

---

## 📞 SUPORTE

- **Issues:** [GitHub Issues](https://github.com/danilopiske/concilie/issues)
- **Email:** suporte@concilie.com.br
- **Documentação:** Ver arquivos `.md` no repositório

---

## 🎉 CHANGELOG

### v2.0 (2025-11-13)
- ✅ Suporte dual-mode (MySQL + SQLite)
- ✅ Instalador automático (`install.py`)
- ✅ Compatibilidade total MySQL/SQLite
- ✅ Correção de schemas (DECIMAL→REAL)
- ✅ 28+ queries otimizadas
- ✅ Documentação completa

### v1.0 (2024)
- ✅ Versão inicial (MySQL only)
- ✅ Importação multi-formato
- ✅ Cálculo de taxas
- ✅ Relatórios HTML

---

**Desenvolvido com ❤️ em Python**
