FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage – serve with nginx and proxy /api to the backend
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# nginx config: serve SPA and proxy /api/* + /health to the backend service
RUN printf '\
server {\n\
  listen 80;\n\
  root /usr/share/nginx/html;\n\
  index index.html;\n\
\n\
  location /api/ {\n\
    proxy_pass http://api:8000/api/;\n\
    proxy_set_header Host $host;\n\
    proxy_set_header X-Real-IP $remote_addr;\n\
  }\n\
\n\
  location /health {\n\
    proxy_pass http://api:8000/health;\n\
    proxy_set_header Host $host;\n\
  }\n\
\n\
  location / {\n\
    try_files $uri $uri/ /index.html;\n\
  }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]\n