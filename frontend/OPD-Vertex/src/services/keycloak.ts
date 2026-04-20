import Keycloak from 'keycloak-js'

export const keycloak = new Keycloak({
  url: 'http://localhost:8089',
  realm: 'opd-vertex',
  clientId: 'vue-app',
})
