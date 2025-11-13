# Concilie v2.0 - Instalação Rápida

## ⚡ Instalação em 3 Passos

### 1️⃣ Instalar Python
- Download: https://www.python.org/downloads/
- Versão: Python 3.8 ou superior
- ✅ **IMPORTANTE:** Marque "Add Python to PATH" durante instalação

### 2️⃣ Executar Instalador
Extraia o ZIP e execute no terminal:
```bash
python install.py
```

O instalador irá automaticamente:
- ✅ Atualizar pip
- ✅ Instalar todas as dependências (panel, pandas, etc.)
- ✅ Criar banco de dados SQLite
- ✅ Criar usuário admin

### 3️⃣ Iniciar Sistema
```bash
python main.py --mode singleuser
```

Acesse: **http://localhost:5006**

**Login padrão:**
- Usuário: `admin`
- Senha: `admin123`

---

## 📋 Requisitos Completos

Para informações detalhadas, consulte: **REQUISITOS_INSTALACAO.md**

## ❓ Problemas na Instalação?

### Erro: "python não reconhecido"
Python não está no PATH. Reinstale marcando "Add to PATH"

### Erro ao instalar dependências
Execute manualmente:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Erro de permissão
Execute o terminal como **Administrador** (Windows) ou use `sudo` (Linux)

---

## 📦 O que está incluído?

- ✅ **Panel 1.7.5** - Interface web moderna
- ✅ **Pandas 2.3.0** - Processamento de dados
- ✅ **SQLAlchemy 2.0.41** - ORM banco de dados
- ✅ **Plotly 5.23.1** - Gráficos interativos
- ✅ E mais 70+ dependências

Total de ~73 pacotes Python (instalados automaticamente)

---

## 🚀 Próximos Passos

Após instalação:
1. ✅ Altere a senha do admin
2. ✅ Configure empresas/estabelecimentos
3. ✅ Importe planilhas de vendas
4. ✅ Gere relatórios de conciliação

**Suporte:** https://github.com/danilopiske/concilie/issues

---
**Versão:** 2.0 | **Modo:** Dual (SQLite + MySQL) | **Data:** Nov 2025
