# Dockerfile para Next.js Static Export
FROM node:20-alpine AS builder

WORKDIR /app

# Instalar pnpm (se o projeto usar)
RUN npm install -g pnpm

# Copiar arquivos de dependência
COPY package.json pnpm-lock.yaml* pnpm-workspace.yaml* ./
COPY apps/web/package.json ./apps/web/

# Instalar dependências
RUN pnpm install --no-frozen-lockfile

# Copiar o código fonte do frontend
COPY apps/web ./apps/web
# Se o frontend depender de tipos compartilhados na raiz:
COPY packages ./packages

# Executar o build estático (Export)
# Certifique-se que o next.config.ts tenha output: 'export'
RUN pnpm --filter web build

# --- Servir com Nginx ---
FROM nginx:stable-alpine

# Copiar o build estático para o diretório do Nginx
COPY --from=builder /app/apps/web/out /usr/share/nginx/html

# Copiar configuração customizada do Nginx para lidar com roteamento do Next.js
# Ex: Redirecionar todas as rotas para index.html se não for arquivo real
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri.html $uri/ /index.html; \
    } \
    # Proxy reverso para a API \
    location /api/ { \
        proxy_pass http://api:8000/; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
