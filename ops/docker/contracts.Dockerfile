FROM ghcr.io/foundry-rs/foundry:latest
WORKDIR /contracts
COPY contracts/ .
CMD ["forge", "build"]
