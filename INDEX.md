# 📚 Índice de Documentação - Financial Checker v2.0

## 🎯 Início Rápido

**Novo usuário? Comece aqui:**

1. **[README_NEW.md](README_NEW.md)** - Visão geral e instalação rápida
2. **[Configurar Banco.bat](Configurar Banco.bat)** - Configure MySQL ou SQLite
3. **[Iniciar Sistema.bat](Iniciar Sistema.bat)** - Inicie o sistema

---

## 📖 Documentação Principal

### Para Usuários

| Documento | Descrição | Quando Usar |
|-----------|-----------|-------------|
| [README_NEW.md](README_NEW.md) | Guia principal do sistema | Primeiro acesso, instalação |
| [HYBRID_DATABASE_GUIDE.md](HYBRID_DATABASE_GUIDE.md) | Guia completo MySQL/SQLite | Entender modos de operação |
| [Configurar Banco.bat](Configurar Banco.bat) | Configurador visual (Windows) | Trocar entre MySQL/SQLite |

### Para Desenvolvedores

| Documento | Descrição | Quando Usar |
|-----------|-----------|-------------|
| [CHANGELOG_V2.md](CHANGELOG_V2.md) | Lista completa de alterações | Ver o que mudou na v2.0 |
| [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) | Guia de migração de código | Atualizar código existente |
| [dev_tools/ANALISE_PROJETO_COMPLETA.md](dev_tools/ANALISE_PROJETO_COMPLETA.md) | Análise técnica do projeto | Entender arquitetura |

### Para Administradores

| Documento | Descrição | Quando Usar |
|-----------|-----------|-------------|
| [HYBRID_DATABASE_GUIDE.md](HYBRID_DATABASE_GUIDE.md) | Setup e troubleshooting | Configurar ambiente |
| database_structure.txt | Estrutura do banco | Entender schema |

---

## 🛠️ Scripts e Ferramentas

### Configuração

| Script | Descrição | Uso |
|--------|-----------|-----|
| configure_db.py | Configurador CLI | `python configure_db.py [mysql\|sqlite\|status]` |
| Configurar Banco.bat | Configurador visual | Execute e escolha opção |

### Instalação

| Script | Descrição | Uso |
|--------|-----------|-----|
| Instalar.bat | Instalador completo | Execute para instalar tudo |
| install.py | Instalador Python | `python install.py` |
| requirements.txt | Dependências | `pip install -r requirements.txt` |

### Migração de Dados

| Script | Descrição | Uso |
|--------|-----------|-----|
| dev_tools/migrate_mysql_to_sqlite.py | Migra MySQL→SQLite | `python dev_tools/migrate_mysql_to_sqlite.py` |
| dev_tools/create_clean_sqlite.py | Cria banco SQLite vazio | `python dev_tools/create_clean_sqlite.py` |

### Análise e Debug

| Script | Descrição | Uso |
|--------|-----------|-----|
| find_updates_needed.py | Encontra código a atualizar | `python find_updates_needed.py` |
| dev_tools/utilities/bd_describe.py | Descreve estrutura BD | `python dev_tools/utilities/bd_describe.py` |

### Execução

| Script | Descrição | Uso |
|--------|-----------|-----|
| main.py | Entry point principal | `python main.py` |
| Iniciar Sistema.bat | Inicializador Windows | Execute para iniciar |

---

## 🗂️ Estrutura de Arquivos

