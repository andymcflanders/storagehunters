# Frontend Dockerfile for StorageHub (SvelteKit)

# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

# Stamp the service worker with a unique build version. Each image build
# gets a fresh timestamp, which becomes the SW cache name. When the new SW
# activates it purges every cache whose name doesn't match, evicting JS
# from the previous deploy. Without this, the stale-while-revalidate
# strategy can serve outdated bundles indefinitely.
RUN sed -i "s/__BUILD_VERSION__/$(date +%Y%m%d%H%M%S)/g" static/sw.js

# Build the application
RUN npm run build

# Production stage
FROM node:20-alpine AS runner

WORKDIR /app

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 sveltekit

# Copy built application
COPY --from=builder /app/build ./build
COPY --from=builder /app/package*.json ./

# Install production dependencies only
RUN npm install --omit=dev --legacy-peer-deps && npm cache clean --force

# Set ownership
RUN chown -R sveltekit:nodejs /app

USER sveltekit

# Expose port
EXPOSE 3000

# Set environment
ENV NODE_ENV=production \
    PORT=3000 \
    HOST=0.0.0.0

# Run the application
CMD ["node", "build"]
