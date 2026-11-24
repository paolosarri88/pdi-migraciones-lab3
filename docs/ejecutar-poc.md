# Ejecutar y demostrar la prueba de concepto

## Qué documento usar

- **Replicar infraestructura:** `docs/despliegue-gcp.md` explica cómo crear los recursos cloud en un proyecto nuevo con Terraform y el script de despliegue.
- **Ejecutar la PoC:** esta guía explica cómo abrir la aplicación ya desplegada y demostrar sus funciones. Para ejecución local, seguir el README.

No hace falta clonar el repositorio para probar la URL. Los dos integrantes comparten los registros cloud, por lo que conviene anunciar qué expediente está usando cada uno.

## Acceso

URL: https://pdi-portal-vwjcdgy22a-uc.a.run.app

Los accesos ficticios están en «Datos de acceso para probar el portal» y en el README. El ciudadano usa `00000001-9` o `ciudadano@demo.pdi.cl`, clave `Ciudadano2026!`. Funcionario: `funcionario@demo.pdi.cl` / `Funcionario2026!`. Administrador: `admin@demo.pdi.cl` / `Admin2026!`. No ingresar ClaveÚnica, RUT ni documentos reales.

## Demostración sugerida

1. Abrir el catálogo sin sesión: buscar un trámite y comprobar el acceso ciudadano destacado.
2. Ingresar como ciudadano. Revisar contadores, avisos accionables y buscar solicitudes por trámite o folio.
3. Crear un expediente de un tipo que no tenga otro activo. Completar antecedentes. Abrir la ayuda de cada documento y descargar sus ejemplos ficticios.
4. Adjuntar cada archivo en su sección. Probar un archivo mayor de 5 MB: debe rechazarse con texto rojo. Quitar un archivo equivocado y reemplazarlo antes de enviar.
5. Enviar y guardar el folio. En tipos que no permiten concurrencia, una solicitud activa del mismo tipo bloquea una nueva al comienzo y muestra «En proceso» en el catálogo. Viajes y domicilio admiten expedientes paralelos en esta configuración.
6. Desde Mis citas, solicitar atención presencial para un expediente activo sin cita vigente. Esa solicitud pide coordinación; no reserva una fecha automáticamente.
7. En otra sesión, ingresar como funcionario. Buscar el folio. Revisar los documentos por separado, aceptar uno y observar otro con motivo. Comprobar el historial y la posibilidad de corregir un resultado automático si Azure está habilitado.
8. Volver al ciudadano: debe ver el aviso de antecedentes pendientes, la explicación y exactamente el documento que debe reemplazar. Enviarlo a revisión: desaparece la acción pendiente cuando ya no falta una acción del ciudadano.
9. El funcionario programa una cita disponible para el expediente. El ciudadano recibe el aviso, confirma asistencia y el aviso de confirmar desaparece. La opción de confirmar permanece para citas aún no confirmadas.
10. En la cita confirmada, abrir calendario y recordatorios; elegir varios plazos, guardar y descargar el `.ics`. Al importarlo, los avisos dependen de la aplicación de calendario. No se envían SMS.
11. Para demostrar llegada y atención, usar una cita de hoy confirmada: abrir `/totem`, ingresar su código, registrar llegada; iniciar y finalizar atención desde la agenda del funcionario. No reutilizar a ciegas códigos de una demostración anterior.
12. Entrar como administrador para consultar persistencia y cuentas. Verificar que otro ciudadano no puede abrir un expediente ajeno.

## IA: demostración pendiente de conexión real

Con el recurso Azure configurado, subir un ejemplo adecuado y un archivo claramente ajeno. Mostrar resultado por documento, explicación e historial; luego mostrar que el funcionario puede corregirlo. Ni el archivo ni el expediente se aprueban o rechazan por la IA: la recomendación requiere decisión del funcionario. Registrar evidencia según `docs/criterios-documentales-ia.md`.

Sin configuración, la aplicación permite la revisión manual. Un botón deshabilitado o el adaptador implementado no demuestran por sí solos el requisito de IA real.

## Registro de incidencias

Al reportar un problema, guardar: cuenta/rol ficticio, folio, sección, pasos, resultado esperado, resultado observado y captura. Distinguir errores de permisos, errores de estado y preferencias de diseño. Evitar probar ambos al mismo tiempo sobre el mismo expediente.

## Probar la ficha y las correcciones

1. Entra como funcionario y abre «Personas». Busca a María por nombre o `00000001-9`; revisa sus solicitudes y enlaces institucionales.
2. Para evitar modificar expedientes ya usados en otra prueba, registra una persona nueva con correo ficticio, clave inicial y RUN asignado. Desde su ficha crea una solicitud presencial.
3. Incorpora una copia indicando «Presentado presencialmente» y registra después tu decisión documental. Pide otro tipo con «Solicitar otro documento» y comprueba el aviso entrando como ese ciudadano. Cancela el requisito adicional con motivo para probar la corrección.
4. Registra su llegada sin cita en la ficha y abre «Atención presencial». Inicia y finaliza su atención. La bandeja online no debe mostrar la solicitud presencial.
5. En un expediente destinado a pruebas, registra rechazo y luego utiliza «Reabrir expediente». La historia debe explicar la reapertura; el selector normal no debe permitir saltarse ese paso. Rectifica una anotación de prueba y verifica que quede conservada en el apartado de rectificaciones.
6. Con un documento aceptado en una solicitud, crea otra del mismo ciudadano y tipo compatible. «Usar documento existente» debe incorporar una referencia pendiente de nueva revisión. Un documento con vencimiento pasado no debe ofrecerse ni aceptarse para reutilización.
7. Abre «Calendario y recordatorios»: prueba cerrar con la equis, Escape y haciendo clic fuera del recuadro. En documentos solo deben quedar las flechas individuales, sin filtro «Mostrar» ni botones globales.
