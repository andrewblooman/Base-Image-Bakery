ARG JAVA_VERSION=21
FROM eclipse-temurin:${JAVA_VERSION}-jre-jammy

ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=21
ARG IMAGE_SOURCE

# Install ca-certificates tooling and copy custom CA certificates
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY certs/ /usr/local/share/ca-certificates/custom/
RUN update-ca-certificates

# Import custom certs into the Java keystore (harmless no-op when directory is empty)
RUN find /usr/local/share/ca-certificates/custom -name "*.crt" -type f \
    | while read -r cert; do \
        alias_name="custom-$(basename "$cert" .crt)"; \
        keytool -importcert -noprompt -trustcacerts \
            -alias "$alias_name" \
            -file "$cert" \
            -keystore "$JAVA_HOME/lib/security/cacerts" \
            -storepass changeit; \
    done

# Apply latest security patches
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

# OCI-standard image labels
LABEL org.opencontainers.image.title="Base Eclipse Temurin" \
      org.opencontainers.image.description="Custom Eclipse Temurin JRE base image with imported CA certificates and security defaults" \
      org.opencontainers.image.vendor="Base Image Bakery" \
      org.opencontainers.image.source="${IMAGE_SOURCE}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.base.name="eclipse-temurin:${JAVA_VERSION}-jre-jammy"

# Create a non-root application user
RUN groupadd -r appgroup && useradd -r -g appgroup -m appuser

USER appuser

CMD ["/bin/bash"]
