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

El primer script verifica el despliegue, obtiene la clave en memoria y la envía a Secret Manager por entrada estándar. Crea una configuración local ignorada por Git con nombres de recursos, no con la clave. El segundo aplica Terraform para permitir solo a la identidad de la aplicación leer ese secreto y publicar las referencias en Cloud Run. Quien ejecute estos pasos necesita los permisos correspondientes en ambas nubes.

## Comportamiento

- `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY` y `AZURE_OPENAI_DEPLOYMENT` habilitan la asistencia del funcionario.
- `AUTO_DOCUMENT_REVIEW=1` activa además la lectura visual de cada archivo nuevo. El aviso del cargador informa su envío a Azure. Los archivos existentes no se procesan retroactivamente.
- Los documentos de hasta tres páginas se convierten en imágenes para la prevalidación. Los protegidos, extensos o ambiguos pasan a revisión manual. Un fallo del servicio conserva el archivo y la posibilidad de revisión.
- El resultado se limita a la admisibilidad académica del archivo, registra su origen y permite corrección por el funcionario. Nunca resuelve el trámite completo.
- Para desactivar la automatización, cambiar `auto_document_review` a `false` en la configuración local y aplicar de nuevo el despliegue. Para retirar toda la integración, vaciar las tres variables `azure_openai_*` y revisar el plan de Terraform.

## Evidencia pendiente

Registrar nombre y versión real del modelo, región, resultado de una llamada desde el portal GCP, tiempos y errores, sin claves ni tokens. Ejecutar los casos definidos en `criterios-documentales-ia.md`. Hasta entonces la integración está preparada, pero no comprobada como requisito cumplido.

Referencias: [crear despliegues con CLI/Bicep](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/how-to/create-model-deployments), [modelos con visión](https://learn.microsoft.com/azure/ai-foundry/openai/how-to/gpt-with-vision).
