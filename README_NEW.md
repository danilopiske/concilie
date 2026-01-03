# PY Concilie v2.0 🚀

Sistema de conciliação de vendas desenvolvido em Python com **suporte híbrido MySQL/SQLite**.

## 🎯 Modos de Operação

### 🔧 Modo Desenvolvimento (MySQL)
- Ideal para desenvolvimento, testes e produção em servidor
- Requer MySQL 5.7+ rodando
- Performance superior para grandes volumes
- Suporte multi-usuário robusto

### 📦 Modo Distribuição (SQLite)  
- Ideal para instalação em clientes e versões standalone
- **Zero configuração** de servidor de banco
- Banco em arquivo único: `data/concilie.db`
- Portável e fácil de distribuir

**[📖 Guia Completo do Sistema Híbrido](HYBRID_DATABASE_GUIDE.md)**

---

## Tecnologias Utilizadas
- **Backend/Interface:** Python 3.8+
- **Framework UI:** Panel (HoloViz)
- **Banco de Dados:** MySQL 5.7+ **OU** SQLite 3
- **Bibliotecas Principais:** Pandas, SQLAlchemy, Plotly, PDFKit

## Requisitos de Sistema
- **Python:** 3.8 ou superior (3.13 recomendado)
- **Espaço em Disco:** Mínimo de 2GB livres
- **Memória RAM:** Mínimo de 4GB (8GB recomendado)
- **Banco de Dados:** 
  - **MySQL 5.7+** (modo desenvolvimento) **OU**
  - **SQLite 3** (modo distribuição - já incluído no Python)

---

## 🚀 Instalação Rápida

### Windows (Recomendado)

**1. Instale Python e dependências:**
```batch
Instalar.bat
```

**2. Configure o tipo de banco:**
```batch
Configurar Banco.bat

# Escolha:
# [1] MySQL (se tiver servidor MySQL)
# [2] SQLite (para uso standalone)
```

**3. Inicie o sistema:**
```batch
Iniciar Sistema.bat
```

Pronto! Acesse http://localhost:8500
- **Usuário:** admin
- **Senha:** 1234

---

### Instalação Manual

**1. Clone o repositório:**
```bash
git clone https://github.com/seu-usuario/financial-checker.git
cd financial-checker
```

**2. Crie ambiente virtual:**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

**3. Instale dependências:**
```bash
pip install -r requirements.txt
```

**4. Configure banco de dados:**

**Opção A: MySQL (Desenvolvimento)**
```bash
python configure_db.py mysql
```
- Certifique-se de que MySQL está rodando
- Configure credenciais em `conf/conf_bd.py`

**Opção B: SQLite (Distribuição)**
```bash
python configure_db.py sqlite
```
- Sem necessidade de servidor
- Banco criado automaticamente

**5. Execute:**
```bash
python main.py
```

---

## 🔄 Migração entre Bancos

### MySQL → SQLite (Para Distribuição)
```bash
# 1. Migra dados
python dev_tools/migrate_mysql_to_sqlite.py

# 2. Configura sistema
python configure_db.py sqlite

# 3. Testa
python main.py
```

### Ver Status Atual
```bash
python configure_db.py status
```

---

## 📁 Estrutura do Projeto

```
Financial_P/
├── main.py                      # Entry point
├── configure_db.py             # 🆕 Configurador de banco
├── Configurar Banco.bat        # 🆕 Interface Windows
├── requirements.txt            # Dependências
├── HYBRID_DATABASE_GUIDE.md    # 🆕 Guia completo
├── conf/                       # Configurações
│   ├── db_manager.py          # 🆕 Gerenciador híbrido
│   ├── sql_adapter.py         # 🆕 Adaptador SQL
│   ├── debug_utils.py         # 🆕 Utilitários debug
│   ├── conf_bd.py             # Config MySQL
│   ├── conf_bd_sqlite.py      # Config SQLite
│   ├── funcoesbd.py           # ✨ Atualizado (híbrido)
│   └── settings.py            # ✨ Ampliado
├── modules/                    # Módulos UI
├── proc/                       # Processamento
├── data/                       # Dados
│   └── concilie.db            # 🆕 Banco SQLite
└── dev_tools/                 # Ferramentas dev
    ├── migrate_mysql_to_sqlite.py
    └── create_clean_sqlite.py
```

---

## 🔧 Solucionando Problemas

### Erro "No module named 'conf.sql_adapter'"
```bash
# Reinstale
python install.py
```

### Banco SQLite travado
```batch
# Windows
del data\concilie.db-shm
del data\concilie.db-wal

# Linux/Mac
rm data/concilie.db-shm data/concilie.db-wal
```

### Performance lenta (SQLite)
```bash
# Otimize banco
sqlite3 data/concilie.db "VACUUM; ANALYZE;"
```

### Migração falha
1. Verifique se MySQL está rodando
2. Verifique credenciais em `conf/conf_bd.py`
3. Tente criar banco limpo:
   ```bash
   python dev_tools/create_clean_sqlite.py
   ```

---

## 📊 Quando Usar Cada Modo?

| Cenário | MySQL | SQLite |
|---------|-------|--------|
| < 10k registros | ✅ | ✅ |
| 10k-100k registros | ✅ | ✅ |
| > 100k registros | ✅ | ⚠️ |
| Multi-usuário | ✅ | ❌ |
| Distribuição | ❌ | ✅ |
| Sem infraestrutura | ❌ | ✅ |

---

## 📖 Documentação

- **[Guia Híbrido MySQL/SQLite](HYBRID_DATABASE_GUIDE.md)** - Completo
- **[Análise do Projeto](dev_tools/ANALISE_PROJETO_COMPLETA.md)** - Técnica
- **Database Structure** - `database_structure.txt`

---

## 🛠️ Desenvolvimento

```bash
# Modo debug
set DEBUG=true
python main.py

# Forçar MySQL
set DB_TYPE=mysql
python main.py

# Forçar SQLite
set DB_TYPE=sqlite
python main.py
```

---

## ✨ Novidades v2.0

- ✅ **Suporte híbrido MySQL/SQLite**
- ✅ **Configuração automática de banco**
- ✅ **Migração de dados simplificada**
- ✅ **Modo distribuição standalone**
- ✅ **Performance otimizada**
- ✅ **Zero breaking changes** (100% compatível com código existente)
- ✅ **Debug utils centralizados**
- ✅ **Documentação ampliada**

---

## 🔐 Segurança

- Senhas com hash SHA256
- MySQL: Conexão local, credenciais não-versionadas
- SQLite: Segurança por acesso ao arquivo
- Backup: MySQL (dump) / SQLite (copiar arquivo)

---

## 📝 Licença

Este projeto é proprietário. Todos os direitos reservados.

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie branch: `git checkout -b feature/nova-feature`
3. Commit: `git commit -m 'Adiciona feature'`
4. Push: `git push origin feature/nova-feature`
5. Pull Request

---

**Desenvolvido com ❤️ em Python**
