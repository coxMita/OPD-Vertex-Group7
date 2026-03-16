# Export and Import Keycloak Realm in Docker

Keycloak automatically imports any realm JSON placed at:

```
/opt/keycloak/data/import/
```
inside the container, when started with the `--import-realm` flag.

## Export the realm from your running Keycloak

Open a terminal inside your running Keycloak container:

```sh
docker exec -it keycloak /bin/bash
```

Export the realm:

```sh
mkdir -p /opt/keycloak/data/import/
```

```sh
/opt/keycloak/bin/kc.sh export \
    --realm opd-vertex \
    --file /opt/keycloak/data/import/opd-vertex.json
```

Copy it to your host:

```sh
docker cp keycloak:/opt/keycloak/data/import/opd-vertex.json ./keycloak/realms/
```

---

## Put the exported file in your Docker build context

Folder structure example:

```
keycloak/
  Dockerfile
  realms/
    opd-vertex.json
```

## Modify your Dockerfile to copy the realm
Add the following lines to your `keycloak/Dockerfile` before the build step:

```Dockerfile
# Copy custom realm configuration
RUN mkdir -p /opt/keycloak/data/import
COPY realms/ /opt/keycloak/data/import/
```

## For ease of use
To automatically export the realm from a running container and copy it to your host, you can use the provided script `export-realm.sh` in the `keycloak/` directory. Run it from your host machine in the root directory of the project:

```sh
./keycloak/export-realm.sh
```
