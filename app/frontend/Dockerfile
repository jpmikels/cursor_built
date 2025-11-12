# ---------- Base deps ----------
FROM node:18-alpine AS base
WORKDIR /app
RUN apk add --no-cache libc6-compat

# ---------- Install deps ----------
FROM base AS deps
COPY package*.json ./
RUN npm install --no-audit --no-fund

# ---------- Build ----------
FROM deps AS builder
WORKDIR /app
COPY . .
RUN npm run build

# ---------- Production ----------
FROM gcr.io/distroless/nodejs20  # smaller + Cloud Run friendly
WORKDIR /app

# Copy build output (Next 13/14 standalone mode)
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
# Copy public assets if they exist
COPY --from=builder /app/public ./public

# Default environment
ENV NODE_ENV=production

# Cloud Run injects $PORT automatically
ENV HOST=0.0.0.0
CMD ["server.js"]
