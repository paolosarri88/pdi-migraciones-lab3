> Bitácora histórica. Las entradas anteriores a la conexión con Foundry describen etapas previas y pueden mencionar funciones sustituidas. Para el estado final, ver `LEEME_ENTREGA.md`, `estado-entrega.md` y `criterios-documentales-ia.md`.

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

## Avisos accionables, coordinación de citas y ayudas documentales

Actualización del 23 de noviembre de 2026, revisión `pdi-portal-00005-b9d`, imagen `portal:20261123203252`.

- Quince pruebas aprobadas con SQLite temporal y quince con PostgreSQL real en una base temporal aislada (251,831 segundos). La base de validación se eliminó al finalizar.
- Nuevas regresiones: avisos derivados del estado aunque las notificaciones anteriores estén leídas; solicitud ciudadana de atención, coordinación por funcionario, confirmación y desaparición del aviso; ayuda y ejemplos PDF; validación del resultado IA; conservación de revisión manual cuando el proveedor falla.
- Terraform validado; plan aplicado con cero recursos nuevos, una actualización y cero eliminaciones. No se habilitó IA ni se crearon recursos Azure.
- En navegador local: acceso ciudadano blanco, ayuda desplegable de identidad y residencia, solicitud de atención registrada, avisos de documentos y confirmación simultáneos y apertura de la cita desde el panel de avisos.
- En navegador público: landing actualizada, avisos de los documentos actualmente pendientes, botón de calendario primario azul y formulario para solicitar atención vinculado a un expediente. Se preservaron los registros del usuario; no se enviaron nuevas solicitudes de prueba en su cuenta pública durante esta verificación.
- Se comprobó el renderizado real de un PDF y el contrato de respuesta mediante transporte simulado. Las pruebas con proveedor simulado verifican el software: no demuestran precisión ni una llamada real a Foundry.
- Diagnóstico Azure: la sesión UAI se renovó correctamente; el directorio universitario no devolvió suscripciones accesibles. La identidad Bytequest guardada tenía token vencido y el usuario informó que el inicio de sesión no reconocía la cuenta. Es necesario confirmar la cuenta/suscripción vigente del laboratorio. La inferencia real y evaluación de calidad permanecen pendientes.

Las guías de uso, criterios, arquitectura, matriz de pruebas y pendientes se incluyen en `docs/`. La automatización de documentos está preparada pero desactivada, con revisión manual disponible.

## Revisión v4: decisión humana, bandeja operativa y simuladores

Publicación final: revisión `pdi-portal-00008-6g8`, imagen `portal:20261124014241` (identificador de compilación en UTC).

- Diecinueve pruebas aprobadas con SQLite temporal. Diecinueve aprobadas con PostgreSQL temporal aislado (359,552 segundos). El último ajuste de la acción «Resolver expediente» después de una cita se verificó además en la prueba local de prioridades.
- La propuesta IA ya no modifica el estado documental ni la solicitud; se conserva separada, con eventos internos. El ciudadano no recibe el contenido interno del análisis. El funcionario decide cada documento y el resultado final.
- Se verificaron registro de ciudadanos sin elevación de rol, RUN sin puntos/con guion, formularios de acceso por rol, tipos de certificado con concurrencia, bandeja de prioridades, permisos de consultas institucionales y procedencia obligatoria de archivos incorporados por funcionario desde correo.
- La finalización de atención y la salida del recinto se registran por separado. El tótem impide repetir llegada/salida y requiere atención finalizada para la salida.
- Comprobación HTTPS del despliegue: ingreso corporativo y ciudadano, acceso restringido a la bandeja, listados con RUN, consultas de GEPOL y Registro Civil, contenido separado por sistema y disponibilidad de las tres páginas independientes. Las consultas de comprobación dejan registros de auditoría, sin modificar expedientes.
- Sintaxis JavaScript y compilación Python verificadas. La revisión visual automática NO pudo completarse: el navegador dejó de responder y su sesión de control expiró. No se presenta una captura anterior como evidencia visual de esta versión.

