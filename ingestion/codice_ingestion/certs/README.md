# Intermedios de CA

Algunos hosts `.gob.mx` sirven un certificado válido pero **omiten el certificado intermedio**, así que la verificación TLS falla contra el almacén del sistema. Estos archivos completan la cadena.

Se versionan aquí para que el pipeline sea reproducible sin depender de una llamada a la CA en tiempo de ejecución. **Son certificados públicos de autoridades certificadoras, no secretos.**

| Archivo | Emisor | Hosts afectados |
|---|---|---|
| `digicert-rapidssl-tls-rsa-ca-g1.pem` | DigiCert — RapidSSL TLS RSA CA G1 (encadena a DigiCert Global Root G2) | `web.diputados.gob.mx`, `sitl.diputados.gob.mx` |
| `godaddy-secure-ca-g2.pem` | GoDaddy Secure Certificate Authority G2 | `sil.gobernacion.gob.mx` |
| `letsencrypt-yr1.pem` | Let's Encrypt YR1 (encadena a ISRG Root YR) | `www.transparenciapresupuestaria.gob.mx` |

La alternativa —desactivar la verificación con `verify=False`— queda descartada: un scraper que no verifica TLS produce snapshots en los que no se puede confiar, y la confianza en el snapshot es el activo central del proyecto (ADR-018).
