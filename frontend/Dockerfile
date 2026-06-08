# syntax=docker/dockerfile:1

# ── Stage 1: build the Vite app ─────────────────────────────────────────────
FROM node:22-slim AS builder

WORKDIR /app

# Install deps first for cache efficiency
COPY package.json package-lock.json ./
RUN npm install --ignore-scripts

# Receive backend URL at build time so Vite can bake it into the bundle
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Copy source and build
COPY . .
RUN npm run build

# ── Stage 2: serve with nginx ────────────────────────────────────────────────
FROM nginx:1.27-alpine AS runtime

# Remove default config and copy built assets
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
