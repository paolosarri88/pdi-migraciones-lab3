# Avisos por documento faltante

El funcionario pulsa **Notificar al ciudadano** dentro del requisito pendiente. Se verifica que el expediente esté abierto, que ese requisito pertenezca al expediente y que todavía no tenga un archivo. Se crea un aviso real en el portal, enlazado a la solicitud. Un aviso idéntico sin leer se devuelve sin duplicarlo. Cuando se aporta el archivo o cierra el expediente, ese aviso deja de presentarse como pendiente.

## Correo y WhatsApp preparados, sin envíos externos

Por decisión del equipo, estos canales no están activos. La tabla `notification_deliveries` conserva una fila por canal y aviso, con `pending_configuration` cuando existe contacto y `no_contact` cuando falta. Esto no es una cola de envío activo ni evidencia de entrega. No se consumen servicios de correo ni WhatsApp y no se usa la cuenta personal de Gmail para avisos del portal.

Para habilitar un canal falta elegir proveedor y remitente autorizado, configurar las credenciales en Secret Manager e implementar su adaptador/worker con registro de intentos, identificador del proveedor, confirmaciones de entrega, reintentos e idempotencia por `(notification_id, channel)`. Antes de enviar, el worker deberá volver a comprobar el contacto y que el documento siga pendiente. Los registros históricos `pending_configuration` no deben enviarse automáticamente al habilitar un proveedor; primero deben descartarse o aprobarse expresamente. No mostrar “enviado” sin aceptación del proveedor. WhatsApp necesita además cumplir los requisitos del proveedor para mensajes iniciados por la institución.

## Comprobación en el portal desplegado

El 24 de noviembre se generó un aviso para el antecedente de domicilio de SOL-2026-0042 y se verificó su recepción mediante la cuenta ciudadana de Niko Bellic. Los canales externos conservaron `pending_configuration`. También se comprobó el rechazo sugerido del PDF genérico de SOL-2026-0013 y de una identificación simulada completa pero vencida en SOL-2026-0044. No se modificaron decisiones humanas.
