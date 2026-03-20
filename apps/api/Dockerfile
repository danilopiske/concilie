FROM python:3.11-slim

WORKDIR /app

# Instalar Poetry
RUN pip install poetry==1.8.3

# Copiar dependências primeiro para aproveitar cache de layers
COPY pyproject.toml poetry.lock ./

# Instalar apenas dependências de produção (sem virtualenv no container)
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction

# Copiar código da aplicação
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
