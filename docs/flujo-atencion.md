# Flujo de atención y ventanas de simulación

## Roles y prioridad

Ciudadano: ingresa una solicitud, adjunta documentos, corrige antecedentes y solicita coordinación de una cita. Funcionario o administrador: revisa los documentos, toma decisiones, coordina la fecha/hora y atiende presencialmente.

La misma persona funcionaria puede atender ambos canales. La prioridad del prototipo es: atención presencial ya iniciada, luego personas con llegada registrada en orden de antigüedad, después expedientes online. «Atención presencial» muestra esa prioridad y botones para iniciar/finalizar atención. «Bandeja de solicitudes» muestra únicamente solicitudes originadas online; las presenciales se consultan en su sección y en la ficha de la persona. Las acciones de expediente distinguen revisar documentos, esperar antecedentes del ciudadano, coordinar cita, atención programada y resolver expediente. Una cita terminada deja de tratarse como una atención futura.

La cola presencial y las bandejas se actualizan cada cinco segundos. Las operaciones del tótem en otra pestaña del mismo navegador notifican además al portal mediante un evento de almacenamiento local. No es una integración con un sistema físico real ni una cola productiva distribuida.

## Documentos y recomendación IA

Los documentos se presentan contraídos, con flecha individual. Siempre aparecen todos: primero los pendientes de revisión, luego faltantes, rechazados, aceptados y versiones anteriores. Se guarda cada revisión por separado. No hay selector «Mostrar» ni controles globales de expandir/contraer. Los colores más visibles corresponden al estado humano; el resumen no agrega un segundo trazo junto al del documento.

La IA puede **proponer aceptar**, **proponer rechazar** o **pedir criterio al funcionario**. Su resultado se guarda aparte y nunca modifica el estado documental ni el expediente. En ausencia de IA real no se inventa una recomendación. El trazo de color corresponde al estado humano: revisión azul, aceptación verde, rechazo rojo y faltantes amarillo. El funcionario también decide el resultado final del expediente.

La carga por el funcionario aparece como «Incorporar copia recibida por el funcionario» y permite indicar correo o presentación presencial. Es una acción manual explícita con procedencia obligatoria; el portal no lee correos automáticamente. Se conserva la versión anterior y la procedencia del archivo.

## Accesos y cuentas

El ciudadano ingresa desde «Iniciar sesión»; funcionario/administrador desde «Ingreso funcionarios», con correo y contraseña. La cuenta determina sus permisos. Las formas se separan y el servidor valida el acceso indicado.

El RUN se ingresa sin puntos y con guion: `00000001-9` para María. El control verifica formato, no acredita identidad ante Registro Civil. En «Cuentas disponibles para probar» se listan las identidades precargadas y sus correos/RUN. Las cuentas ciudadanas precargadas comparten `Ciudadano2026!`; las cuentas nuevas usan su propia clave y no se publican en esa lista.

«Crear cuenta» solicita nombre, correo y clave, y asigna un RUN sintético. No solicita un RUT real ni otorga roles de funcionario o administrador. La confirmación muestra el RUN para ingresarlo después. No hay conexión real con ClaveÚnica ni envío de correo de verificación.

Los certificados de viajes y domicilio permiten más de un expediente activo en la configuración del prototipo. El resto conserva el control de duplicados y muestra «En proceso» en su tarjeta del catálogo. Esta es una regla de la simulación, no una afirmación sobre políticas legales de trámites reales.

## Tótem: flujo definido

URL: https://pdi-portal-vwjcdgy22a-uc.a.run.app/totem

1. El funcionario programa una cita y el ciudadano confirma en su portal.
2. En el recinto, el ciudadano ingresa el código de cita en «Registrar mi llegada», el día correspondiente. Se asigna un turno y aparece en la cola del funcionario.
3. «Consultar mi turno» muestra la información asociada al código, sin volver a registrar llegada.
4. El funcionario inicia y finaliza la atención. El fin de atención tiene su propia marca de tiempo.
5. El ciudadano registra su salida en el tótem. Se guarda por separado del fin de atención y se impide repetirla.

El código localiza una cita; no verifica por sí solo que la persona sea su titular. No se implementaron cámara, lectura física de cédula ni reconocimiento facial. Detectar la presencia de un rostro no equivale a verificar identidad. Para una futura demostración de escaneo/identidad primero se debe definir qué acredita, qué datos utiliza y cómo se manejan errores; no basta con agregar una librería.

## GEPOL y Registro Civil

