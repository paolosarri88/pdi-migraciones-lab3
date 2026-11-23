# Estado de la entrega y trabajo compartido

## Pauta confirmada

La página 2 de «Laboratorios Prácticos 2026» pide para el laboratorio 3: código de una prueba de concepto, archivos de ejecución, pasos para replicar la infraestructura, URL y documentación para ejecutar la prueba. La nota al pie exige GCP e incorporar soluciones de IA desde Microsoft Foundry con los créditos universitarios. El buzón indicado cierra el martes 24 de noviembre a las 23:59.

## Qué existe y qué falta

| Elemento | Estado | Evidencia / siguiente cierre |
|---|---|---|
| Código de la PoC | Implementado | Flask, portales por rol, documentos, citas, tótem e historial |
| URL compartida | Publicada en GCP | Cloud Run HTTPS; datos compartidos en PostgreSQL y Storage |
| Scripts IaC | Implementados | `infra/main.tf`, Dockerfile y `scripts/deploy.py` |
| Guía para replicar infraestructura | Escrita | `docs/despliegue-gcp.md`; falta que otra persona reproduzca desde cero en un proyecto autorizado y registre el resultado |
| Guía para usar/ejecutar PoC | Escrita | README y `docs/ejecutar-poc.md` |
| IA real de Microsoft Foundry | Pendiente de acceso y evidencia | Adaptador de asistencia y prevalidación visual; no afirmar cumplimiento solo por tener código o un enlace al portal |
| Criterios y evaluación de IA | Criterios preparados; evaluación real pendiente | `document_rules.py`, prompt versionado y `docs/criterios-documentales-ia.md` |
| Verificaciones funcionales | Automatizadas y manuales | Conservar resultados fechados en `docs/verificacion-gcp.md`; actualizar tras cada despliegue relevante |
| Archivo final de entrega | Preparar al cerrar IA y evidencias | Incluir solo código, configuración de ejemplo y documentación; excluir datos, claves, estado y planes de Terraform |

## Cómo interviene IaC

Terraform describe los recursos deseados: Cloud Run, Cloud SQL, buckets, identidades, permisos, secretos y avisos de presupuesto. `scripts/deploy.py` inicializa Terraform, calcula y aplica planes, construye el contenedor con Cloud Build y publica la aplicación. El código Flask define la lógica del portal; no reemplaza la infraestructura. Que la web funcione en el computador no demuestra por sí solo la réplica cloud.

## Azure y la captura recibida

La captura muestra el catálogo de Foundry dentro de Azure Portal, con errores al cargar recursos. No prueba que haya un modelo desplegado ni que falten permisos: se deben verificar suscripción, directorio, sesión, roles y cuota. El diagnóstico por CLI encontró una sesión expirada de la cuenta del curso y una suscripción universitaria personal no resoluble en la sesión disponible. Se renovó la sesión UAI: el directorio universitario no devuelve suscripciones accesibles. La cuenta Bytequest no fue reconocida en el inicio de sesión indicado por el usuario. Falta confirmar con la Universidad la cuenta y suscripción vigentes para este laboratorio.

No es obligatorio usar la interfaz del portal de Foundry para consumir el modelo: Microsoft documenta el despliegue y gestión mediante CLI/Bicep y consumo por API. Si el portal falla pero la cuenta tiene suscripción, permisos y cuota, esa ruta puede funcionar. No permite saltarse restricciones del tenant ni crear recursos sin permisos. Ver `docs/conectar-foundry.md`.

## Frentes que pueden escoger entre ambos

- **Recorridos ciudadanos:** lenguaje, documentos comprensibles, duplicados, correcciones, avisos que aparecen y desaparecen a tiempo, citas y calendario.
- **Recorridos funcionarios y seguridad:** revisar por documento, observaciones útiles, decisiones finales coherentes, acceso a expedientes y descargas según rol.
- **IA:** ejemplos ficticios y etiquetas esperadas, criterios, errores, medición y evidencia de una llamada real Azure desde GCP.
- **Reproducibilidad y entrega:** ejecutar las guías como lector nuevo, detectar pasos implícitos, guardar evidencias y comprobar que el paquete no incluye secretos.

No son tareas asignadas a Camilo. Elijan qué frente toma cada uno y avisen los folios/archivos que están tocando para no pisarse. Usen ramas y cambios pequeños; revisen antes de integrar a main.

## Recomendado para una entrega completa

Se agregaron `arquitectura-poc.md` y `matriz-pruebas.md`, que muestran la arquitectura real, la conexión Azure pendiente, historias de usuario, verificaciones y límites. El plan de costos y cierre está en la guía GCP. Son elementos útiles para explicar el trabajo; la pauta no exige una arquitectura productiva completa, VPN, WAF, SMS, ClaveÚnica real ni implementar todos los trámites nacionales. Falta completar la evidencia real de IA y consolidar el paquete final.
