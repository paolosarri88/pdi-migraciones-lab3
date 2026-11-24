# Integración de IA: puntos preparados para continuar

Estado al 24 de noviembre de 2026: la web y los datos funcionan en GCP. La revisión documental tiene adaptador y contrato de resultado; falta configurar un recurso real de Foundry y obtener evidencia de inferencia. El chat ciudadano es una interfaz en desarrollo, sin backend ni respuestas simuladas. No hay un mensaje o tarea enviada a ninguna persona: esta guía queda compartida en el repositorio.

## 1. Revisión documental: ciudadano → IA → funcionario

1. El ciudadano sube un archivo por `POST /api/requests/<rid>/documents`.
2. `app.py:upload` guarda el archivo privado, conserva versiones y, si está habilitada, llama a `document_ai.inspect_document(raw, mime, requirement)`.
3. `document_ai.py` convierte las páginas en imágenes y usa la API visual del despliegue de Azure. El prompt está en `prompts/revision-documental.txt`; los criterios por tipo en `document_rules.py`; su explicación está en `criterios-documentales-ia.md`.
4. La respuesta se valida con `normalize_result` y se guarda en `documents.ai_review` como JSON. Los eventos de la propuesta son internos. El ciudadano no recibe el contenido interno de ese análisis.
5. `proposalHtml` de `static/portal-v7.js` muestra «En desarrollo» cuando no hay análisis; cuando exista un resultado reutiliza la presentación de la propuesta con criterios y motivo.
6. El funcionario decide mediante `PATCH /api/documents/<did>/review`. La IA no modifica `review_status`, `review_note`, `reviewed_by` ni resuelve el expediente.

Variables ya previstas:

```text
AUTO_DOCUMENT_REVIEW=1
AZURE_OPENAI_ENDPOINT=https://<recurso>.openai.azure.com
AZURE_OPENAI_API_KEY=<secreto>
AZURE_OPENAI_DEPLOYMENT=<nombre-real-del-despliegue>
```

Guardar la clave como secreto, no en código, README, capturas, argumentos de comandos ni Git. Ver `conectar-foundry.md` para el bloqueo actual de suscripción y los pasos de conexión. Tener la interfaz de Azure abierta no prueba una llamada real.

### Contrato vigente

El proveedor debe devolver `decision` (`aceptar`, `observar` o `manual`), `confidence` (0..1), `reason`, `document_type_matches`, `legible` y `checks` con `field`, `present`, `evidence`. La normalización agrega `source`, `model` y `rules_version`. Los nombres de campo comprobados deben corresponder a la regla del requisito.

- `aceptar`: propone conformidad; sigue pendiente del funcionario.
- `observar`: propone pedir corrección, explicando el incumplimiento concreto.
- `manual`: incertidumbre, ilegibilidad, archivo protegido o información insuficiente.

Una confianza alta por sí sola no permite proponer aceptación. El normalizador degrada a revisión manual si faltan campos/evidencias, no corresponde el tipo, no es legible o la confianza está bajo el umbral definido. Un fallo de proveedor conserva la revisión humana; no debe presentarse como una evaluación real exitosa.

El documento es contenido no confiable: las instrucciones escritas dentro de él no deben reemplazar el prompt del sistema. No usar nombre de archivo o palabras sueltas como prueba suficiente de identidad, vigencia o domicilio.

### Qué comprobar al conectar

- Cédula/identificación de ejemplo correcta frente a un CV o fotografía sin documento.
- Domicilio con dirección y fecha frente a un archivo ajeno al requisito.
- Documento ilegible, protegido, incompleto, con tipo incorrecto y resultado del proveedor mal formado.
- Propuesta visible solo para funcionario; estado del documento sin cambios hasta su decisión.
- Deshacer una revisión humana restaura el estado anterior y sus metadatos; no borrar archivos ni la propuesta original por fuera del flujo de versiones.
- Registrar despliegue/modelo real, fecha, caso, resultado esperado/obtenido, tiempo y error, sin secretos. Las pruebas simuladas validan el adaptador, no la calidad de un modelo real.

Los archivos incorporados por el funcionario desde correo o recepción usan el mismo expediente. La copia de identificación del tótem se incorpora pendiente de revisión; su captura no acredita identidad.

## 2. Chat ciudadano: interfaz preparada, integración pendiente

`static/portal-v7.js:decorate` crea `#citizen-assistant` solo para ciudadanos. El botón se puede arrastrar, conserva posición y abre un panel. El campo está deshabilitado y el panel dice «En desarrollo». Actualmente no se recogen consultas, no hay llamadas de red al pulsarlo y no se inventan respuestas.

Punto sugerido para la siguiente implementación (todavía no existe): `POST /api/chat`, autenticado como ciudadano y protegido por CSRF. Entrada `{message, conversation_id?}`; salida `{answer, sources?, conversation_id}`. Mantener la clave/modelo en el servidor. Cambiar el campo deshabilitado por un formulario únicamente al tener esa ruta implementada y comprobada.

Contexto inicial apropiado: catálogo de trámites, ayudas documentales, horarios configurados, cómo reservar y cómo aportar antecedentes. Si se incorpora estado personal, limitarlo a solicitudes del usuario autenticado. No dar al chat acceso a GEPOL, antecedentes policiales, fotografías privadas ni expedientes de otras personas. La identidad y el rol vienen de la sesión, nunca de un identificador enviado por el navegador.

El asistente orienta dentro del prototipo, explica límites y cita la ayuda que utiliza. No acepta documentos, modifica estados, agenda por iniciativa propia ni promete decisiones institucionales. En caso de indisponibilidad debe mostrar un error claro y conservar el canal de atención humana. Definir límites de longitud, historial y frecuencia antes de habilitarlo.

## No confundir las dos funciones con la cámara del tótem

La detección del rostro usa MediaPipe/BlazeFace local en el navegador. Solo comprueba que aparezca un rostro durante cinco segundos; no compara con la identificación y no acredita identidad ni prueba de vida. No sustituye la integración con Microsoft Foundry exigida para el laboratorio.

## Comprobaciones del proyecto

```text
python -m unittest discover -s tests -v
node tests/frontend_smoke.cjs
```

Usar bases temporales para mutaciones de prueba. No reiniciar los datos del portal compartido para probar IA. Los criterios, historias y evidencias están en `criterios-documentales-ia.md`, `matriz-pruebas.md`, `verificacion-gcp.md` y `estado-entrega.md`.
