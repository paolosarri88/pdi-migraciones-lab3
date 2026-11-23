# Verificación del despliegue · 23 de noviembre de 2026

URL: https://pdi-portal-vwjcdgy22a-uc.a.run.app

Proyecto: `pdi-lab3-paolo-20261123`. Región: `us-central1`.

Imagen desplegada: `us-central1-docker.pkg.dev/pdi-lab3-paolo-20261123/pdi-images/portal@sha256:a4986f7cf9dcce38e9aa0d7135107e48675a1af9b38a5b8ea95bfb721f966085`.

## Resultados

- Las seis pruebas de integración pasan con SQLite local.
- Las seis pruebas pasan con PostgreSQL real en una base temporal aislada `pdi_validation_*` de Cloud SQL. Esa base temporal se eliminó al finalizar y no alteró los registros iniciales del portal publicado.
- La imagen del contenedor arrancó dentro de Cloud Build y comprobó Flask, zona horaria, controlador PostgreSQL, librería de Cloud Storage y los 11 tipos del catálogo.
- `/health` en la URL pública respondió correctamente.
- Las cuentas ciudadana, funcionaria y administradora iniciaron sesión por HTTPS.
- La cuenta ciudadana principal conserva sus seis expedientes de ejemplo.
- El documento precargado del expediente 2 se recuperó desde Cloud Storage mediante la API autenticada.
- Un nuevo expediente ficticio `SOL-2026-0037` se creó con una cuenta ciudadana secundaria, se adjuntó un PDF y se recuperó el mismo archivo. La sesión independiente del funcionario pudo consultar el expediente. Se dejó ese registro marcado en su descripción como comprobación del despliegue.
- Administración informa persistencia en Cloud SQL PostgreSQL y Cloud Storage privado.
- Terraform creó un presupuesto de avisos por US$40 de consumo bruto mensual, con umbrales de 25%, 50%, 75% y 100%. Es un aviso, no un tope automático de gasto.

La integración real con Microsoft Foundry sigue pendiente de una suscripción y despliegue Azure disponibles. El portal no presenta una respuesta ficticia como si proviniera de un modelo real. Las integraciones institucionales y la identidad ciudadana permanecen simuladas.

## Actualización de flujos documentales e interfaz

Publicada el 23 de noviembre de 2026 en la revisión `pdi-portal-00003-w82`, imagen `portal:20261123193525` del mismo repositorio de Artifact Registry. La imagen indicada al inicio corresponde al despliegue original.

- Diez pruebas de integración aprobadas con SQLite y diez con PostgreSQL real en base temporal aislada. Incluyen permisos, revisión por documento, rechazo y reemplazo, conservación de versiones, resolución favorable condicionada a documentos aceptados, avisos completados y calendario con alarmas.
- Comprobación en navegador: ingreso con RUN de prueba, ojo para mostrar/ocultar clave, búsqueda inmediata, aviso de duplicado antes del formulario, validación en español, rechazo de archivos mayores a 5 MB y carga separada de dos antecedentes hasta enviar la solicitud.
- Comprobación de cita: al confirmar desaparece el aviso de confirmación; se pueden guardar varios plazos de recordatorio. El archivo de calendario contiene alarmas y no sustituye un servicio de SMS.
- La versión pública permite ingreso ciudadano con RUN ficticio y conserva los registros anteriores. Se verificó el formulario de nueva solicitud en Google Cloud después de la corrección final.
- Migraciones aditivas: añaden campos de revisión, requisito, versiones y recordatorios. No borran ni reinician los datos existentes.

ClaveÚnica e integraciones institucionales continúan simuladas. No se deben ingresar contraseñas ni documentos reales. El eslogan anterior era texto del prototipo y se reemplazó por «Portal de atención migratoria».

Ajuste final de contadores publicado en `pdi-portal-00004-sqt` (`portal:20261123194359`). Comprobación en el panel funcionario: el contador de antecedentes pendientes muestra 17 y su filtro muestra exactamente 17 solicitudes. Código sincronizado en main y Paolo.
