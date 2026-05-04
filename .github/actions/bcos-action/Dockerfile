FROM python:3.11-slim

LABEL "com.github.actions.name"="BCOS v2 Scan"
LABEL "com.github.actions.description"="Beacon Certified Open Source verification engine"
LABEL "repository"="https://github.com/Scottcjn/rustchain-bounties"
LABEL "homepage"="https://rustchain.org/bcos"
LABEL "maintainer"="RustChain / Elyan Labs"

# Install system dependencies and Node.js for semgrep
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    jq \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for semgrep (via NodeSource)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g semgrep cyclonedx-cyclonedx-cli \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -q \
    bandit \
    safety \
    fpdf2 \
    requests \
    GitPython \
    np

WORKDIR /action
COPY entrypoint.sh /action/entrypoint.sh
RUN chmod +x /action/entrypoint.sh
ENTRYPOINT ["/action/entrypoint.sh"]
