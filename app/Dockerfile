# Multi-stage Dockerfile for anyplot React + Vite app on Cloud Run

# Stage 1: Build the application
# node:22-alpine — matches the render harness's pinned Node 22 (Node 20 is EOL
# April 2026; CI tests on 24, 22 is the conservative in-between).
FROM node:22-alpine AS builder

# Accept build arguments for environment variables
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}
ARG VITE_DEBUG_API_URL
ENV VITE_DEBUG_API_URL=${VITE_DEBUG_API_URL}

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

# Copy nginx configuration for SPA (+ the security-headers snippet it includes)
COPY --chown=nginx:nginx nginx.conf /etc/nginx/conf.d/default.conf
COPY --chown=nginx:nginx security-headers.conf /etc/nginx/security-headers.conf

# The origin gate's maps, which need the shared secret — and nginx cannot read
# the environment. The base image already ships the official entrypoint's
# 20-envsubst-on-templates.sh, which renders /etc/nginx/templates/*.template
# into /etc/nginx/conf.d/ before nginx starts, so this costs no start script of
# our own. The `00-` prefix puts the rendered maps ahead of default.conf in the
# conf.d glob, where a reader expects to meet them.
COPY --chown=nginx:nginx origin-gate.conf.template /etc/nginx/templates/00-origin-gate.conf.template

# Two defaults that have to exist as real ENVIRONMENT variables rather than as a
# documented meaning of "unset". envsubst substitutes only names it finds in the
# environment: with neither set, `${ORIGIN_SECRET}` would survive into the
# rendered config as a literal, nginx would read it as a reference to a variable
# it does not know, and the container would refuse to start. With them set, a
# service that declares neither means "gate off, no secret" — which is the
# default state this change ships in and the rollback it rolls back to.
#
# NGINX_ENVSUBST_FILTER keeps envsubst away from everything else: without it,
# envsubst rewrites every `$name` in the template whose name happens to exist in
# the environment, and `$host` and `$uri` in there are nginx's variables, not the
# shell's. The filter is a regex over variable NAMES; `^ORIGIN_` is exactly
# ORIGIN_GATE and ORIGIN_SECRET.
ENV ORIGIN_GATE=off \
    NGINX_ENVSUBST_FILTER="^ORIGIN_"

# On its own instruction so the exception below excuses this line and nothing
# else. DL3064 reads the NAME and warns that a secret may be baked into the
# image; the value here is the empty string, and it is declared for the opposite
# reason — so that a service which supplies no secret renders a config that
# refuses everyone, rather than one nginx cannot parse. The real value arrives at
# runtime from Secret Manager and never reaches a layer. Renaming the variable
# would silence the rule and break the contract instead: the API service, the
# Worker binding, the GitHub repository secret and the Secret Manager entry all
# carry this name.
# hadolint ignore=DL3064
ENV ORIGIN_SECRET=""

# Copy built assets from builder stage
COPY --from=builder --chown=nginx:nginx /app/dist /usr/share/nginx/html

# Cloud Run expects port 8080 — nginx-unprivileged already binds 8080 by default
EXPOSE 8080

# Use exec form to ensure nginx receives signals properly
CMD ["nginx", "-g", "daemon off;"]
