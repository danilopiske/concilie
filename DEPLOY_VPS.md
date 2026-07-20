# Guia de Deploy Profissional - Concilie (VPS)

Este guia descreve os passos para realizar o deploy do sistema Concilie em uma VPS (Ubuntu/Debian) de forma segura e performática.

## 1. Pré-requisitos na VPS
* Docker & Docker Compose v2 instalado
* Acesso SSH
* Um domínio apontado para o IP da VPS (Opcional, mas recomendado para SSL)

## 2. Preparação do Ambiente
Crie o diretório do projeto e suba os arquivos (ou faça git clone):
```bash
mkdir -p /opt/financial-concilie
cd /opt/financial-concilie
```

Certifique-se de que o arquivo `.env` existe com as configurações de produção:
```bash
# .env
SECRET_KEY=sua_chave_segura_aqui
DATABASE_URL=sqlite:///./data/financial.db  # Ou MySQL
REDIS_URL=redis://redis:6379/0
API_V1_STR=/api/v1
```

## 3. Deployment com Docker
O sistema já está orquestrado para subir a API (Gunicorn/Uvicorn), o Frontend (Nginx) e o Redis automaticamente.

```bash
# Build e inicialização em background
docker compose up -d --build
```

### Por que esta estrutura?
* **Gunicorn (API):** Gerencia múltiplos processos da API. Se um travar, o Gunicorn sobe outro.
* **Nginx (Frontend):** Serve os arquivos estáticos do Next.js de forma ultra-rápida e faz o proxy das chamadas `/api` para o contêiner interno.
* **Redis:** Preparado para cache e futuras filas de processamento (Celery).

## 4. Gerenciamento de Logs e Manutenção
Para visualizar o que está acontecendo em tempo real:
```bash
docker compose logs -f api
```

Para aplicar migrações do banco de dados (Alembic):
```bash
docker compose exec api alembic upgrade head
```

## 5. SSL / HTTPS (Próximo Nível)
Para habilitar HTTPS, recomenda-se usar o **Nginx Proxy Manager** ou **Traefik** como entrypoint, ou adicionar o **Certbot** ao contêiner Nginx atual.

---
*Documentação gerada pelo Agente Gemini CLI - 2026*
