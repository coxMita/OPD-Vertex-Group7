docker exec -it keycloak mkdir -p /opt/keycloak/data/import/
echo "Exporting realm 'opd-vertex' from Keycloak..."
docker exec -it keycloak rm -f /opt/keycloak/data/import/opd-vertex.json
docker exec -it keycloak /opt/keycloak/bin/kc.sh export \
    --realm opd-vertex \
    --file /opt/keycloak/data/import/opd-vertex.json
echo "Realm 'opd-vertex' exported inside the container."
rm -f ./keycloak/realms/opd-vertex.json
echo "Copying the exported realm to the host machine..."
docker cp keycloak:/opt/keycloak/data/import/opd-vertex.json ./keycloak/realms/
echo "Realm 'opd-vertex' copied to ./keycloak/realms/opd-vertex.json"
