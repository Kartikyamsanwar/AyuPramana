# AyuPramana frontend: build static files with Node, serve them with nginx.
# Build context is the repository root (see docker-compose.yml).
FROM node:22-alpine AS build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
ARG VITE_VOICE_INPUT=false
ENV VITE_VOICE_INPUT=$VITE_VOICE_INPUT
RUN npx vite build

FROM nginx:alpine
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/frontend/dist /usr/share/nginx/html
EXPOSE 80