- https://pdi-portal-vwjcdgy22a-uc.a.run.app/simuladores/gepol
- https://pdi-portal-vwjcdgy22a-uc.a.run.app/simuladores/registro-civil

Se abren desde «Consulta institucional» o desde un expediente, en otra pestaña, con el RUN precargado. También permiten ingresar RUN, nombre o pasaporte manualmente. Son rutas independientes del mismo servicio Cloud Run, con estilos propios; no son nuevos servidores ni sistemas oficiales. Sus datos vienen de la misma base de demostración.

Las páginas no solicitan contraseñas institucionales. Los datos de consulta requieren sesión de funcionario/administrador y se registran en la auditoría. Un ciudadano recibe rechazo de acceso a esas APIs.

La referencia GEPOL aportada por el usuario pertenece a un dominio `.com.br`: se tomó su estilo visual antiguo como referencia y se utilizó marca textual propia, sin atribuirlo al sistema chileno real. Registro Civil usa una composición propia en azul/rojo y mantiene aviso visible de simulación.

## Ficha de persona y atención sin cita

«Personas» busca por RUN o nombre. Cada ficha reúne contactos, enlaces a GEPOL/Registro Civil, documentos y todas las solicitudes (online y presenciales, activas y finalizadas). El nombre del solicitante en la bandeja o el expediente abre su ficha.

El funcionario puede registrar una persona nueva: nombre, correo, clave inicial acordada con ella y contacto opcional. Se asigna un RUN sintético y el rol siempre es ciudadano. No se envía un correo de activación ni un SMS; en este prototipo la persona usa ese correo/RUN y la clave acordada para ingresar.

Desde la ficha puede registrar una llegada sin cita y crear una solicitud presencial. Se impiden llegadas duplicadas y se indica usar el tótem si existe una cita para hoy. La llegada sin cita puede preceder a la creación del expediente; por eso la cola siempre enlaza a la persona y solo enlaza a un expediente cuando ya está asociado.

La copia digitalizada se incorpora al expediente indicando su procedencia y lo verificado. Después el funcionario registra «Aceptado» explícitamente. La carga por sí sola no acredita la identidad ni acepta el documento. Si falta un antecedente, el ciudadano puede entrar al mismo expediente desde el portal y adjuntarlo. El tótem actual registra códigos de cita: no entrega una fotocopia automática de una cédula.

## Documentos adicionales y errores de registro

«Solicitar otro documento» permite escoger un tipo del catálogo aún no solicitado y explicar su necesidad. Se agrega al expediente y se avisa al ciudadano dentro del portal. Un requisito adicional puede cancelarse con motivo; los archivos que ya tuviera quedan como versiones anteriores y el registro de la cancelación se conserva. No se permite cancelar los requisitos base del catálogo con esta acción.

Una decisión final ya no se revierte con el selector normal. «Reabrir expediente» exige un motivo y registra «Expediente reabierto» conservando la decisión anterior. Solo administración puede reabrir el estado «Cerrada».

«Corregir una anotación» permite rectificar un registro equivocado con motivo. Conserva texto, fecha, autor y motivo de rectificación; el original pasa al apartado contraído «Anotaciones rectificadas». El ciudadano ve la corrección y puede desplegar su motivo; el funcionario también conserva el texto original. Rectificar una anotación no cambia el estado del expediente ni deshace por sí solo una revisión documental. Las correcciones y reaperturas no se rectifican desde esta opción. No se borran registros de prueba automáticamente al desplegar.

## Reutilización y vigencia

La ficha ofrece una biblioteca lógica de documentos: los objetos permanecen privados y asociados a versiones de expedientes. «Usar documento existente» solo ofrece archivos de esa misma persona, aceptados, no sustituidos y sin vencimiento conocido. El tipo debe corresponder exactamente al requisito de destino.

La nueva solicitud crea una referencia a la versión del archivo (`source_document_id`) y conserva su propio estado «En revisión», sin copiar el funcionario ni la aceptación anterior. No duplica el objeto de Storage. Una vigencia desconocida se indica como pendiente de comprobación; no se inventa una duración universal. El funcionario puede registrar fecha de vencimiento con motivo antes del cierre. Un vencimiento conocido impide volver a reutilizar esa versión.

Este es el diseño de la PoC, no una afirmación sobre requisitos jurídicos o procedimientos actuales de organismos reales. En producción se necesitarían reglas por trámite, verificación de identidad, consentimiento/base de tratamiento, retención, activación de cuentas y controles de concurrencia más completos.
