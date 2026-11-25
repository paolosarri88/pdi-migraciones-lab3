# Portal de atención migratoria · PoC PDI

Paolo Sarri y Camilo Bresciani · Arquitectura Cloud · Laboratorio 3.

**Empezar por [LEEME_ENTREGA.md](LEEME_ENTREGA.md)**: URL, cuentas y correspondencia de los archivos con la entrega.

## Probar sin instalar

https://pdi-portal-vwjcdgy22a-uc.a.run.app/

Ciudadano: `ciudadano@demo.pdi.cl` / `Ciudadano2026!`. Funcionario: `funcionario@demo.pdi.cl` / `Funcionario2026!`. Administrador: `admin@demo.pdi.cl` / `Admin2026!`.

El tótem está en `/totem`. GEPOL y Registro Civil se simulan en `/simuladores/gepol` y `/simuladores/registro-civil`. No son servicios oficiales ni usan ClaveÚnica real.

## Ejecutar localmente

Requisitos: Python 3.11 o superior; Node.js solo para la comprobación de frontend. Desde la carpeta que contiene `app.py`:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

En Windows usar `.venv\Scripts\python.exe` en lugar de `.venv/bin/python`. Abrir http://127.0.0.1:8080. Detener con Ctrl+C. Si 8080 está ocupado, en macOS/Linux ejecutar `PORT=8081 .venv/bin/python app.py`.

La primera ejecución crea datos sintéticos. En local persisten en `data/portal.sqlite3`, `data/files/` y `data/.session-key`. No se incluyen en la entrega. Sin variables Azure válidas, la aplicación informa que la IA no está configurada y mantiene la revisión manual.

## Guías

- [Demostrar y utilizar la PoC](docs/ejecutar-poc.md).
- [Replicar infraestructura GCP](docs/despliegue-gcp.md).
- [Replicar y conectar Azure Foundry](docs/replicar-azure.md).
- [Arquitectura desplegada](docs/arquitectura-poc.md).
- [Estado y límites de entrega](docs/estado-entrega.md).
- [Criterios y evidencia documental](docs/criterios-documentales-ia.md).
- [Avisos del portal y canales externos](docs/avisos-documentales.md).

## Ejecutar las comprobaciones

```sh
.venv/bin/python -m unittest discover -s tests -v
node tests/frontend_smoke.cjs
```

Las pruebas usan datos temporales aislados. No ejecutarlas sobre la base cloud del portal: el modo PostgreSQL exige una base aislada con prefijo `pdi_validation_`. Se comprobaron 40 pruebas Python y los scripts del frontend juntos.

## Infraestructura y secretos

Cloud Run sirve web/API, Cloud SQL PostgreSQL guarda registros, Cloud Storage privado guarda archivos y Secret Manager contiene secretos. Terraform y `scripts/deploy.py` describen y publican GCP. La IA usa Microsoft Foundry, despliegue `gpt-4.1-mini`; el botón **Generar sugerencia con IA** actúa sobre un archivo y mantiene la decisión humana separada. El análisis al subir archivos depende de `AUTO_DOCUMENT_REVIEW`.

El ZIP excluye `infra/foundry-config.auto.tfvars.json` del proyecto original. En una réplica se genera la configuración propia mediante `scripts/connect_foundry.py`; no reutilizar claves ni nombres de secretos de la cuenta del equipo. No compartir `.env`, estado/planes de Terraform ni archivos personales. Los presupuestos son avisos, no cortes de gasto. No se crean recursos cloud por descomprimir el ZIP o ejecutar localmente.

## Licencias y referencias visuales

El SVG de referencia de PDI se basa en [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Policia_de_Investigaciones_de_Chile.svg), atribuido a PDI como PD-textlogo. El portal se identifica como prototipo académico. MediaPipe incluye licencia Apache-2.0 y referencias dentro de `static/vendor/mediapipe/`. Los personajes y escenarios administrativos son ficticios; ver `docs/personajes-gta.md`.

El código actual de la entrega está en la rama `Paolo`: https://github.com/paolosarri88/pdi-migraciones-lab3/tree/Paolo . El repositorio es privado; el ZIP permite revisar el código sin depender de permisos GitHub.
