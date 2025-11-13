# 📦 ESTRUTURA DE DISTRIBUIÇÃO - CONCILIE

## Arquivos ESSENCIAIS (Devem estar no pacote)

### Core do Sistema
```
main.py                          # Entry point do sistema
requirements.txt                 # Dependências Python
README.md                        # Documentação principal
install.py                       # Script de instalação
```

### Configurações (conf/)
```
conf/
├── __init__.py                  # ✅ ESSENCIAL
├── db_manager.py                # ✅ ESSENCIAL - Gerenciador dual-mode
├── conf_bd.py                   # ✅ ESSENCIAL - Conexão MySQL
├── conf_bd_sqlite.py            # ✅ ESSENCIAL - Conexão SQLite
├── funcoesbd.py                 # ✅ ESSENCIAL - Funções de banco
├── settings.py                  # ✅ ESSENCIAL - Configurações gerais
├── auth.py                      # ✅ ESSENCIAL - Autenticação
├── colunas_recebiveis.py        # ✅ ESSENCIAL - Metadados
├── depara_utils.py              # ✅ ESSENCIAL - Mapeamento
└── __pycache__/                 # ❌ REMOVER
```

### Módulos de Interface (modules/)
```
modules/
├── __init__.py                  # ✅ ESSENCIAL
├── ui_importacao.py             # ✅ ESSENCIAL - Interface de importação
├── ui_gestao.py                 # ✅ ESSENCIAL - Interface de gestão
├── ui_calculos.py               # ✅ ESSENCIAL - Interface de cálculos
├── reports.py                   # ✅ ESSENCIAL - Geração de relatórios
├── grafico_views.py             # ✅ ESSENCIAL - Gráficos
└── __pycache__/                 # ❌ REMOVER
```

### Processadores (proc/)
```
proc/
├── proc_importacao.py           # ✅ ESSENCIAL - Lógica de importação
├── proc_usuarios.py             # ✅ ESSENCIAL - Gestão de usuários
└── __pycache__/                 # ❌ REMOVER
```

### Assets (assets/)
```
assets/
├── cabecalho_financial.png      # ✅ ESSENCIAL - Logo do sistema
└── capa_relatorio.jpg           # ✅ ESSENCIAL - Capa de relatórios
```

### Documentação Adicional
```
COMPATIBILIDADE_SQL.md           # ✅ RECOMENDADO - Docs de compatibilidade
ANALISE_COMPLETA_SISTEMA.md      # ✅ RECOMENDADO - Análise técnica
```

---

## Diretórios CRIADOS NA INSTALAÇÃO (Vazios no pacote)

```
data/                            # ✅ Criado pelo install.py
├── arquivos_processados/        # ✅ Criado pelo install.py
├── lancamento_planilhas/        # ✅ Criado pelo install.py
└── venda_planilhas/             # ✅ Criado pelo install.py

relatorios/                      # ✅ Criado pelo install.py
├── README.md                    # ℹ️  Opcional - Instruções
└── template_relatorio.html      # ℹ️  Opcional - Template

temp/                            # ✅ Criado pelo install.py
```

---

## Arquivos/Diretórios a REMOVER (Não distribuir)

### Ambientes Virtuais
```
.venv/                           # ❌ REMOVER - Ambiente virtual
venv/                            # ❌ REMOVER - Ambiente virtual
venv2/                           # ❌ REMOVER - Ambiente virtual duplicado
env/                             # ❌ REMOVER - Ambiente virtual
```

### Cache Python
```
__pycache__/                     # ❌ REMOVER - Cache Python (todos)
*.pyc                            # ❌ REMOVER - Bytecode compilado
*.pyo                            # ❌ REMOVER - Bytecode otimizado
*.pyd                            # ❌ REMOVER - Extensões compiladas
```

### Arquivos de Dados Locais
```
data/concilie.db                 # ❌ REMOVER - Banco local (será criado)
data/concilie.db-shm             # ❌ REMOVER - SQLite shared memory
data/concilie.db-wal             # ❌ REMOVER - SQLite write-ahead log
```

### Arquivos de Trabalho
```
arquivos_processados/            # ❌ REMOVER - Resultados locais
lancamento_planilhas/            # ❌ REMOVER - Planilhas locais
venda_planilhas/                 # ❌ REMOVER - Planilhas locais
*.xlsx                           # ❌ REMOVER - Planilhas Excel
*.xls                            # ❌ REMOVER - Planilhas Excel antigas
```

### Relatórios Gerados
```
relatorios/*.html                # ❌ REMOVER - Relatórios já gerados
relatorios/*.png                 # ❌ REMOVER - Gráficos gerados
```

### Schemas e JSONs Temporários
```
mysql_schema.json                # ❌ REMOVER - Schema temporário
sqlite_schema.json               # ❌ REMOVER - Schema temporário
schema_differences.json          # ❌ REMOVER - Comparação temporária
debug.txt                        # ❌ REMOVER - Debug local
```

### Scripts de Desenvolvimento
```
bd_describe.py                   # ⚠️  OPCIONAL - Tool de debug
compare_schemas.py               # ⚠️  OPCIONAL - Tool de comparação
migrate_mysql_to_sqlite.py       # ⚠️  OPCIONAL - Tool de migração (útil para deploy→single)
fix_placeholders.py              # ❌ REMOVER - Script já aplicado
test_produto_cielo.py            # ❌ REMOVER - Teste unitário
```

