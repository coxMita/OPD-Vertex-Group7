FROM quay.io/keycloak/keycloak:26.4.2 AS builder

# Enable health and metrics support
ENV KC_HEALTH_ENABLED=true
ENV KC_METRICS_ENABLED=true

# Configure a database vendor
ENV KC_DB=postgres

WORKDIR /opt/keycloak
# for demonstration purposes only, please make sure to use proper certificates in production instead
RUN keytool -genkeypair -storepass password -storetype PKCS12 -keyalg RSA -keysize 2048 -dname "CN=server" -alias server -ext "SAN:c=DNS:localhost,IP:127.0.0.1" -keystore conf/server.keystore

# Copy health check script
# Moving this to the final image directly to avoid builder permission drops

# Copy custom realm configuration
RUN mkdir -p /opt/keycloak/data/import
COPY realms/ /opt/keycloak/data/import/
RUN /opt/keycloak/bin/kc.sh build --health-enabled=true

FROM quay.io/keycloak/keycloak:26.4.2
COPY --from=builder /opt/keycloak/ /opt/keycloak/
COPY healthcheck.sh /opt/keycloak/healthcheck.sh

USER root
RUN chmod +x /opt/keycloak/healthcheck.sh
USER keycloak

ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]