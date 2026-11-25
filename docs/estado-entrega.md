# Estado de entrega · 24 de noviembre de 2026

Según el fragmento de pauta proporcionado, se solicitan archivos de ejecución, pasos para replicar la infraestructura, URL y documentación para ejecutar la PoC. `LEEME_ENTREGA.md` relaciona cada requisito con sus archivos.

| Componente | Estado al cierre |
|---|---|
| Código y contenedor | Incluidos; Python/Flask, recursos web y Dockerfile |
| Infraestructura GCP | Desplegada y descrita con Terraform y scripts |
| URL compartida | Cloud Run con Cloud SQL y Cloud Storage privado |
| Azure Foundry | Conectado y probado con inferencias reales de `gpt-4.1-mini` desde el portal |
| IA documental | Lee archivos y contrasta campos/titular/vigencia; propuesta por documento, confirmación humana |
| Evaluación de IA | Casos concretos verificados; evaluación amplia y precisión general pendientes |
| Avisos | Portal funcional; correo y WhatsApp preparados sin proveedor ni envíos externos |
| Chat ciudadano | Interfaz en desarrollo; sin chatbot conectado |
| Simuladores institucionales | Ficticios; no conectados a PDI ni Registro Civil reales |
| Tótem | Flujo de cita/sin cita, copia y cámara; sin lector físico ni comparación biométrica |
| Validación | 40 pruebas Python y control frontend; recorridos reales documentados |
| Replicación desde cero | Guías incluidas; no se afirma haber repetido todo en una segunda cuenta nueva |

El paquete está pensado para entregar código y documentación, no credenciales de las cuentas cloud. No desactivar los recursos publicados antes de la evaluación. La URL depende de que los recursos y créditos permanezcan activos. `docs/verificacion-gcp.md` es una bitácora histórica: sus entradas iniciales anteriores a la conexión Azure no describen el estado final.