Rutas publicadas: `/totem`, `/simuladores/gepol` y `/simuladores/registro-civil`. Usan el mismo servicio y datos del laboratorio, con diseños independientes y avisos de simulación. No se conectan a sistemas reales ni leen correos automáticamente. La biometría permanece fuera del flujo definido; la IA real sigue pendiente del acceso Azure descrito previamente.

## Fichas de personas, atención presencial y rectificaciones

Actualización del 23 de noviembre de 2026 (Santiago). Imagen final `portal:20261124024116` (etiqueta UTC), publicada en el mismo servicio Cloud Run.

- 21 pruebas aprobadas con SQLite temporal (1,372 segundos) y 21 con PostgreSQL real en base temporal aislada (460,373 segundos). La normalización final de fechas de vigencia se comprobó además con la ejecución local final.
- Casos nuevos: alta de persona sin elevación de rol, ficha protegida, solicitud presencial, requisito adicional y cancelación con motivo, bloqueo de cambio normal de una decisión final, reapertura explícita, rectificación conservando el original, llegada sin cita y atención sin expediente asociado.
- Reutilización: solo versiones aceptadas de la misma persona y tipo; se conserva la referencia al original y el nuevo documento queda pendiente de revisión. Los documentos vencidos se rechazan para reutilización. La biblioteca de otra persona no es accesible al ciudadano.
- Migraciones aditivas para canal de ingreso, referencia de versión, vigencia y datos de rectificación; tabla de requisitos adicionales. No se borraron expedientes ni anotaciones existentes.
- HTTPS: recursos de la nueva interfaz, ficha y biblioteca autenticadas, permisos de ciudadano, accesos por rol y simuladores institucionales comprobados. Las consultas institucionales dejan auditoría; esta comprobación no cambió expedientes publicados.
- Interfaz implementada: documentos siempre visibles y contraídos, pendientes primero, flechas individuales, solicitud/cancelación de otro requisito, colores más visibles, cierre de diálogo con clic exterior y equis; bandeja online separada de atención presencial y ficha de persona.
- Sintaxis JavaScript y diferencias de archivos comprobadas. La comprobación visual interactiva en navegador sigue sin completarse; no se presenta una captura antigua como evidencia de esta versión. El cierre por clic exterior forma parte de la revisión manual indicada en la guía.

La IA real de Foundry sigue pendiente. Las recomendaciones no cambian decisiones humanas. No se añadieron SMS, lectura automática de correo, escáner de cédula ni biometría.

## Actualización del 24 de noviembre: fila, capturas y personajes

Imagen publicada: `portal:20261124032743` (etiqueta UTC). Se mantiene la misma URL y la persistencia compartida.

- 24 pruebas aprobadas en SQLite (1,645 segundos) y 24 en PostgreSQL temporal aislado (579,106 segundos). Incluyen atención exclusiva por funcionario, rechazo de toma/finalización ajena, flexibilidad del orden de llamada, autorización temporal de recepción, consumo del token, archivos privados, corrección/eliminación lógica de eventos y bloqueo del cambio de estado de un expediente cerrado sin reapertura.
- La incorporación de la identificación del tótem como documento pendiente se comprobó además en la ejecución local final. No se hereda una aceptación de identidad ni se acepta automáticamente por detectar un rostro.
- `node tests/frontend_smoke.cjs`: carga conjunta de scripts, contadores, color rojo de «Cerrada», enlaces de folio, fecha e historial escapado. Sintaxis y diferencias de archivos comprobadas.
- Comprobación visual interactiva en copia local aislada: ingreso de funcionario, menú con contadores, expediente sin panel de antecedentes declarados, editor junto a una acción, ficha, lista de tres documentos y despliegue «Ver más», llamado de Franklin Clinton con apertura directa de su ficha y sesión activa en Módulo 2; tótem mostrando ese turno llamado, bienvenida y teclado QWERTY con fila numérica.
- La cámara física y la inferencia sobre un rostro real no se ejecutaron durante esta comprobación. El flujo usa `getUserMedia`, MediaPipe Tasks Vision 0.10.21 y BlazeFace servidos localmente. Falta probar el permiso y recorrido con la cámara del equipo que se usará en la presentación. No se declara biometría ni verificación de identidad.
- HTTPS público: nuevas rutas y recursos, nombres temáticos, contadores, tablero, bibliotecas protegidas, consultas con campos distintos en GEPOL/Registro Civil y tipo MIME del WASM comprobados. Las consultas generan auditoría; no se modificaron expedientes de la demostración mediante este control.
- Se preservan personas nuevas, cuentas de funcionario/administrador y expedientes/archivos existentes. La migración temática solo cambia las identidades precargadas. Fuentes y escenarios inventados en `personajes-gta.md`.

