Financial Checker - Portable Version
====================================

Como instalar/distribuir:
1. Copie a pasta `FinancialChecker` inteira (localizada em `dist`) para o computador de destino.
   - Você pode copiar para `C:\FinancialChecker` ou qualquer outro local.
2. Não retire o executável de dentro da pasta. Ele precisa dos outros arquivos para funcionar.
3. Não é necessário instalar Python ou Node.js na máquina de destino.

Como usar:
1. Abra a pasta `FinancialChecker`.
2. Execute o `FinancialChecker.exe`.
3. Uma janela preta (console) abrirá - não a feche, ela é o servidor.
4. O navegador padrão abrirá automaticamente em alguns segundos no endereço `http://localhost:8000`.

Dados:
- O banco de dados será criado automaticamente na pasta `%APPDATA%\FinancialChecker` do usuário (ex: `C:\Users\Nome\AppData\Roaming\FinancialChecker`).
- Isso garante que os dados sejam preservados mesmo se você atualizar o executável.

Solução de Problemas:
- Se o navegador não abrir, acesse `http://localhost:8000` manualmente.
- Se houver erro de permissão, tente executar como Administrador (geralmente não necessário).
