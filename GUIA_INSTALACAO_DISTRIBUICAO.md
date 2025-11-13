# 📦 GUIA DE INSTALAÇÃO E DISTRIBUIÇÃO - CONCILIE v2.0

## ✅ ARQUIVOS CRIADOS PARA DISTRIBUIÇÃO

### 1. **install.py** - Instalador Automático
**Localização:** Raiz do projeto  
**Função:** Script completo de instalação para modo singleuser

**O que faz:**
- ✅ Verifica Python 3.8+
- ✅ Cria estrutura de diretórios (data/, relatorios/, temp/)
- ✅ Instala dependências do requirements.txt
- ✅ Cria banco SQLite com schema completo
- ✅ Cria usuário admin (admin/admin123)
- ✅ Valida instalação

**Uso:**
```bash
python install.py
```

---

### 2. **clean_for_distribution.ps1** - Script de Limpeza
**Localização:** Raiz do projeto  
**Função:** Remove arquivos temporários e locais antes de distribuir

**O que remove:**
- ❌ Ambientes virtuais (.venv, venv, venv2)
- ❌ Cache Python (__pycache__, *.pyc)
- ❌ Banco de dados local (concilie.db*)
- ❌ Planilhas de teste (*.xlsx, *.xls)
- ❌ Relatórios gerados (*.html)
- ❌ Schemas temporários (*.json)
- ❌ Diretórios não relacionados (spotify_downloader/)

**Uso:**
```powershell
.\clean_for_distribution.ps1
```

---

### 3. **.gitignore** - Atualizado e Completo
**Localização:** Raiz do projeto  
**Função:** Define arquivos/diretórios ignorados pelo Git

**Inclui:**
- Ambientes virtuais
- Cache Python
- Bancos de dados locais
- Planilhas e relatórios
- IDEs e editores
- Sistema operacional
- Configurações sensíveis

---

### 4. **Arquivos .gitkeep** - Mantém Estrutura Vazia
**Localização:** Diretórios vazios

Criados em:
- `data/.gitkeep`
- `relatorios/.gitkeep`
- `temp/.gitkeep`
- `arquivos_processados/.gitkeep`

**Função:** Mantém diretórios vazios no Git (necessários para o sistema)

---

### 5. **ESTRUTURA_DISTRIBUICAO.md** - Guia de Empacotamento
**Localização:** Raiz do projeto  
**Função:** Documentação completa de quais arquivos incluir/remover

**Conteúdo:**
- ✅ Lista de arquivos essenciais
- ❌ Lista de arquivos a remover
- 📦 Estrutura final do pacote
- 🚀 Opções de distribuição (ZIP, Git, PyInstaller)
- 📋 Checklist de distribuição

---

### 6. **README_NEW.md** - README Atualizado
**Localização:** Raiz do projeto  
**Função:** Documentação moderna com dual-mode

**Conteúdo:**
- 🚀 Instalação rápida
- 📖 Modos de operação (MySQL/SQLite)
- 📂 Estrutura do projeto
- 🔧 Tecnologias
- 📊 Workflow
- 🐛 Solução de problemas
- 🎉 Changelog v2.0

**Nota:** Renomear `README_NEW.md` → `README.md` antes de distribuir

---

## 📋 PROCESSO COMPLETO DE DISTRIBUIÇÃO

### Passo 1: Limpar o Workspace

```powershell
# Executar script de limpeza
.\clean_for_distribution.ps1
```

### Passo 2: Substituir README

```bash
# Windows
move /Y README_NEW.md README.md

# Linux/Mac
mv README_NEW.md README.md
```

### Passo 3: Verificar Estrutura

**Arquivos ESSENCIAIS (devem estar presentes):**
```
✅ install.py
✅ main.py
✅ requirements.txt
✅ README.md
✅ .gitignore
✅ conf/ (todos os .py)
✅ modules/ (todos os .py)
✅ proc/ (todos os .py)
✅ assets/ (imagens)
✅ data/.gitkeep
✅ relatorios/.gitkeep
✅ temp/.gitkeep
```

**Arquivos OPCIONAIS (recomendados):**
```
📄 COMPATIBILIDADE_SQL.md
📄 ANALISE_COMPLETA_SISTEMA.md
📄 ESTRUTURA_DISTRIBUICAO.md
🔧 migrate_mysql_to_sqlite.py
🔧 compare_schemas.py
```

**Arquivos/Diretórios que NÃO devem estar:**
```
❌ .venv/, venv/, venv2/
❌ __pycache__/
❌ data/concilie.db*
❌ *.xlsx, *.xls (em venda_planilhas/, lancamento_planilhas/)
❌ relatorios/*.html (exceto template)
❌ mysql_schema.json, sqlite_schema.json, schema_differences.json
❌ spotify_downloader/
❌ bd_structures/
❌ debug.txt
```

