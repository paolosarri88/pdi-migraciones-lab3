# Integración documental vigente y chatbot pendiente

Corte: 24 de noviembre de 2026. La IA documental está conectada a Microsoft Foundry y se verificaron inferencias reales desde la aplicación GCP. El chatbot ciudadano continúa en desarrollo, sin backend ni respuestas simuladas. Para replicar la conexión, seguir `replicar-azure.md`.

## Revisión documental

- Carga: `POST /api/requests/<rid>/documents`. Guarda archivo/versiones y analiza si `AUTO_DOCUMENT_REVIEW=1`.
- Análisis individual del funcionario: `POST /api/documents/<did>/ai`. Solo procesa ese archivo y actualiza su propuesta.
- Adaptador: `document_ai.py`; criterios: `document_rules.py`; instrucciones: `prompts/revision-documental.txt`. Se convierten hasta tres páginas de cada archivo en imágenes. Archivos protegidos, extensos o ambiguos se derivan a revisión manual.
- Resultado: JSON con `decision`, `confidence`, `reason`, `document_type_matches`, `legible`, `checks` y datos extraídos para comparar perfil/vigencia. El servidor valida la estructura y coincidencias; agrega proveedor/modelo, fecha y versión de criterios.
- UI: `proposalHtml` en `static/portal-v4.js`. Solo dentro de cada documento del funcionario. Muestra «IA sugiere: aceptarlo / rechazarlo / revisarlo», motivo y evidencia por campo.
- Confirmación humana: `PATCH /api/documents/<did>/review`. La propuesta no modifica estado/observación/responsable humano ni resuelve el expediente.

Una etiqueta de demostración no invalida el archivo. Un CV no es identidad aunque repita nombre y RUN. Tipo claramente incorrecto o campos ausentes con lectura legible proponen rechazo; incertidumbre o errores proponen revisión. Coincidencia de titular/RUN y vigencia se contrastan con el perfil y fecha del portal. No se valida autenticidad ni se comparan rostros.

La clave Azure queda en Secret Manager; el navegador no recibe credenciales del proveedor. Texto e imágenes de los documentos son contenido no confiable: no deben cambiar instrucciones del sistema. Ver pruebas concretas y evaluación pendiente en `criterios-documentales-ia.md`.

## Chat ciudadano

El botón flotante de `static/portal-v7.js` abre una interfaz «En desarrollo» y se puede mover. No existe `/api/chat` ni un servicio conversacional activo. Para desarrollarlo después se requiere un endpoint autenticado, modelo en servidor, límites de consumo y contexto verificable del catálogo; no presentarlo como parte ya operativa de esta entrega.
