# Entrega · PoC de atención migratoria PDI

Integrantes: Paolo Sarri y Camilo Bresciani. Arquitectura Cloud · Laboratorio 3. Corte: 24 de noviembre de 2026.

## Acceso directo a la demostración

- Portal: https://pdi-portal-vwjcdgy22a-uc.a.run.app/
- Funcionarios: https://pdi-portal-vwjcdgy22a-uc.a.run.app/login?acceso=funcionarios
- Tótem: https://pdi-portal-vwjcdgy22a-uc.a.run.app/totem
- Simuladores: `/simuladores/gepol` y `/simuladores/registro-civil` en la misma URL.

| Rol | Usuario | Clave de demostración |
|---|---|---|
| Ciudadano (Michael De Santa) | ciudadano@demo.pdi.cl | Ciudadano2026! |
| Funcionario | funcionario@demo.pdi.cl | Funcionario2026! |
| Administrador | admin@demo.pdi.cl | Admin2026! |

Son accesos de la aplicación académica, no credenciales de GCP/Azure ni ClaveÚnica real. No se requiere acceso a las cuentas cloud para evaluar la URL.

## Correspondencia con la entrega solicitada

| Lo solicitado | Archivos incluidos |
|---|---|
| Archivos de ejecución | Código Python, `requirements.txt`, `Dockerfile`, interfaz y recursos locales en `static/` |
| Infraestructura reproducible | `infra/main.tf`, bloqueo de proveedores, `infra/terraform.tfvars.example`, `scripts/deploy.py` y `scripts/connect_foundry.py` |
| Pasos para replicar | `docs/despliegue-gcp.md` y `docs/replicar-azure.md` |
| URL de ejemplo y ejecución | Este documento, `README.md` y `docs/ejecutar-poc.md` |
| Arquitectura, criterios y evidencia | `docs/arquitectura-poc.md`, `docs/criterios-documentales-ia.md`, `docs/matriz-pruebas.md`, `docs/estado-entrega.md` y pruebas en `tests/` |

## Orden de lectura

1. Para probar lo existente: `docs/ejecutar-poc.md`.
2. Para ejecutar localmente: `README.md` (SQLite, sin necesidad de cuentas cloud).
3. Para recrear GCP en un proyecto nuevo: `docs/despliegue-gcp.md`.
4. Para crear/conectar un recurso Azure autorizado: `docs/replicar-azure.md`.

## Alcance comprobado

Aplicación desplegada en Cloud Run, persistencia en PostgreSQL/Cloud SQL, documentos privados en Cloud Storage y claves en Secret Manager. Foundry con `gpt-4.1-mini` ha respondido a pruebas reales desde GCP: lectura del archivo, criterios mínimos, titular y vigencia. La IA propone aceptar, rechazar o revisar cada documento; solo el funcionario confirma decisiones.

Los simuladores institucionales, personas y certificados son académicos. No existe integración real con PDI, Registro Civil o ClaveÚnica, ni verificación biométrica de identidad. El chatbot ciudadano y los envíos externos por correo/WhatsApp no están habilitados. El aviso interno del portal sí funciona. La cámara del tótem detecta presencia de rostro localmente; no compara identidades.

El ZIP no contiene bases de datos, documentos personales, claves de Azure, credenciales cloud, planes ni estado de Terraform. Los datos de la instancia publicada no forman parte del paquete: la réplica crea datos sintéticos nuevos. Para probar, usar archivos ficticios.

Se ejecutaron 40 pruebas Python, controles de frontend y recorridos reales. Una réplica completa desde cero en otra suscripción/proyecto no se ha ejecutado como parte de este cierre; permisos, cuota y disponibilidad de modelos deben comprobarse en las cuentas del evaluador. Las pruebas de casos no representan una medición de precisión general del modelo.
