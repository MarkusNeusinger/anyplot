# Multi-stage Dockerfile for anyplot React + Vite app on Cloud Run

# Stage 1: Build the application
FROM node:20-alpine AS builder

# Accept build arguments for environment variables
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json yarn.lock ./

# Install dependencies with yarn
RUN yarn install --frozen-lockfile

# Copy source code
COPY . .

# Build the application
RUN yarn build

# Stage 2: Serve with nginx (unprivileged — runs as the `nginx` user, not root)
FROM nginxinc/nginx-unprivileged:alpine

# Copy nginx configuration for SPA
COPY --chown=nginx:nginx nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder --chown=nginx:nginx /app/dist /usr/share/nginx/html

# Cloud Run expects port 8080 — nginx-unprivileged already binds 8080 by default
EXPOSE 8080

# Use exec form to ensure nginx receives signals properly
CMD ["nginx", "-g", "daemon off;"]
