# Portal de atención migratoria · Laboratorio 3

Prototipo académico UAI. No es un servicio oficial de PDI. Solo utiliza personas, expedientes y documentos ficticios.

## Probar y desplegar en Google Cloud

Portal publicado: https://pdi-portal-vwjcdgy22a-uc.a.run.app

La misma URL se puede abrir desde otro computador sin clonar este repositorio. [Resultados de verificación](docs/verificacion-gcp.md).

La configuración cloud ejecuta la web y la API en Cloud Run, los registros en Cloud SQL PostgreSQL y los documentos en Cloud Storage privado. Terraform y el script de despliegue están incluidos. Consulta [la guía de despliegue](docs/despliegue-gcp.md) para replicar la infraestructura, conocer los costos y cerrar los recursos después de la evaluación.

## Ejecutar en el computador

Requiere Python 3.11 o superior.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Abrir http://127.0.0.1:8080. En el computador de Paolo también está disponible `/opt/anaconda3/bin/python3 app.py`, con Flask ya instalado. El servidor local escucha solo en este computador.

## Cuentas de demostración

| Cuenta | Correo | Contraseña |
|---|---|---|
| Ciudadano | ciudadano@demo.pdi.cl | Ciudadano2026! |
| Funcionario | funcionario@demo.pdi.cl | Funcionario2026! |
| Administrador | admin@demo.pdi.cl | Admin2026! |

El inicio de sesión determina el portal. No hay un selector de roles. El tótem está separado en `/totem`: representa una pantalla de autoservicio del recinto, utilizada por el ciudadano para registrar llegada, consultar su turno y registrar salida. El funcionario atiende desde su agenda.

## Recorrido para probar

1. Entrar como ciudadano. Los contadores filtran solicitudes y los avisos llevan al expediente o cita correspondiente.
2. Abrir SOL-2026-0002, adjuntar un PDF, PNG o JPG de prueba (hasta 5 MB) y enviar antecedentes a revisión.
3. Confirmar la próxima cita desde «Mis citas». Sus fechas se calculan al crear los datos iniciales.
4. Iniciar otra solicitud desde el catálogo, completar sus campos, revisar y enviar. Descargar su comprobante PDF.
5. Cerrar sesión y entrar como funcionario. Buscar expedientes, registrar una observación y cambiar su estado, asignárselo o programar una cita.
6. En «Consulta institucional», consultar `DEMO-001` en GEPOL o Registro Civil. Son respuestas ficticias guardadas localmente y cada consulta queda registrada.
7. Abrir `/totem` en otra ventana. Para la cita inicial de hoy usar `CITA-1002`: registrar llegada. En la agenda del funcionario iniciar y finalizar la atención. Una llegada repetida se rechaza.
8. Entrar como administrador para consultar los registros y activar o desactivar cuentas de prueba. No se permite desactivar la propia cuenta.

Las fechas de los datos precargados se fijan el día del primer arranque. Para otro día, el funcionario puede programar nuevas citas. No se borran datos al reiniciar.

## Qué persiste

En modo local: SQLite en `data/portal.sqlite3`, archivos en `data/files/` y clave local de sesión en `data/.session-key`. En GCP: Cloud SQL, Cloud Storage y Secret Manager; las actualizaciones del contenedor no borran los registros ni los documentos. La primera ejecución crea 15 cuentas, 36 solicitudes con documentos, 5 citas y registros institucionales ficticios. La carpeta `data/` queda fuera de Git. Las contraseñas se almacenan mediante hash; los permisos y propiedad de expedientes se verifican en el servidor. Las operaciones de modificación requieren protección CSRF.

## IA y alcance de la infraestructura

La misma versión soporta ejecución local y despliegue GCP con Terraform. El código selecciona PostgreSQL cuando existe `DB_HOST` y almacenamiento privado cuando existe `DOCUMENT_BUCKET`. No se ha desplegado VPN, WAF ni conexión a sistemas institucionales reales. La simulación institucional vive en el mismo servidor de demostración, sin afirmar que constituye una red on-premise real.

El módulo de asistencia del funcionario admite Azure OpenAI mediante variables `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY` y `AZURE_OPENAI_DEPLOYMENT`. Sin ellas, informa que no está configurado y no inventa una respuesta de IA. Envía los antecedentes escritos y nombres de archivos; no realiza OCR ni lee el contenido de los documentos. La respuesta es apoyo preliminar y la decisión queda en el funcionario. Nunca agregar claves a Git.

## Catálogo y diseño

Once tipos de solicitudes con campos propios y expedientes compartidos. Los requisitos del prototipo son simplificados; no reproducen requisitos legales ni emiten certificados oficiales. Se incluyen enlaces externos para procedimientos fuera de la demostración. Referencias: https://www.pdichile.cl/home/pdi y https://www.pdichile.cl/tr%C3%A1mites-online. Los casos de revisión de ingreso, entrega de antecedentes, entrevista y orientación son escenarios académicos basados en el problema del proyecto. Residencia y nacionalización se derivan a https://serviciomigraciones.cl/.

Interfaz azul marino, blanco y gris, estados en texto, navegación lateral y superior, pie institucional de referencia y aviso académico. El texto PDI es una composición tipográfica de demostración, no un archivo de logotipo institucional oficial.

## Validación

```sh
python3 -m unittest discover -s tests -v
node --check static/app.js
```

Seis pruebas de integración, ejecutables contra SQLite o una base PostgreSQL aislada con nombre `pdi_validation_*`, cubren autenticación y CSRF, aislamiento entre ciudadanos, documentos, reenvío de antecedentes, citas, llegada/atención/salida, administración y simuladores institucionales. Las pruebas usan una base temporal separada.

## Trabajo compartido

`main` conserva la base compartida; `Paolo` y `Camilo` son ramas de trabajo. Integrar cambios revisados mediante pull requests. Los datos locales y secretos no se comparten con el repositorio.
