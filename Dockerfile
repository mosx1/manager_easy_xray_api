FROM python:3.13-slim

WORKDIR /fastapiapp

ARG TARGETARCH

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        jq \
        openssl \
        unzip \
    && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    case "${TARGETARCH:-$(dpkg --print-architecture)}" in \
        amd64) XRAY_ARCH="64" ;; \
        arm64) XRAY_ARCH="arm64-v8a" ;; \
        *) echo "Unsupported architecture: ${TARGETARCH}"; exit 1 ;; \
    esac; \
    curl -fsSL \
        "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-${XRAY_ARCH}.zip" \
        -o /tmp/xray.zip; \
    unzip -q /tmp/xray.zip -d /tmp/xray; \
    install -m 0755 /tmp/xray/xray /usr/local/bin/xray; \
    mkdir -p /usr/local/share/xray /usr/local/etc/xray; \
    install -m 0644 /tmp/xray/geoip.dat /usr/local/share/xray/geoip.dat; \
    install -m 0644 /tmp/xray/geosite.dat /usr/local/share/xray/geosite.dat; \
    rm -rf /tmp/xray /tmp/xray.zip; \
    xray version

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . /fastapiapp
RUN install -m 0644 /fastapiapp/customgeo.dat /usr/local/share/xray/customgeo.dat

EXPOSE 443 8081

HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=6 \
    CMD curl --fail --silent http://127.0.0.1:8081/health || exit 1

CMD ["python3", "main.py"]