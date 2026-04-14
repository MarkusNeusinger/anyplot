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

# Stage 2: Serve with nginx
FROM nginx:alpine

# Copy nginx configuration for SPA
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Cloud Run expects port 8080
EXPOSE 8080

# Use exec form to ensure nginx receives signals properly
CMD ["nginx", "-g", "daemon off;"]
