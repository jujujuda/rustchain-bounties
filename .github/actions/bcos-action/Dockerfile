FROM python:3.11-slim

LABEL "repository"="https://github.com/Scottcjn/bcos-action"
LABEL "homepage"="https://rustchain.org/bcos"
LABEL "license"="MIT"

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl jq shellcheck \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /action

# Install Python dependencies
RUN pip install --no-cache-dir requests httpx

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