### Passo 4: Testar em Ambiente Limpo

```bash
# 1. Clonar/Copiar para diretório novo
cd /tmp
cp -r /caminho/concilie concilie_test

# 2. Executar instalador
cd concilie_test
python install.py

# 3. Iniciar sistema
python main.py --mode singleuser

# 4. Validar
# - Login funciona?
# - Interface carrega?
# - Importação funciona?
# - Relatório é gerado?
```

### Passo 5: Criar Pacote de Distribuição

**Opção A: ZIP**
```bash
# Criar arquivo ZIP
zip -r concilie_v2.0_singleuser.zip concilie/ \
    -x "*.pyc" "*.pyo" "*__pycache__*" "*.db" "*.xlsx"
```

**Opção B: Git Tag**
```bash
git add .
git commit -m "Release v2.0 - Dual Mode (MySQL + SQLite)"
git tag v2.0
git push origin main --tags
```

**Opção C: GitHub Release**
1. Ir para https://github.com/danilopiske/concilie/releases
2. Clicar em "Draft a new release"
3. Tag: `v2.0`
4. Title: "Concilie v2.0 - Dual Mode Release"
5. Description: Copiar CHANGELOG
6. Anexar ZIP (opcional)
7. Publicar

---

## 🎯 INSTRUÇÕES PARA USUÁRIO FINAL

**Documento a ser incluído no pacote:**

```markdown
# COMO INSTALAR O CONCILIE

## Requisitos
- Python 3.8 ou superior instalado
- 2GB de espaço em disco

## Instalação (3 passos simples)

1. Extrair o arquivo ZIP em uma pasta de sua escolha

2. Abrir terminal/prompt na pasta extraída e executar:
   ```
   python install.py
   ```

3. Após a instalação, iniciar o sistema:
   ```
   python main.py --mode singleuser
   ```

4. Abrir navegador em: http://localhost:8500

5. Login:
   - Usuário: admin
   - Senha: admin123

## Pronto! O sistema está funcionando.
```

---

## 📊 TAMANHO FINAL DO PACOTE

| Componente | Tamanho |
|------------|---------|
| Código Python (.py) | ~350 KB |
| Documentação (.md) | ~200 KB |
| Assets (imagens) | ~50 KB |
| Scripts (install, clean) | ~20 KB |
| **Total (sem venv)** | **~620 KB** |

**Com dependências instaladas:**
- venv completo: ~300 MB

---

## ✅ CHECKLIST FINAL DE DISTRIBUIÇÃO

### Antes de Distribuir
- [ ] Executar `clean_for_distribution.ps1`
- [ ] Renomear `README_NEW.md` para `README.md`
- [ ] Remover todos `__pycache__/`
- [ ] Remover `data/concilie.db*`
- [ ] Remover planilhas de teste
- [ ] Verificar `.gitignore` atualizado
- [ ] Confirmar `.gitkeep` em diretórios vazios

### Testes
- [ ] Testar `install.py` em máquina limpa
- [ ] Testar `python main.py --mode singleuser`
- [ ] Testar login com admin/admin123
- [ ] Testar importação de planilha
- [ ] Testar geração de relatório

### Documentação
- [ ] README.md atualizado com dual-mode
- [ ] CHANGELOG.md com versão 2.0
- [ ] Licença incluída (se aplicável)

### Distribuição
- [ ] Criar ZIP (se aplicável)
- [ ] Criar GitHub Release (se aplicável)
- [ ] Atualizar documentação online (se aplicável)

---

## 🚀 PRÓXIMOS PASSOS APÓS DISTRIBUIÇÃO

1. **Coletar Feedback** - Issues, melhorias, bugs
2. **Monitorar Instalações** - Ver onde usuários têm dificuldade
3. **Criar Tutoriais em Vídeo** - Para instalação e uso básico
4. **Desenvolver v2.1** - Com melhorias baseadas em feedback

---

## 📞 SUPORTE PÓS-DISTRIBUIÇÃO

**Canais de Suporte:**
- GitHub Issues: Relatar bugs e solicitar features
- Email: suporte@concilie.com.br
- Documentação: Arquivos .md no repositório

**Tempo de Resposta Esperado:**
- Bugs críticos: 24-48h
- Features: 1-2 semanas
- Dúvidas: 48-72h

---

**Última Atualização:** 13/11/2025  
**Versão do Guia:** 1.0  
**Responsável:** Danilo Piske
