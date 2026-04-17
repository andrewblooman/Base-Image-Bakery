ARG PYTHON_VERSION=3.13
FROM cgr.dev/chainguard/python:latest-dev

ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=3.13
ARG IMAGE_SOURCE

USER root

# Install ca-certificates and import custom certs from the repo's certs/ directory
RUN apk add --no-cache ca-certificates
COPY certs/ /usr/local/share/ca-certificates/custom/
RUN update-ca-certificates

# Point Python HTTP libraries at the system certificate bundle
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# OCI-standard image labels
LABEL org.opencontainers.image.title="Base Python" \
      org.opencontainers.image.description="Custom Python base image (Chainguard/Wolfi) with imported CA certificates and security defaults" \
      org.opencontainers.image.vendor="Base Image Bakery" \
      org.opencontainers.image.source="${IMAGE_SOURCE}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.base.name="cgr.dev/chainguard/python:latest-dev"

USER nonroot

CMD ["python3"]
