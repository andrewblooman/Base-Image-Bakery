ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim-bookworm

ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=3.13
ARG IMAGE_SOURCE

# Install ca-certificates tooling and copy custom CA certificates
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY certs/ /usr/local/share/ca-certificates/custom/
RUN update-ca-certificates

# Apply latest security patches
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

# Point Python HTTP libraries at the system certificate bundle
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# OCI-standard image labels
LABEL org.opencontainers.image.title="Base Python" \
      org.opencontainers.image.description="Custom Python base image with imported CA certificates and security defaults" \
      org.opencontainers.image.vendor="Base Image Bakery" \
      org.opencontainers.image.source="${IMAGE_SOURCE}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.base.name="python:${PYTHON_VERSION}-slim-bookworm"

# Create a non-root application user
RUN groupadd -r appgroup && useradd -r -g appgroup -m appuser

USER appuser

CMD ["python3"]
