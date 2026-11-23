# Despliegue de la prueba de concepto en GCP

## Alcance

La misma aplicación sirve los portales, el tótem y la API desde Cloud Run. No se contratan tres servidores independientes. Cloud SQL PostgreSQL conserva registros y Cloud Storage conserva documentos privados. Los archivos se entregan exclusivamente desde la API autenticada, comprobando la propiedad del expediente. GEPOL y Registro Civil siguen siendo simulaciones con datos ficticios. Microsoft Foundry no se despliega ni se factura en GCP.

La región económica elegida para esta demostración es `us-central1`. Esta configuración no afirma residencia de datos en Chile ni replica la arquitectura productiva del laboratorio 2.

## Antes de empezar

Instalar Python 3.11 o superior, [Google Cloud CLI](https://docs.cloud.google.com/sdk/docs/install-sdk) y [Terraform](https://developer.hashicorp.com/terraform/install). Iniciar sesión con una cuenta que tenga permisos para crear recursos en el proyecto y utilizar la cuenta de facturación educativa:

```sh
gcloud auth login
gcloud projects create TU-PROYECTO --name="PDI Laboratorio 3"
gcloud billing projects link TU-PROYECTO --billing-account=TU-CUENTA-DE-FACTURACION
```

Utilizar un proyecto nuevo dedicado al laboratorio. Verificar el crédito en Facturación > Créditos. Los US$50 son un saldo de consumo, no un presupuesto mensual que se renueve. No habilitar una cuenta de facturación personal diferente para este despliegue.

## Crear infraestructura y desplegar

Desde la raíz del repositorio:

```sh
python3 scripts/deploy.py --project TU-PROYECTO --billing-account TU-CUENTA-DE-FACTURACION
```

El script ejecuta estas etapas:

1. Inicializa Terraform y genera un plan concreto de recursos.
2. Aplica el plan: APIs, identidades, permisos, Cloud SQL, base, usuario, secretos, almacenamiento, registro de imágenes y avisos de presupuesto.
3. Cloud Build construye el contenedor a partir del Dockerfile. No es necesario tener Docker ejecutándose en el computador.
4. Genera y aplica un segundo plan con la imagen construida y el servicio Cloud Run.
5. Muestra la URL HTTPS asignada por Google. Abrirla y utilizar las cuentas de demostración del README.

El proyecto debe existir y tener facturación habilitada antes de ejecutar el script. Se puede dividir el trabajo mediante `--phase foundation` y luego `--phase app`. El segundo comando sirve también para actualizar el código de la aplicación. El servicio público es únicamente el portal; la base no tiene redes IP autorizadas y los contenedores de almacenamiento impiden acceso público.

La primera ejecución en Cloud Run crea los registros ficticios y los PDF de prueba directamente en PostgreSQL y Cloud Storage. El despliegue no carga la carpeta local `data/` ni datos que se hayan introducido en el portal local. Una clave de sesión estable en Secret Manager permite compartir sesión entre instancias y mantenerla durante actualizaciones normales. No existen claves descargadas de cuentas de servicio.

## Comprobar

- `/health` debe responder con estado correcto.
- Iniciar sesión como ciudadano; revisar solicitudes y abrir un PDF precargado.
- Crear una solicitud y adjuntar un archivo ficticio; comprobarla desde la cuenta del funcionario.
- Abrir la URL desde un navegador distinto para que Camilo vea los mismos registros.
- Cambiar de instancia o actualizar el contenedor no debe borrar expedientes ni documentos.
- Verificar en administración que la persistencia indica PostgreSQL y Cloud Storage.
- El botón de IA permanece no disponible hasta configurar un servicio real de Azure; no se presenta una respuesta simulada como IA real.

## Tamaño y consumo

| Recurso | Configuración de demostración |
|---|---|
| Cloud Run | 1 vCPU, 512 MiB, 0 instancias mínimas, máximo 2, concurrencia 4 |
| Cloud SQL | PostgreSQL 16 Enterprise, db-f1-micro, una zona, 10 GB SSD, sin aumento automático de disco |
| Respaldos | 3 copias automáticas; sin recuperación a un instante específico |
| Documentos | Cloud Storage Standard regional, acceso privado |
| Compilaciones | Cloud Build bajo demanda; fuentes y registros temporales con limpieza a 7 días |
| Avisos | US$40/mes de consumo bruto, umbrales US$10, US$20, US$30 y US$40 |

Los avisos miden consumo antes de aplicar créditos, para que un saldo facturado de cero no oculte el uso del cupón. No constituyen un corte automático de gasto. La base tiene costo aunque nadie navegue y conserva costo de almacenamiento si se detiene. El límite de instancias reduce el escalamiento, pero no garantiza un monto máximo. Los detalles de facturación pueden aparecer con retraso.

Referencias oficiales: [Cloud Run](https://cloud.google.com/run/pricing), [Cloud SQL](https://cloud.google.com/sql/pricing), [Cloud Storage](https://cloud.google.com/storage/pricing) y [presupuestos](https://docs.cloud.google.com/billing/docs/how-to/budgets). La referencia de CPU compartida db-f1-micro en Iowa es US$0,0105/h, aproximadamente US$7,67 por 730 horas; se suman disco, respaldos y otros consumos. Esto no es una garantía del importe final. Las instancias compartidas son apropiadas para esta prueba y no tienen el SLA de instancias dedicadas.

## Conservación y cierre

No borrar recursos mientras el grupo esté probando o antes de la evaluación. Después de guardar la evidencia y exportar los datos ficticios necesarios, revisar el plan de eliminación de Terraform. Cloud SQL tiene protección contra borrado y el contenedor de documentos no permite vaciarse automáticamente. El cierre definitivo requiere desactivar esas protecciones conscientemente y confirmar la eliminación. No basta con cerrar el navegador para detener los cobros.

El estado de Terraform y sus planes contienen secretos: conservarlos fuera de Git y de archivos de entrega públicos. La configuración los ignora y el script restringe los permisos de los archivos que genera. Para trabajar desde otro computador se necesita el estado seguro del despliegue existente o importar los recursos; no ejecutar otra creación sobre el mismo proyecto sin ese estado.