```
Financial_P/
├── 📘 README_NEW.md                    # ⭐ Comece aqui
├── 📘 HYBRID_DATABASE_GUIDE.md         # Guia completo híbrido
├── 📘 CHANGELOG_V2.md                  # O que mudou
├── 📘 MIGRATION_GUIDE.md               # Como migrar código
├── 📘 INDEX.md                         # ⭐ Este arquivo
│
├── 🚀 main.py                          # Entry point
├── 🔧 configure_db.py                  # Configurador
├── 🔧 find_updates_needed.py           # Verificador de código
├── 📦 requirements.txt                 # Dependências
│
├── 🪟 Instalar.bat                     # Instalador Windows
├── 🪟 Iniciar Sistema.bat              # Iniciar Windows
├── 🪟 Configurar Banco.bat             # ⭐ Configurar Windows
├── 🪟 Atualizacao.bat                  # Atualizar pacotes
│
├── 📁 conf/                            # Configurações
│   ├── ⭐ db_manager.py                # Gerenciador híbrido
│   ├── ⭐ sql_adapter.py               # Adaptador SQL
│   ├── ⭐ debug_utils.py               # Utilitários debug
│   ├── ⭐ settings.py                  # Settings ampliado
│   ├── conf_bd.py                     # Config MySQL
│   ├── conf_bd_sqlite.py              # Config SQLite
│   ├── funcoesbd.py                   # ⭐ Funções híbridas
│   ├── auth.py                        # Autenticação
│   └── ...
│
├── 📁 modules/                         # Módulos UI
│   ├── ui_importacao.py               # Interface importação
│   ├── ui_gestao.py                   # Interface gestão
│   ├── ui_calculos.py                 # Interface cálculos
│   ├── ui_analista.py                 # Interface análise
│   ├── ui_correcao.py                 # Interface correção
│   ├── reports.py                     # Relatórios
│   └── grafico_views.py               # Gráficos
│
├── 📁 proc/                            # Processamento
│   ├── proc_importacao.py             # Importação de dados
│   └── proc_usuarios.py               # Gestão usuários
│
├── 📁 data/                            # Dados
│   └── concilie.db                    # ⭐ Banco SQLite
│
├── 📁 relatorios/                      # Templates
│   ├── template_relatorio.html
│   └── template_relatorio_mensal.html
│
└── 📁 dev_tools/                       # Ferramentas dev
    ├── 📘 ANALISE_PROJETO_COMPLETA.md
    ├── migrate_mysql_to_sqlite.py     # ⭐ Migração
    ├── create_clean_sqlite.py         # Criar DB limpo
    ├── clean_for_distribution.ps1     # Limpar para dist
    └── utilities/                     # Utilitários
        ├── bd_describe.py
        ├── compare_schemas.py
        └── ...
```

**Legenda:**
- ⭐ Novo ou significativamente atualizado na v2.0
- 📘 Documentação
- 🚀 Executável principal
- 🔧 Ferramenta/utilitário
- 🪟 Script Windows
- 📁 Diretório
- 📦 Arquivo de configuração

---

## 🎓 Fluxos de Trabalho Comuns

### 1️⃣ Instalação Inicial (Usuário Final)

```mermaid
Instalar.bat → Configurar Banco.bat (SQLite) → Iniciar Sistema.bat
```

1. Execute `Instalar.bat`
2. Execute `Configurar Banco.bat` → Escolha [2] SQLite
3. Execute `Iniciar Sistema.bat`
4. Acesse http://localhost:8500

### 2️⃣ Setup Desenvolvimento (Desenvolvedor)

```mermaid
Clone → venv → pip install → configure MySQL → python main.py
```

1. Clone o repositório
2. Crie venv: `python -m venv .venv`
3. Ative: `.venv\Scripts\activate`
4. Instale: `pip install -r requirements.txt`
5. Configure: `python configure_db.py mysql`
6. Execute: `python main.py`

### 3️⃣ Preparar Distribuição (Admin)

```mermaid
Develop (MySQL) → migrate → configure SQLite → test → package
```

1. Desenvolva normalmente com MySQL
2. Migre dados: `python dev_tools/migrate_mysql_to_sqlite.py`
3. Configure: `python configure_db.py sqlite`
4. Teste: `python main.py`
5. Limpe: `dev_tools/clean_for_distribution.ps1`
6. Empacote: ZIP com `data/concilie.db` incluído

### 4️⃣ Atualizar Código v1→v2 (Desenvolvedor)

```mermaid
find_updates → fix code → test MySQL → test SQLite → commit
```

