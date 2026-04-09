FROM debian:13.4

# Install system dependencies in one layer, clear APT cache
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential nodejs npm python3 python3-pip ripgrep ffmpeg gcc python3-dev libffi-dev && \
    rm -rf /var/lib/apt/lists/*

COPY . /opt/hermes
WORKDIR /opt/hermes

# Install Python and Node dependencies in one layer, no cache.
# Split optional extras into smaller pip passes to avoid resolver-too-deep
# failures when buildx tries to solve the entire `.[all]` extra at once.
RUN set -eux; \
    pip install --no-cache-dir -e . --break-system-packages; \
    for extra in \
        modal \
        daytona \
        messaging \
        cron \
        cli \
        dev \
        tts-premium \
        pty \
        honcho \
        mcp \
        homeassistant \
        sms \
        acp \
        voice \
        dingtalk \
        feishu \
        mistral; do \
        pip install --no-cache-dir -e ".[${extra}]" --break-system-packages; \
    done; \
    npm install --prefer-offline --no-audit; \
    npx playwright install --with-deps chromium --only-shell; \
    cd /opt/hermes/scripts/whatsapp-bridge; \
    npm install --prefer-offline --no-audit; \
    npm cache clean --force

WORKDIR /opt/hermes
RUN chmod +x /opt/hermes/docker/entrypoint.sh

ENV HERMES_HOME=/opt/data
VOLUME [ "/opt/data" ]
ENTRYPOINT [ "/opt/hermes/docker/entrypoint.sh" ]
