FROM node:20-alpine
WORKDIR /app
COPY . .
RUN npm i -g pnpm && pnpm i --frozen-lockfile && pnpm --filter @janus/adapter-base-solana build
CMD ["pnpm", "--filter", "@janus/adapter-base-solana", "start"]