La actualización automática de la tabla evita reemplazar un contenido idéntico y descarta una respuesta de sondeo si se cambió de sección. La IA documental real de Foundry sigue pendiente de acceso Azure.

## Reservas confirmadas, recepción provisional y deshacer · 24 de noviembre

Imagen final: `portal:20261124144014` (etiqueta UTC), publicada en el mismo servicio Cloud Run.

- **29 pruebas locales aprobadas**, ejecución final de 2,114 segundos, más la comprobación Node de inicialización conjunta de scripts y navegación con el enrutador vigente.
- **29 casos distintos comprobados en PostgreSQL entre dos ejecuciones:** la primera ejecutó 28 casos durante 793,122 segundos; 26 terminaron correctamente y los dos últimos se interrumpieron por cierre de la conexión. Se renovó el proxy y se repitieron esos dos casos, junto con el nuevo caso de asignación duplicada: las tres pruebas pasaron en 163,531 segundos. La base temporal de la ejecución interrumpida se eliminó explícitamente y la nueva se eliminó al finalizar.
- Los casos nuevos verifican reservas Confirmadas sin coordinación, colisiones de bloques, cita prevista fuera de la fila hasta la llegada, recepción provisional sin RUN, vinculación de identidad por el funcionario, revisión deshecha que restaura metadatos, rechazo deshecho que restaura estado, incorporación deshecha que conserva la versión archivada y certificado privado condicionado a Resuelta.
- La actualización final agrega captura de acciones sin cambio material (por ejemplo, tomar una asignación ya propia), para que su anotación también pueda deshacerse. Retira avisos generados por la acción deshecha. Las citas con atención iniciada no se restauran desde el historial del expediente.
- **Comprobación visual local aislada:** reserva ciudadana del 25 de noviembre a las 09:00 confirmada en la misma operación; chat En desarrollo que abre y se arrastra; ficha con folios enlazados y Ver menos tras el último documento; citas previstas con Niko Bellic marcado No ha llegado fuera de la fila; tótem con pregunta de cita, prefijo CITA- fijo y teclado numérico completo sin desplazamiento en la vista de prueba.
- Se corrigió una colisión entre el atributo del contador del menú y el de Ver más que podía borrar su texto al actualizar. Los contadores ahora solo modifican las etiquetas de navegación.
- **HTTPS público:** nuevas rutas y recursos, horario/bloques, citas previstas, permisos de fichas/bibliotecas, simuladores y PDF de certificado de ejemplo comprobados sin mutar expedientes publicados. La revisión en navegador se hizo sobre copia aislada, no sobre datos de usuarios del portal compartido.
- Los formularios emergentes usan la validación en español y Atrás/Adelante utiliza el enrutador actual, incluidas las nuevas recepciones.

La papelera conserva auditoría y deshace en orden inverso. Los registros históricos previos a las instantáneas solo permiten restauración cuando existe información suficiente; en caso contrario se exige corrección explícita. No se inventan estados históricos. No se ejecutó una inferencia real de Foundry ni un chat real; ambos puntos quedan señalados En desarrollo y documentados en `integrar-ia.md`. La cámara/lector físico no se volvieron a probar en esta actualización; el lector/OCR sigue sin conectar y el recorrido sin cita utiliza vinculación humana.
