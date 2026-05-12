# Stage 1: Build the React app
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json ./

RUN npm install

COPY . .

RUN npm run build

# Stage 2: Serve with nginx (non-root)
FROM nginxinc/nginx-unprivileged:alpine

USER root
RUN apk upgrade --no-cache nghttp2 curl
USER nginx

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD wget -q -O /dev/null http://127.0.0.1:8080/ || exit 1

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
