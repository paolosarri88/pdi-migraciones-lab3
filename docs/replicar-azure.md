# Replicar Azure y conectar la IA documental

Esta guía complementa `despliegue-gcp.md`. Primero probar la URL publicada o la ejecución local; replicar cloud requiere cuentas autorizadas, cuota y puede consumir crédito. No es necesario crear recursos nuevos para evaluar la URL existente.

## 1. Elegir la cuenta correcta

Requisitos: Azure CLI, sesión de una suscripción autorizada para el curso y permisos para crear un recurso de IA/desplegar modelos. El modelo usado en la demostración es `gpt-4.1-mini` con entrada de texto e imágenes. La disponibilidad de región, versión y cuota depende de cada suscripción.

```sh
az login --tenant TU-TENANT
az account show --subscription TU-SUSCRIPCION --query '{name:name,state:state}' -o table
```

Todos los comandos siguientes usan explícitamente `--subscription`; sustituir los marcadores por los recursos propios. No ingresar ni compartir claves en la línea de comandos.

## 2. Crear o identificar el recurso

Si existe un recurso compatible del equipo/evaluador, consultar sus datos y saltar su creación. En un entorno nuevo autorizado:

```sh
az group create --name TU-GRUPO --location eastus2 --subscription TU-SUSCRIPCION
az cognitiveservices account create --name TU-NOMBRE-UNICO --resource-group TU-GRUPO --custom-domain TU-NOMBRE-UNICO --location eastus2 --kind AIServices --sku S0 --subscription TU-SUSCRIPCION
az cognitiveservices account list-models --name TU-NOMBRE-UNICO --resource-group TU-GRUPO --subscription TU-SUSCRIPCION --query "[?name=='gpt-4.1-mini'].{name:name,version:version,format:format,skus:skus}" -o json
```

`eastus2` es un ejemplo de región para la réplica, no una afirmación sobre la región del recurso del equipo. Si no aparece el modelo o SKU, elegir otra región admitida o resolver la cuota antes de continuar; no contratar capacidad provisionada para esta demostración. La PoC consume el despliegue por API; no depende del nombre del proyecto visual que se creó dentro de Foundry.

## 3. Desplegar el modelo

Sustituir `VERSION-DISPONIBLE` por una versión efectivamente listada en el paso anterior y comprobar que admite `GlobalStandard` y la capacidad elegida. La capacidad es un parámetro de cuota, no el número de servidores del portal.

```sh
az cognitiveservices account deployment create --name TU-NOMBRE-UNICO --resource-group TU-GRUPO --deployment-name gpt-4.1-mini --model-name gpt-4.1-mini --model-version VERSION-DISPONIBLE --model-format OpenAI --sku-name GlobalStandard --sku-capacity 1 --subscription TU-SUSCRIPCION
az cognitiveservices account deployment show --name TU-NOMBRE-UNICO --resource-group TU-GRUPO --deployment-name gpt-4.1-mini --subscription TU-SUSCRIPCION --query properties.provisioningState -o tsv
```

Debe responder `Succeeded`. Si la suscripción exige otro mínimo de capacidad, usar el valor permitido que devuelva el catálogo. No se garantiza que una cuenta universitaria tenga acceso a cualquier modelo o región.

## 4. Conectar con el proyecto GCP nuevo

Completar primero el despliegue GCP de `despliegue-gcp.md` y conservar su estado local. Desde la raíz del proyecto, con ambas CLI autenticadas:

```sh
python3 scripts/connect_foundry.py --project TU-PROYECTO-GCP --subscription TU-SUSCRIPCION --resource-group TU-GRUPO --account TU-NOMBRE-UNICO --deployment gpt-4.1-mini --enable-auto
python3 scripts/deploy.py --project TU-PROYECTO-GCP --billing-account TU-FACTURACION --phase app
```

El primer script consulta el recurso/despliegue, toma la clave en memoria y crea una versión de `pdi-foundry-key` en Secret Manager del proyecto indicado. No imprime la clave ni la escribe al repositorio. Genera `infra/foundry-config.auto.tfvars.json` con endpoint, despliegue y referencia/versión de secreto. El segundo aplica el permiso del servicio y publica esas referencias en Cloud Run. Requiere permisos tanto sobre el recurso Azure como sobre el proyecto/Secret Manager GCP; no basta con tener acceso al portal ciudadano.

`--enable-auto` activa el análisis al subir archivos. Sin esa opción queda desactivado y el funcionario puede usar el botón individual **Generar sugerencia con IA**. La conexión sigue siendo real; la decisión documental continúa siendo humana.

## 5. Verificar por la aplicación

1. Entrar como ciudadano y crear un trámite de domicilio nuevo.
2. Adjuntar una identidad simulada con todos los campos definidos en `document_rules.py`; usar exactamente el nombre y RUN de esa cuenta.
3. Entrar como funcionario en otra sesión y abrir el mismo folio.
4. Abrir el documento y pulsar **Generar sugerencia con IA**. Debe aparecer el proveedor Microsoft Foundry, explicación y evidencia por campo.
5. Probar un CV ficticio y un documento completo vencido. Debe proponer rechazo. Con lectura ambigua o fallo del servicio debe pedir revisión, sin inventar una aceptación.
6. Verificar que el documento sigue En revisión hasta guardar la decisión del funcionario.

No se ha recreado desde cero una segunda suscripción para esta entrega. Sí se verificó inferencia real en el despliegue publicado; ver las evidencias y límites en `criterios-documentales-ia.md`.

Referencia oficial de los comandos y comprobaciones: [Microsoft Learn: desplegar modelos mediante Azure CLI y Bicep](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/how-to/create-model-deployments).
