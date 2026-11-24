# Flujo vigente de la PoC · 24 de noviembre de 2026

## Ciudadano y reservas

El ciudadano crea solicitudes, adjunta/corrige documentos y reserva directamente en «Mis citas». Puede asociar una solicitud abierta o pedir atención general. Escoge un bloque libre de treinta minutos y la cita queda **Confirmada** en la misma operación. No hay solicitud de coordinación ni confirmación posterior.

El horario configurado para la demostración es lunes a viernes, 09:00–16:00, con último bloque a las 15:30 y hasta noventa días de anticipación. No es una afirmación sobre horarios oficiales ni incluye feriados. Se impiden bloques ocupados, pasados, citas duplicadas por expediente y más de una cita activa por persona/día. La reserva se serializa en el servidor para evitar dos confirmaciones del mismo bloque.

El funcionario no programa nuevas citas desde este flujo. Su botón y ruta anterior se retiraron; la ruta devuelve indicación de reservar desde el portal ciudadano. Las propuestas antiguas pendientes se migraron a Confirmada. Los códigos nuevos son numéricos tras `CITA-`; los códigos alfanuméricos anteriores se conservan como alias y se muestran con su nuevo código numérico.

## Citas previstas y fila real

«Fila presencial» aparece primero en el menú y su contador solo incluye personas con llegada registrada. La misma página muestra por separado las citas previstas para hoy: una cita confirmada aparece como **No ha llegado** hasta pasar por el tótem. Tener una cita no equivale a estar en la fila ni habilita iniciar atención antes de llegar.

Las llegadas están ordenadas por antigüedad, con posibilidad de llamar fuera de orden si alguien no responde. «Llamar e iniciar» abre la ficha y anuncia turno, nombre y módulo en el tótem. Cada funcionario solo puede tener una atención activa, controlado en servidor e índice de base de datos. Otro funcionario no puede tomarla o finalizarla. El módulo es estable por cuenta (por ejemplo, Javier usa Módulo 2).

La bandeja online permanece separada de los trámites presenciales y muestra acciones del funcionario, no solo el estado ciudadano. Los contadores se actualizan cada cinco segundos. El tablero del tótem se actualiza cada tres segundos y las citas previstas cada diez.

## Tótem

URL: https://pdi-portal-vwjcdgy22a-uc.a.run.app/totem

Bienvenida → «¿Tienes cita?»:

- **Sí:** solo pide los números del código. `CITA-` es texto fijo y el teclado es numérico convencional. La cita debe estar confirmada y corresponder al día actual. Si ya llegó, muestra su turno existente.
- **No:** prepara una recepción provisional sin pedir RUN. La persona carga una copia del documento y se captura una foto; el funcionario debe vincular esa recepción a una persona al atenderla.

En ambos casos se presenta el lector de documento y una carga PDF/JPG/PNG (hasta 5 MB) para este computador. El lector físico/OCR no está conectado. Después se solicita permiso de cámara y un único rostro visible durante cinco segundos. El contador reinicia si se pierde o hay más de un rostro. No hay comparación de identidad ni prueba de vida; el funcionario contrasta el documento y la persona.

Se guardan copias privadas, legibles solo por funcionarios. El token de recepción vence a los quince minutos y se consume al completar el ingreso. El tótem muestra el turno y los llamados, sin exponer RUN, correo, documentos ni fotos en su tablero. Se retiró «Registrar salida»; las APIs antiguas permanecen por compatibilidad.

## Recepción provisional y ficha personal

Una recepción sin cita entra a la fila como Visitante sin cita. Al iniciarla se abre su copia/foto y un formulario para buscar una persona por nombre/RUN, o registrar una nueva. Solo el funcionario que la atiende puede vincularla, indicando qué contrastó. No puede vincularse a una persona que ya tenga otra llegada activa.

La ficha reúne contactos, consultas institucionales, capturas, documentos y todas las solicitudes. Los documentos muestran tres elementos; «Ver más» despliega el resto y el botón cambia a **Ver menos al final del último documento**. Cada folio de procedencia enlaza al expediente.

«Crear solicitud presencial» no exige descripción. El funcionario puede incorporar una copia indicando procedencia presencial/correo o usar la identificación capturada en el tótem. Cada incorporación queda pendiente hasta que registre su decisión explícitamente. El ciudadano puede completar después los antecedentes desde su portal. No hay lectura automática de correos ni envío de SMS.

## Requisitos, resolución y certificado

Los requisitos del trámite aparecen primero, contraídos y ordenados con pendientes delante. Una línea gris separa los documentos adicionales solicitados por el funcionario. Un adicional activo también se exige hasta que se acepte o se cancele con motivo. Las versiones anteriores se conservan separadas.

Solo puede resolverse favorablemente cuando todos los requisitos activos están aceptados. No basta con estar en revisión ni rechazados. La observación es obligatoria al pedir antecedentes, y opcional al resolver. Una solicitud **Resuelta** ofrece un PDF básico con folio, persona y trámite, identificado como prototipo sin validez oficial. La descarga exige permiso sobre ese expediente y vuelve a bloquearse si se deshace la resolución.

## Historial reversible

El lápiz corrige título/nota y permite seleccionar explícitamente una corrección de estado. La papelera ahora **deshace** la acción, en lugar de limitarse a ocultar una anotación:

- Las nuevas mutaciones guardan antes/después de expediente, documentos, requisitos y citas asociadas.
- Deshacer una aceptación devuelve estado, observación y metadatos de revisión anteriores.
- Deshacer una incorporación recupera la versión activa anterior; el nuevo archivo permanece archivado, no se borra del almacenamiento.
- Deshacer rechazo/resolución restaura el estado previo, por lo que la línea temporal deja de presentarse como finalizada.
- Se conserva original, motivo y autor en auditoría, y se retiran avisos de la acción deshecha.
- Se deshace en orden inverso para no pisar cambios posteriores. Una cita con atención iniciada no puede restaurarse desde la papelera; la sesión se gestiona desde su atención. Solo administración puede deshacer un cierre.

**Límite de los registros antiguos:** antes no existían instantáneas completas. Se permite reconstruir revisiones documentales identificables y transiciones de estado con historial suficiente. Si no se puede determinar el estado anterior con seguridad, se rechaza el deshacer y se indica usar corrección explícita; no se inventan metadatos históricos ni se borran datos para aparentar una restauración.

## IA y consultas institucionales

La propuesta documental y el chat ciudadano se señalan **En desarrollo** mientras no hay servicio conectado. El chat es un botón movible con panel y entrada deshabilitada. La revisión documental conserva su adaptador; solo el funcionario cambia el estado del documento. Puntos de integración en `integrar-ia.md`.

GEPOL y Registro Civil se abren en otra ventana, con RUN precargado, desde ficha/expediente o consulta institucional. Son simuladores propios, con datos del mismo laboratorio; no sistemas oficiales. GEPOL muestra antecedentes ficticios separados de identidad. Fuentes y límites de las identidades GTA en `personajes-gta.md`.

Rutas: `/simuladores/gepol`, `/simuladores/registro-civil`. Se requiere sesión de funcionario para consultar sus datos. La cuenta determina el rol; ningún dato del navegador otorga permisos de funcionario.
