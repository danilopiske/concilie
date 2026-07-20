# Guia de Instalação do Cliente

Este manual descreve os passos para instalar e iniciar o sistema **Concilie** em um computador cliente (ambiente de produção). O sistema é distribuído como uma aplicação portátil ("portable"), facilitando o deploy.

---

## 💻 Requisitos do Sistema

*   **Sistema Operacional**: Windows 10 ou Windows 11 (64-bits).
*   **Memória RAM**: Mínimo 4GB (Recomendado 8GB).
*   **Espaço em Disco**: Mínimo 500MB livres.
*   **Permissões**: Permissão de escrita na pasta onde o sistema for extraído (para salvar banco de dados local e logs).

---

## 📥 Passo a Passo da Instalação

### 1. Obter o Pacote
Você receberá um arquivo compactado (ex: `FinancialChecker_v1.8.zip`) ou a pasta `FinancialChecker` descompactada.

### 2. Extração
1.  Copie a pasta `FinancialChecker` para um local seguro no computador do cliente (ex: `C:\Concilie\FinancialChecker`).
2.  **Importante**: Evite colocar na Área de Trabalho ou pastas sincronizadas (OneDrive/Dropbox) se estiver usando banco de dados SQLite local, para evitar conflitos de sincronização.

### 3. Primeira Execução
1.  Abra a pasta `FinancialChecker`.
2.  Localize o arquivo `FinancialChecker.exe`.
3.  Clique duas vezes para iniciar.

> **Nota**: Na primeira execução, o Windows pode exibir uma tela de proteção ("Windows protegeu o computador"). Clique em "Mais informações" e depois em "Executar assim mesmo". Isso ocorre porque o executável é interno e não possui assinatura digital pública.

### 4. Uso do Sistema
*   Ao executar, uma janela preta (terminal) será aberta. **Não feche esta janela**, ela é o motor do sistema.
*   O navegador padrão abrirá automaticamente no endereço `http://localhost:3000`.
*   Acesse o sistema com as credenciais fornecidas (se houver login configurado) ou comece a usar os módulos de importação.

### 5. Configurar Banco de Dados (Opcional - MySQL)
Por padrão, o sistema usa um banco **SQLite** local (`data/concilie.db`), pronto para uso imediato.

Se o cliente usar **MySQL/Oracle**:
1.  Na pasta `conf`, edite o arquivo `db.env` (ou similar, dependendo da versão).
2.  Altere a string de conexão:
    `DATABASE_URL=mysql+pymysql://usuario:senha@localhost:3306/concilie`
3.  Reinicie o `FinancialChecker.exe`.

## ⚠️ Solução de Problemas

*   **Sistema não abre o navegador**: Abra manualmente o Chrome/Edge e digite `http://localhost:3000`.
*   **Erro "Porta em uso"**: Verifique se não há outra instância do sistema aberta. O sistema usa as portas 8000 (API) e 3000 (Frontend).
*   **Janela fecha imediatamente**: Pode haver um erro de configuração. Verifique se a pasta `data` tem permissão de escrita.

---

**Suporte Técnico**: Entre em contato com a equipe de TI da Concilie em caso de dúvidas.
