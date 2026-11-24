# Flujo de atención y ventanas de simulación

## Roles y prioridad

Ciudadano: ingresa una solicitud, adjunta documentos, corrige antecedentes y solicita coordinación de una cita. Funcionario o administrador: revisa los documentos, toma decisiones, coordina la fecha/hora y atiende presencialmente.

La misma persona funcionaria puede atender ambos canales. La prioridad del prototipo es: atención presencial ya iniciada, luego personas con llegada registrada en orden de antigüedad, después expedientes online. La bandeja muestra esa prioridad y botones para iniciar/finalizar atención. Las acciones de expediente distinguen revisar documentos, esperar antecedentes del ciudadano, coordinar cita, atención programada y resolver expediente. Una cita terminada deja de tratarse como una atención futura.

El panel se actualiza cada cinco segundos mientras está en bandeja/agenda. Las operaciones del tótem en otra pestaña del mismo navegador notifican además al portal mediante un evento de almacenamiento local. No es una integración con un sistema físico real ni una cola productiva distribuida.

## Documentos y recomendación IA

Los documentos se presentan contraídos. «Por revisar» incluye documentos vigentes sin decisión definitiva; «Todos» incluye también aceptados, observados y versiones sustituidas. El funcionario puede expandir uno o todos y guardar cada revisión por separado.

La IA puede **proponer aceptar**, **proponer rechazar** o **pedir criterio al funcionario**. Su resultado se guarda aparte y nunca modifica el estado documental ni el expediente. En ausencia de IA real no se inventa una recomendación. El trazo de color corresponde al estado humano: revisión azul, aceptación verde, rechazo rojo y faltantes amarillo. El funcionario también decide el resultado final del expediente.

La carga por el funcionario aparece como «Incorporar documento recibido por correo». Es una acción manual explícita con procedencia obligatoria; el portal no lee correos automáticamente. Se conserva la versión anterior y la procedencia del archivo.

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
