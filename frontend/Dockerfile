FROM node:18-bullseye-slim AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
# Install build deps required by some native modules and then remove them after install
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates python3 build-essential git \
	&& if [ -f package-lock.json ]; then npm ci --silent; else npm install --silent; fi \
	&& rm -rf /var/lib/apt/lists/*
COPY . .
RUN npm run build

FROM node:18-bullseye-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app .
EXPOSE 3000
CMD ["npm", "run", "start"]
