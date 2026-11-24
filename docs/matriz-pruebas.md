# Historias y matriz de comprobación

| Historia | Resultado esperado | Verificación disponible |
|---|---|---|
| Como ciudadano quiero ingresar a mi portal | Inicio determina rol; no hay selector ciudadano/admin | Autenticación, CSRF y alias RUN en pruebas automatizadas |
| Como ciudadano quiero encontrar un expediente | Búsqueda inmediata por nombre del trámite y folio | Navegador, sin enviar el filtro |
| Como ciudadano quiero entender cada documento | Ayuda desplegable, distinción domicilio/residencia, ejemplo ficticio | Navegador y prueba de API de ejemplos |
| Como ciudadano quiero corregir solo lo observado | Documento aceptado no se reemplaza; observado conserva su versión anterior | Prueba automatizada de ciclo documental |
| Como ciudadano quiero ver acciones realmente pendientes | Avisos reconstruidos del estado actual, incluso después de leerlos | Prueba automatizada y navegador |
| Como ciudadano quiero solicitar atención | Expediente activo, sin duplicar petición ni cita vigente | Prueba automatizada y navegador local |
| Como funcionario quiero coordinar la cita | Fecha y hora válidas, sin expediente cerrado ni horario ocupado | Pruebas de autorización y estados de citas |
| Como ciudadano quiero confirmar y recordar la cita | Aviso desaparece al confirmar; archivo ICS conserva alarmas | Pruebas automatizadas y navegador |
| Como funcionario quiero revisar archivos individualmente | Guardar estado y motivo, historial y aviso al ciudadano | Prueba automatizada de ciclo documental |
| Como equipo quiero proteger expedientes | Otro ciudadano no accede a detalle ni descarga ajenos | Prueba automatizada de aislamiento |
| Como funcionario quiero atender presencialmente | Llegada, turno, inicio y salida coherentes | Prueba automatizada del tótem y agenda |
| Como administrador quiero gestionar cuentas ficticias | Acceso reservado y no desactivar la propia cuenta | Prueba automatizada de administración |
| Como equipo quiero recuperación ante error de IA | No inventar análisis; conservar archivo y revisión manual | Prueba con proveedor simulado; llamada Azure real pendiente |
| Como equipo quiero comprobar calidad de IA | Archivo adecuado, incorrecto y ambiguo; medir errores | Pendiente de acceso Azure y evaluación descrita en criterios |

Las pruebas se ejecutan con SQLite temporal o una base PostgreSQL temporal con prefijo `pdi_validation_`; no utilizan la base publicada para las mutaciones de prueba. La evidencia fechada se conserva en `verificacion-gcp.md`. Las verificaciones mediante respuestas simuladas de proveedor comprueban el código, no la precisión de un modelo real.

Para trabajo compartido, registrar incidencias con rol, folio, pasos y resultado esperado/observado. Acordar quién usa cada expediente y revisar los cambios antes de integrarlos; ninguno de estos frentes está asignado a una persona específica.

## Ampliación: ficha personal y correcciones

| Recorrido | Comportamiento esperado | Evidencia |
|---|---|---|
| Persona y expediente presencial | Buscar ficha; registrar persona con rol ciudadano; crear solicitud fuera de bandeja online | `test_23_person_presential_additional_and_rectification` |
| Pedir/cancelar documento adicional | Motivo obligatorio, sin duplicados activos, aviso y trazabilidad | Prueba 23 |
| Reapertura y corrección | Selector normal bloqueado tras decisión final; reapertura con motivo; original rectificado conservado | Prueba 23 |
| Llegada sin cita | Sin doble turno; iniciar/finalizar aunque no se asociara expediente | Prueba 23 |
| Reutilizar versión | Mismo ciudadano y tipo, sin heredar aceptación, referencia de versión, bloqueo por vencimiento | `test_24_document_reuse_is_owned_versioned_and_pending` |
| Flechas, colores y diálogo | Sin filtro global; orden de pendientes; cerrar con equis o clic fuera | Implementado; revisión visual manual pendiente |

## Ampliación: sesión presencial y edición directa

| Recorrido | Evidencia automatizada / manual |
|---|---|
| Una atención por funcionario, toma ajena impedida, orden flexible | `test_25_attention_exclusive_and_owned` |
| Autorización de recepción, no reutilización de token, captura privada y copia al expediente | `test_26_reception_grant_and_private_files` |
| Lápiz/papelera, auditoría del original, corrección explícita de estado y cierre protegido | `test_27_history_edit_delete_and_closed_guard` |
| Inicialización conjunta de scripts, contadores y tabla | `node tests/frontend_smoke.cjs` |
| Llamado abre ficha y aparece en tótem; tres documentos y «Ver más»; teclado convencional | Comprobación visual local documentada en `verificacion-gcp.md` |
| Cámara y rostro real durante cinco segundos | Implementado; falta recorrido con el equipo físico de presentación |
