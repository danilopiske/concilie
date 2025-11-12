# PY Concilie

Sistema de conciliação de vendas desenvolvido em Python.

## Tecnologias Utilizadas
- **Backend/Interface:** Python 3
- **Framework UI:** Panel (HoloViz)
- **Banco de Dados:** MySQL
- **Bibliotecas Principais:** Pandas, SQLAlchemy, Plotly, PDFKit

## Requisitos de Sistema
- **Espaço em Disco:** Mínimo de 2GB livres em C: (ou na partição do sistema)
- **Memória RAM:** Mínimo de 4GB (8GB recomendado para processamento de grandes volumes)
- **MySQL:** Versão 5.7 ou superior
- **Python:** 3.8 ou superior

## Como Executar o Projeto

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/py-concilie.git](https://github.com/seu-usuario/py-concilie.git)
    cd py-concilie
    ```

2.  **Crie um ambiente virtual e ative-o:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure o Banco de Dados:**
    * Assegure-se de que um servidor MySQL esteja rodando.
    * Configure a string de conexão no arquivo `conf/conf_bd.py` ou através de variáveis de ambiente.
    * Verifique se o MySQL tem permissão de escrita em seu diretório temporário.
    * Para melhorar performance, considere configurar um diretório temporário em outro disco:

5.  **Verifique o espaço em disco:**
    ```bash
    python utils_disk_space.py
    ```
    * Este utilitário verifica se há espaço suficiente para operações de banco de dados.
    * Recomenda-se liberar espaço se o disco C: estiver com menos de 10% livre.

6.  **Execute a aplicação:**
    ```bash
    python main.py
    ```
    * A aplicação iniciará automaticamente em uma porta disponível (normalmente 8500).
    * Um navegador web será aberto com a interface do sistema.
    
## Solucionando Problemas Comuns

### Erro "No space left on device" (Sem espaço em disco)
Se aparecer o erro relacionado a espaço em disco no MySQL:
1. Execute o utilitário de diagnóstico: `python utils_disk_space.py`
2. Libere espaço no disco C:
   * Execute o Limpeza de Disco do Windows
   * Remova arquivos temporários
   * Considere mover arquivos grandes para outro disco
3. Configure MySQL para usar diretório temporário em outro disco (ver instruções no utilitário)

### Erros de memória insuficiente
Para operações com grandes conjuntos de dados:
1. Feche aplicativos que consomem muita memória antes de executar
2. Ajuste o parâmetro `max_rows` nas funções de processamento
3. Aumente a memória RAM se possível