1. Execute: `python find_updates_needed.py`
2. Atualize chamadas conforme `MIGRATION_GUIDE.md`
3. Teste com MySQL: `set DB_TYPE=mysql && python main.py`
4. Teste com SQLite: `set DB_TYPE=sqlite && python main.py`
5. Commit das alterações

---

## 🔍 Referência Rápida

### Comandos Úteis

```bash
# Ver status
python configure_db.py status

# Trocar para MySQL
python configure_db.py mysql

# Trocar para SQLite
python configure_db.py sqlite

# Migrar dados
python dev_tools/migrate_mysql_to_sqlite.py

# Encontrar código a atualizar
python find_updates_needed.py

# Iniciar com debug
set DEBUG=true
python main.py

# Forçar tipo de banco
set DB_TYPE=sqlite
python main.py
```

### Variáveis de Ambiente

| Variável | Valores | Descrição |
|----------|---------|-----------|
| DB_TYPE | mysql, sqlite | Força tipo de banco |
| DEBUG | true, false | Ativa modo debug |
| VERBOSE | true, false | Ativa modo verbose |

### Arquivos de Configuração

| Arquivo | Localização | Descrição |
|---------|-------------|-----------|
| .db_config | Raiz | Define tipo de banco (mysql ou sqlite) |
| conf/conf_bd.py | conf/ | Credenciais MySQL |
| conf/conf_bd_sqlite.py | conf/ | Configuração SQLite |

---

## 📞 Suporte e Ajuda

### Problemas Comuns

1. **Erro de módulo não encontrado**
   - Solução: Execute `python install.py`

2. **Query não funciona no SQLite**
   - Solução: Use funções do `sql_adapter.py`
   - Consulte: [HYBRID_DATABASE_GUIDE.md](HYBRID_DATABASE_GUIDE.md)

3. **Migração falha**
   - Solução: Verifique MySQL rodando e credenciais
   - Consulte: [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)

4. **Performance lenta (SQLite)**
   - Solução: Execute `VACUUM; ANALYZE;`
   - Considere: Usar MySQL para volumes grandes

### Onde Procurar Ajuda

| Problema | Documento |
|----------|-----------|
| Como instalar | README_NEW.md |
| Como configurar banco | HYBRID_DATABASE_GUIDE.md |
| Como migrar código | MIGRATION_GUIDE.md |
| O que mudou | CHANGELOG_V2.md |
| Estrutura técnica | dev_tools/ANALISE_PROJETO_COMPLETA.md |

---

## ✅ Checklist para Diferentes Perfis

### Usuário Final
- [ ] Li o README_NEW.md
- [ ] Executei Instalar.bat
- [ ] Configurei para SQLite
- [ ] Iniciei o sistema com sucesso

### Desenvolvedor
- [ ] Li CHANGELOG_V2.md
- [ ] Li MIGRATION_GUIDE.md
- [ ] Executei find_updates_needed.py
- [ ] Atualizei código conforme guia
- [ ] Testei com MySQL
- [ ] Testei com SQLite

### Administrador/DevOps
- [ ] Li HYBRID_DATABASE_GUIDE.md
- [ ] Migrei dados MySQL→SQLite
- [ ] Testei instalação limpa
- [ ] Preparei pacote de distribuição
- [ ] Documentei processo interno

---

## 🎯 Próximos Passos Recomendados

1. **Se é usuário novo**: Leia [README_NEW.md](README_NEW.md)
2. **Se está atualizando**: Leia [CHANGELOG_V2.md](CHANGELOG_V2.md) e [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
3. **Se vai distribuir**: Leia [HYBRID_DATABASE_GUIDE.md](HYBRID_DATABASE_GUIDE.md) seção "Preparando para Distribuição"
4. **Se tem problemas**: Consulte seção "Troubleshooting" em [HYBRID_DATABASE_GUIDE.md](HYBRID_DATABASE_GUIDE.md)

---

**Última atualização:** 23 de Dezembro de 2025  
**Versão:** 2.0  
**Status:** ✅ Produção
