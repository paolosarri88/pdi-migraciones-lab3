# Conectar Microsoft Foundry desde GCP

## Qué se necesita

Una sesión vigente en el directorio correcto, suscripción habilitada, permisos para el recurso y un despliegue de modelo con entrada de imágenes. El error del portal no diagnostica por sí solo cuál de estos elementos falta. El proyecto utiliza documentos ficticios; no se deben enviar documentos personales a esta demostración.

1. Iniciar sesión: `az login --tenant TU-TENANT`. Elegir con `--subscription` la suscripción autorizada en los comandos siguientes. No confundir la cuenta UAI con la cuenta del directorio Bytequest.
2. Consultar recursos: `az cognitiveservices account list --subscription TU-SUSCRIPCION -o table`.
3. Si existe un recurso adecuado, consultar sus despliegues: `az cognitiveservices account deployment list -g TU-GRUPO -n TU-RECURSO --subscription TU-SUSCRIPCION -o table`.
4. Si no existe, preparar un recurso y despliegue siguiendo la guía oficial de CLI/Bicep enlazada abajo. Consultar modelos y SKU disponibles para esa suscripción/región antes de elegirlos. No contratar capacidad provisionada para esta pequeña prueba. La disponibilidad, permiso y cuota deben comprobarse; no se garantizan con una cuenta educativa.
5. Con el recurso listo, conectar sin copiar su clave a Git ni a un argumento de terminal:

```sh
python3 scripts/connect_foundry.py --project TU-PROYECTO-GCP --subscription TU-SUSCRIPCION-AZURE --resource-group TU-GRUPO --account TU-RECURSO --deployment TU-DESPLIEGUE --enable-auto
python3 scripts/deploy.py --project TU-PROYECTO-GCP --billing-account TU-FACTURACION --phase app
```

El primer script verifica el despliegue, obtiene la clave en memoria y la envía a Secret Manager por entrada estándar. Actualiza la configuración compartida de Terraform con nombres de recursos y la versión del secreto, nunca con la clave. El segundo aplica Terraform para permitir solo a la identidad de la aplicación leer ese secreto y publicar las referencias en Cloud Run. Quien ejecute estos pasos necesita los permisos correspondientes en ambas nubes.

## Comportamiento

- `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY` y `AZURE_OPENAI_DEPLOYMENT` habilitan la asistencia del funcionario.
- `AUTO_DOCUMENT_REVIEW=1` activa además la lectura visual de cada archivo nuevo. El aviso del cargador informa su envío a Azure. Los archivos existentes no se procesan retroactivamente.
- Los documentos de hasta tres páginas se convierten en imágenes para la prevalidación. Los protegidos, extensos o ambiguos pasan a revisión manual. Un fallo del servicio conserva el archivo y la posibilidad de revisión.
- El resultado es una recomendación de admisibilidad del archivo: registra su origen y requiere decisión del funcionario. No cambia el estado documental ni resuelve el trámite completo.
- Para desactivar la automatización, cambiar `auto_document_review` a `false` en la configuración local y aplicar de nuevo el despliegue. Para retirar toda la integración, vaciar las tres variables `azure_openai_*` y revisar el plan de Terraform.

## Evidencia pendiente

Registrar nombre y versión real del modelo, región, resultado de una llamada desde el portal GCP, tiempos y errores, sin claves ni tokens. Ejecutar los casos definidos en `criterios-documentales-ia.md`. Hasta entonces la integración está preparada, pero no comprobada como requisito cumplido.

Referencias: [crear despliegues con CLI/Bicep](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/how-to/create-model-deployments), [modelos con visión](https://learn.microsoft.com/azure/ai-foundry/openai/how-to/gpt-with-vision).

## Conexión compartida del proyecto PDI

Las referencias públicas del despliegue se conservan en `infra/foundry-config.auto.tfvars.json`: endpoint de Foundry, despliegue `gpt-4.1-mini`, secreto `pdi-foundry-key` y versión `1`. La clave permanece exclusivamente en Secret Manager. La revisión documental automática está activada para archivos nuevos desde los criterios v2. No crear otra configuración local con valores contradictorios sin revisar el plan.

En el expediente del funcionario, cada documento permite pulsar **Generar sugerencia con IA**. Este endpoint lee únicamente ese archivo y guarda su recomendación en él. No cambia decisiones documentales ni el estado del expediente. Utiliza los mismos criterios que la prevalidación al subir archivos nuevos.

### Verificación del 24 de noviembre de 2026

Se comprobó una respuesta HTTP 200 desde el endpoint de asistencia del portal y se ejecutó **Analizar antecedentes** en la interfaz del funcionario para SOL-2026-0013. La respuesta de Microsoft Foundry se mostró en pantalla y quedó como sugerencia interna; no se guardó ninguna decisión documental ni resolución. Pasaron 29 pruebas Python, la comprobación conjunta de JavaScript y la validación de Terraform. El plan aplicado cambió la imagen de Cloud Run e incorporó el permiso de lectura del secreto ya existente; no eliminó recursos.

Esto verifica conectividad, no calidad documental: el modelo calificó el contenido ficticio como no confiable. Es necesario ajustar y evaluar el prompt con los criterios del proyecto antes de presentar sus recomendaciones como validación de documentos. La lectura visual automática sigue apagada.
