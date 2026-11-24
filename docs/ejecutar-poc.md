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
6. Desde Mis citas, elegir un día y bloque libre, con solicitud relacionada opcional. La reserva queda Confirmada de inmediato.
7. En otra sesión, ingresar como funcionario. Buscar el folio. Revisar los documentos por separado, aceptar uno y observar otro con motivo. Comprobar el historial y la posibilidad de corregir un resultado automático si Azure está habilitado.
8. Volver al ciudadano: debe ver el aviso de antecedentes pendientes, la explicación y exactamente el documento que debe reemplazar. Enviarlo a revisión: desaparece la acción pendiente cuando ya no falta una acción del ciudadano.
9. El funcionario consulta las citas previstas, distinguiendo No ha llegado de la fila real. No programa citas desde su portal; el ciudadano ya reservó su bloque.
10. En la cita confirmada, abrir calendario y recordatorios; elegir varios plazos, guardar y descargar el `.ics`. Al importarlo, los avisos dependen de la aplicación de calendario. No se envían SMS.
11. Para demostrar llegada y atención, usar una cita confirmada de hoy: abrir `/totem`, elegir Sí, ingresar los números del código y completar copia/captura. Iniciar/finalizar desde Fila presencial. Sin cita, usar el turno provisional y su vinculación por funcionario. No reutilizar a ciegas códigos de una demostración anterior.
12. Entrar como administrador para consultar persistencia y cuentas. Verificar que otro ciudadano no puede abrir un expediente ajeno.

## IA: demostración pendiente de conexión real

Con el recurso Azure configurado, subir un ejemplo adecuado y un archivo claramente ajeno. Mostrar resultado por documento, explicación e historial; luego mostrar que el funcionario puede corregirlo. Ni el archivo ni el expediente se aprueban o rechazan por la IA: la recomendación requiere decisión del funcionario. Registrar evidencia según `docs/criterios-documentales-ia.md`.

Sin configuración, la aplicación permite la revisión manual. Un botón deshabilitado o el adaptador implementado no demuestran por sí solos el requisito de IA real.

## Registro de incidencias

Al reportar un problema, guardar: cuenta/rol ficticio, folio, sección, pasos, resultado esperado, resultado observado y captura. Distinguir errores de permisos, errores de estado y preferencias de diseño. Evitar probar ambos al mismo tiempo sobre el mismo expediente.

## Probar la ficha y las correcciones

1. Entra como funcionario y abre «Personas». Busca a Michael por nombre o `00000001-9`; revisa sus solicitudes y enlaces institucionales.
2. Para evitar modificar expedientes ya usados en otra prueba, registra una persona nueva con correo ficticio, clave inicial y RUN asignado. Desde su ficha crea una solicitud presencial.
3. Incorpora una copia indicando «Presentado presencialmente» y registra después tu decisión documental. Pide otro tipo con «Solicitar otro documento» y comprueba el aviso entrando como ese ciudadano. Cancela el requisito adicional con motivo para probar la corrección.
4. Registra su llegada sin cita en la ficha y abre «Atención presencial». Inicia y finaliza su atención. La bandeja online no debe mostrar la solicitud presencial.
5. En un expediente destinado a pruebas, registra rechazo y luego utiliza «Reabrir expediente». La historia debe explicar la reapertura; el selector normal no debe permitir saltarse ese paso. Rectifica una anotación de prueba y verifica que quede conservada en el apartado de rectificaciones.
6. Con un documento aceptado en una solicitud, crea otra del mismo ciudadano y tipo compatible. «Usar documento existente» debe incorporar una referencia pendiente de nueva revisión. Un documento con vencimiento pasado no debe ofrecerse ni aceptarse para reutilización.
7. Abre «Calendario y recordatorios»: prueba cerrar con la equis, Escape y haciendo clic fuera del recuadro. En documentos solo deben quedar las flechas individuales, sin filtro «Mostrar» ni botones globales.

## Recorrido de recepción con cámara

1. Abre `/totem` en otra ventana. Toca la bienvenida, responde si tienes cita y, en caso afirmativo, usa el teclado numérico con prefijo CITA- fijo.
2. Con cita, ingresa solo los números de una reserva confirmada para hoy. Sin cita, no ingreses RUN: se genera una recepción provisional que el funcionario vinculará tras revisar la copia.
3. Carga una identificación ficticia PDF/JPG/PNG de hasta 5 MB. El lector físico se representa visualmente; no está conectado a hardware.
4. Permite la cámara y mantén un único rostro visible cinco segundos. Si falta permiso/cámara, reintenta o acude al mesón. No existe botón que simule una detección exitosa ni comparación con la foto del documento.
5. Aparece el turno. Entra como funcionario en otra ventana, abre «Fila presencial» y usa «Llamar e iniciar». Se abre la ficha, el turno se anuncia con módulo y no se puede iniciar otra atención hasta finalizar esta.
6. La ficha muestra foto y copia de identificación para contraste visual. Crea una solicitud presencial; en Documento de identidad, usa «Incorporar identificación del tótem» y registra tu decisión después de revisarla.
7. Finaliza la atención desde la ficha o la fila. El tótem ya no solicita registrar la salida.

Para la presentación, comprobar la cámara en el navegador y computador definitivos antes de comenzar. No es una función de Foundry: la detección de rostro se ejecuta en el navegador y no acredita identidad.

## Flujo vigente de citas y deshacer

- En «Mis citas», selecciona atención general o solicitud, día y bloque libre. «Confirmar reserva» crea la cita Confirmada, sin esperar al funcionario. El horario de la PoC es lunes a viernes 09:00–16:00 en bloques de treinta minutos.
- En el mesón, «Citas previstas para hoy» muestra No ha llegado hasta pasar por el tótem. La fila de prioridad solo contiene llegadas registradas.
- En el tótem, responde si tienes cita. Con cita, escribe solo los números después del prefijo fijo CITA-. Sin cita, carga la copia y completa la captura; recibirás un turno provisional sin ingresar RUN. El funcionario lo vincula después de contrastar identidad.
- En la ficha, los folios bajo cada archivo llevan a su expediente. «Ver más» cambia a «Ver menos» al final de todos los documentos.
- En un expediente de prueba, acepta un documento y usa la papelera de esa última acción con motivo. El documento debe volver a revisión, no solo desaparecer la anotación. Prueba también deshacer un rechazo. Se deshace desde lo más reciente; no se deben eliminar acciones posteriores para saltarse sus dependencias.
- Si la solicitud está Resuelta, el ciudadano puede descargar el certificado de demostración. Si se deshace esa resolución, la descarga debe bloquearse nuevamente.
- El chat flotante solo aparece al ciudadano, se puede arrastrar y muestra En desarrollo. La propuesta IA del documento también está preparada, con la misma indicación mientras no esté conectada. Ver `integrar-ia.md`.

La restauración completa corresponde a acciones con instantánea antes/después. Un registro antiguo incompleto puede requerir corrección explícita porque el sistema no inventa su estado anterior.
