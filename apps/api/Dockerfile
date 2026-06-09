FROM python:3.11-slim

WORKDIR /app

# Instalar dependências de sistema (necessárias para algumas libs de dados)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar Poetry
RUN pip install "poetry>=1.8.3,<3"

# Copiar os arquivos de dependência da API (não da raiz do monorepo)
COPY apps/api/pyproject.toml apps/api/poetry.lock ./

# Instalar dependências
RUN poetry config virtualenvs.create false && \
    poetry lock && \
    poetry install --only main --no-interaction --no-root && \
    pip install gunicorn uvicorn

# --- SOLUÇÃO PARA L-01 (Módulos Legados) ---
# Copiamos as pastas da raiz que a API ainda utiliza
COPY modules/ ./modules/
COPY proc/ ./proc/
COPY conf/ ./conf/
COPY templates/ ./templates/

# Copiar o código específico da API
COPY apps/api/app/ ./app/
COPY apps/api/alembic.ini ./
COPY apps/api/alembic/ ./alembic/

# Variáveis de ambiente padrão
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Usamos Gunicorn com worker Uvicorn para resiliência em VPS
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120"]
