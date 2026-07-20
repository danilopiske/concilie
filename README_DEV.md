# Guia de Desenvolvimento: Inicialização e Performance

Este documento descreve como operar o sistema manualmente e as melhores práticas para extrair o máximo de performance do hardware atual (20GB RAM / Windows Native).

---

## 🚀 Inicialização Manual (Sem .bat)

Para ter controle total sobre os logs e processos, você pode abrir dois terminais e rodar os comandos abaixo:

### 1. Backend (FastAPI)
```powershell
cd apps/api
# Ativa otimização do Python e desativa watch em pastas pesadas
$env:PYTHONOPTIMIZE=1
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --reload-dir app --reload-exclude 'node_modules/*,.next/*,dist/*'
```

### 2. Frontend (Next.js)
```powershell
cd apps/web
pnpm dev --turbo
```

---

## 📈 Análise de Performance: Native vs WSL vs Docker

Dado que você tem **20GB de RAM** e está no **Windows**, aqui está a recomendação de "Ranking de Performance":

### 1º Lugar: Windows Native (Atual) - **VENCEDOR**
- **Por que**: O sistema é baseado em Python, Node e MySQL. O MySQL rodando como serviço nativo no Windows consome muito menos RAM do que o Docker Desktop (que exige uma VM Linux por trás).
- **Vantagem**: Menor latência de I/O em arquivos (especialmente para o Node/Next.js).
- **Melhoria**: Continue no nativo, mas use os scripts otimizados que eu criei para limpar processos pendentes.

### 2º Lugar: WSL 2 (Windows Subsystem for Linux)
- **Por que**: Excelente para ferramentas CLI, mas o consumo de RAM do `vmmem` costuma ser agressivo (pode roubar 50% da sua RAM rapidamente).
- **Risco**: Se o seu projeto estiver em uma partição Windows (`/mnt/d/`), a performance de I/O é **péssima**. Você teria que mover o projeto TODO para dentro do sistema de arquivos do Linux (`\\wsl$\...`) para valer a pena.

### 3º Lugar: Docker Desktop
- **Por que**: O "Vilão da RAM". O Docker Desktop no Windows consome muita memória apenas para manter o motor rodando. Para um ambiente de desenvolvimento onde você já tem MySQL instalado, o Docker traria mais peso (overhead) do que benefício.

### **Conclusão para sua máquina:**
Mantenha o sistema **Nativo (Windows)**, mas aplique estas regras:
1.  **MySQL como Serviço**: Configure o serviço MySQL para início "Manual" se não usar todo dia, ou deixe em "Automático" se for uso constante.
2.  **Limpeza de Processos**: Sempre use os novos scripts `.bat` ou o comando `taskkill` (descrito abaixo) se sentir travamento.
3.  **Antigravity/IA**: Use o `.cursorrules` atualizado para que ele não tente ler pastas gigantes.

---

## 🧹 Dicas de Limpeza Rápida

Se o sistema travar, rode este comando no PowerShell (Admin) para limpar tudo de uma vez:
```powershell
taskkill /f /im python.exe /t; taskkill /f /im node.exe /t
```

Para limpar arquivos temporários do Python:
```powershell
Get-ChildItem -Path . -Include __pycache__ -Recurse | Remove-Item -Force -Recurse
```
## 🏎️ Motores de Performance (C/Rust)

O sistema foi atualizado com bibliotecas de baixo nível para máxima eficiência:
- **FastAPI + OrJSON**: Respostas de API serializadas em Rust.
- **Excel + Fastexcel**: Leitura de planilhas usando o motor **Calamine** (Rust).
- **SQLite WAL Mode**: Banco de dados muito mais rápido em concorrência.
- **Tuned SQLAlchemy Pool**: Gerenciamento sênior de conexões com o MySQL.

---

## 💿 Modo Ultra: Dev Drive (Windows 11)

Se você estiver no Windows 11, pode ganhar **até 30% a mais de velocidade de I/O** criando um **Dev Drive** (unidade ReFS).

### Como criar (Sem formatar nada):
1. Abra **Configurações > Sistema > Para Desenvolvedores**.
2. Clique em **Dev Drive** > **Criar Dev Drive**.
3. Escolha **Criar arquivo VHDX** (Disco rígido virtual).
4. Defina um tamanho (ex: 50GB) e chame de "Financial_Dev".
5. **Mova a pasta do projeto para este novo disco**.
6. O Windows usará a tecnologia **ReFS** que é otimizada para milhões de arquivos pequenos (node_modules).

---

## 🛠️ Ferramentas de Manutenção (Pasta /scripts)

Criei ferramentas exclusivas para você:
- `TurboRamCleaner.ps1`: Limpa a RAM sem fechar nada (chamado automaticamente no boot).
- `OptimizeOS.ps1`: Configura o Windows Defender e prioridade de processos (chamado automaticamente no boot).

---

## 🏁 Checklist de Performance
- [x] `.cursorrules` configurado (IA não trava).
- [x] Pasta `dist_v18` isolada.
- [x] Scripts `.bat` otimizados com `taskkill` e `cleaners`.
- [x] Engines trocadas para Rust/C.