### Diretórios de Desenvolvimento
```
bd_structures/                   # ❌ REMOVER - Estruturas de debug
docs/                            # ❌ REMOVER - Vazio
scripts/                         # ❌ REMOVER - Vazio
spotify_downloader/              # ❌ REMOVER - Não relacionado ao projeto
```

### Git
```
.git/                            # ⚠️  MANTER se for distribuição via Git
.gitignore                       # ⚠️  MANTER se for distribuição via Git
```

### IDE/Editor
```
.vscode/                         # ❌ REMOVER - Configurações VS Code
.idea/                           # ❌ REMOVER - Configurações PyCharm
*.swp                            # ❌ REMOVER - Vim swap files
.DS_Store                        # ❌ REMOVER - macOS
Thumbs.db                        # ❌ REMOVER - Windows
```

---

## 📦 Estrutura FINAL do Pacote Distribuível

```
concilie/
├── install.py                   # Script de instalação
├── main.py                      # Entry point
├── requirements.txt             # Dependências
├── README.md                    # Documentação
├── COMPATIBILIDADE_SQL.md       # Docs técnicas
├── ANALISE_COMPLETA_SISTEMA.md  # Análise completa
├── .gitignore                   # (se via Git)
│
├── conf/                        # Configurações
│   ├── __init__.py
│   ├── db_manager.py
│   ├── conf_bd.py
│   ├── conf_bd_sqlite.py
│   ├── funcoesbd.py
│   ├── settings.py
│   ├── auth.py
│   ├── colunas_recebiveis.py
│   └── depara_utils.py
│
├── modules/                     # Interfaces
│   ├── __init__.py
│   ├── ui_importacao.py
│   ├── ui_gestao.py
│   ├── ui_calculos.py
│   ├── reports.py
│   └── grafico_views.py
│
├── proc/                        # Processadores
│   ├── proc_importacao.py
│   └── proc_usuarios.py
│
└── assets/                      # Recursos visuais
    ├── cabecalho_financial.png
    └── capa_relatorio.jpg
```

**Tamanho Estimado:** ~500KB (código) + ~50KB (assets) = **~550KB total**

---

## 🚀 INSTRUÇÕES DE DISTRIBUIÇÃO

### Opção 1: ZIP para Download Direto

```bash
# Criar estrutura limpa
mkdir concilie_singleuser
cd concilie_singleuser

# Copiar apenas arquivos essenciais
# (ver lista acima)

# Compactar
zip -r concilie_singleuser_v2.0.zip concilie_singleuser/
```

### Opção 2: Repositório Git

```bash
# Clonar e limpar
git clone https://github.com/danilopiske/concilie.git concilie_clean
cd concilie_clean

# Remover arquivos locais
rm -rf .venv venv venv2 __pycache__
rm -rf data/*.db* arquivos_processados/* lancamento_planilhas/* venda_planilhas/*
rm -rf relatorios/*.html relatorios/*.png
rm *.json debug.txt
rm -rf bd_structures docs scripts spotify_downloader

# Criar release
git tag v2.0-singleuser
git push origin v2.0-singleuser
```

### Opção 3: PyInstaller (Executável)

```bash
# Criar executável standalone (Windows)
pip install pyinstaller

pyinstaller --name=Concilie \
            --onefile \
            --add-data "assets;assets" \
            --add-data "conf;conf" \
            --add-data "modules;modules" \
            --add-data "proc;proc" \
            --hidden-import=sqlalchemy.dialects.sqlite \
            --hidden-import=pymysql \
            main.py
```

---

## 📋 CHECKLIST DE DISTRIBUIÇÃO

- [ ] Remover todos os `__pycache__/`
- [ ] Remover ambientes virtuais (.venv, venv, venv2)
- [ ] Remover banco de dados local (data/concilie.db*)
- [ ] Remover planilhas de teste (*.xlsx, *.xls)
- [ ] Remover relatórios gerados (relatorios/*.html)
- [ ] Remover schemas JSON temporários
- [ ] Remover diretório spotify_downloader/
- [ ] Verificar .gitignore atualizado
- [ ] Testar install.py em máquina limpa
- [ ] Verificar README.md atualizado
- [ ] Criar CHANGELOG.md com versão
- [ ] Testar main.py --mode singleuser após instalação
- [ ] Validar login com credenciais padrão
- [ ] Testar uma importação completa
- [ ] Gerar um relatório de teste

---

## 📝 Tamanho de Cada Componente

| Componente | Arquivos | Tamanho Aprox. |
|------------|----------|----------------|
| Código Python | 15 | ~350 KB |
| Documentação | 3 | ~150 KB |
| Assets | 2 | ~50 KB |
| **TOTAL** | **20** | **~550 KB** |

---

## ⚙️ Instalação pelo Usuário Final

```bash
# 1. Baixar/Clonar
git clone https://github.com/danilopiske/concilie.git
cd concilie

# 2. Executar instalador
python install.py

# 3. Iniciar sistema
python main.py --mode singleuser

# 4. Acessar
# http://localhost:8500
# Usuário: admin
# Senha: admin123
```

**Tempo estimado de instalação:** 3-5 minutos (dependendo da velocidade de internet)
