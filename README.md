# Portal de atención migratoria · Laboratorio 3

Prototipo académico UAI. No es un servicio oficial de PDI. Solo utiliza personas, expedientes y documentos ficticios.

## Probar y desplegar en Google Cloud

Portal publicado: https://pdi-portal-vwjcdgy22a-uc.a.run.app

La misma URL se puede abrir desde otro computador sin clonar este repositorio. [Resultados de verificación](docs/verificacion-gcp.md).

La configuración cloud ejecuta la web y la API en Cloud Run, los registros en Cloud SQL PostgreSQL y los documentos en Cloud Storage privado. Terraform y el script de despliegue están incluidos. Consulta [la guía de despliegue](docs/despliegue-gcp.md) para replicar la infraestructura, conocer los costos y cerrar los recursos después de la evaluación.

## Personas de demostración

Las cuentas ciudadanas precargadas usan personajes de GTA y conservan sus RUN/correos/claves. [Mapa de cuentas, fuentes y datos inventados](docs/personajes-gta.md). El tótem incluye carga de identificación y captura con detección local de rostro; no verifica identidad.

## Atención online y presencial

La bandeja online está separada de «Atención presencial». «Personas» permite buscar una ficha, revisar todas sus solicitudes, registrar una llegada y crear un trámite en nombre del ciudadano. Los documentos adicionales, reaperturas y rectificaciones conservan trazabilidad. [Flujo y límites de la PoC](docs/flujo-atencion.md).

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

Los accesos ciudadano y corporativo tienen formularios distintos; el servidor comprueba el rol correspondiente. No hay un selector de roles. El tótem está separado en `/totem`: representa una pantalla de autoservicio del recinto, utilizada por el ciudadano para registrar llegada, consultar su turno y registrar salida. El funcionario atiende desde su agenda.

## Recorrido para probar

1. Entrar como ciudadano. Los contadores filtran solicitudes y los avisos llevan al expediente o cita correspondiente.
2. Abrir un expediente con antecedentes pendientes, adjuntar un PDF, PNG o JPG ficticio en el requisito correspondiente (hasta 5 MB) y enviar antecedentes a revisión cuando corresponda. Los ejemplos iniciales pueden haber sido modificados por otras pruebas.
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

El módulo de asistencia del funcionario admite Azure OpenAI mediante variables `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY` y `AZURE_OPENAI_DEPLOYMENT`. Sin ellas, informa que no está configurado y no inventa una respuesta de IA. La asistencia del funcionario resume antecedentes escritos y nombres de archivos. Un adaptador separado permite prevalidación visual de archivos nuevos cuando se configura Azure y `AUTO_DOCUMENT_REVIEW=1`: puede proponer aceptar u observar el archivo, o pedir ayuda al funcionario. Su recomendación se guarda por separado y no cambia el estado del documento. El funcionario confirma cada decisión y el resultado del expediente. La llamada real y su calidad permanecen pendientes de comprobar con una sesión Azure válida. Nunca agregar claves a Git.

## Catálogo y diseño

Once tipos de solicitudes con campos propios y expedientes compartidos. Los requisitos del prototipo son simplificados; no reproducen requisitos legales ni emiten certificados oficiales. Se incluyen enlaces externos para procedimientos fuera de la demostración. Referencias: https://www.pdichile.cl/home/pdi y https://www.pdichile.cl/tr%C3%A1mites-online. Los casos de revisión de ingreso, entrega de antecedentes, entrevista y orientación son escenarios académicos basados en el problema del proyecto. Residencia y nacionalización se derivan a https://serviciomigraciones.cl/.

Interfaz azul marino, blanco y gris, estados en texto, navegación lateral y superior, pie institucional de referencia y aviso académico. La marca PDI usa contornos vectoriales de referencia, sin depender de una fuente instalada. Referencia: [SVG en Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Policia_de_Investigaciones_de_Chile.svg), atribuido a PDI y publicado como PD-textlogo. Colores de referencia: #00234c y #ffd100. El portal mantiene su identificación como prototipo académico.

## Validación

```sh
python3 -m unittest discover -s tests -v
node --check static/app.js
```

Diecinueve pruebas de integración, ejecutables contra SQLite o una base PostgreSQL aislada con nombre `pdi_validation_*`, cubren autenticación y CSRF, aislamiento entre ciudadanos, documentos, reenvío de antecedentes, citas, llegada/atención/salida, administración y simuladores institucionales. Las pruebas usan una base temporal separada.

## Trabajo compartido

`main` conserva la base compartida; `Paolo` y `Camilo` son ramas de trabajo. Integrar cambios revisados mediante pull requests. Los datos locales y secretos no se comparten con el repositorio.

### Actualización de experiencia y documentos

Ingreso con RUN ficticio `00000001-9` o correo de demostración (misma clave ciudadana). No se conecta con ClaveÚnica real. Búsqueda inmediata por trámite y folio, control temprano de duplicados, documentos separados por requisito, revisión individual con versiones e historial, avisos que dejan de pedir acciones completadas y validaciones en español. Las citas confirmadas permiten descargar un archivo `.ics` con varios recordatorios; el teléfono es una preferencia de prueba y no se envían SMS.

## Guías para la entrega

- [Replicar infraestructura GCP](docs/despliegue-gcp.md).
- [Ejecutar y demostrar la PoC](docs/ejecutar-poc.md).
- [Estado de entrega y frentes compartidos](docs/estado-entrega.md).
- [Arquitectura realmente desplegada](docs/arquitectura-poc.md).
- [Historias y matriz de pruebas](docs/matriz-pruebas.md).
- [Criterios de documentos y evaluación IA](docs/criterios-documentales-ia.md).
- [Conectar Foundry](docs/conectar-foundry.md).

Los avisos accionables se reconstruyen desde documentos y citas pendientes, aunque se hayan leído. En Mis citas se puede solicitar coordinación de atención para un expediente activo sin cita; el funcionario agenda y luego el ciudadano confirma. Las ayudas desplegables explican cada requisito y ofrecen PDF ficticios de ejemplo.

## Operación actualizada

Consulta [el flujo de atención, accesos y simuladores](docs/flujo-atencion.md). Los documentos se muestran contraídos y permiten filtrar «Por revisar» o «Todos». La bandeja prioriza atenciones presenciales y muestra la siguiente acción del funcionario. La carga de archivos por funcionario requiere procedencia de correo explícita.

El ciudadano puede crear una cuenta; se asigna un RUN sintético, sin puntos y con guion. Las identidades precargadas se pueden consultar desde el desplegable del ingreso. Los certificados de viajes y domicilio permiten solicitudes paralelas según la configuración académica.

Las ventanas independientes están en `/simuladores/gepol`, `/simuladores/registro-civil` y `/totem`. Son rutas de un mismo despliegue, sin servidores nuevos ni conexión a sistemas institucionales reales. La interfaz de consulta abre ventanas con el RUN seleccionado. La cámara y la biometría quedan fuera del flujo definido.
