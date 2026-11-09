---
title: Plantilla - Solicitud de Autorización de Intervención en Servidor
type: plantilla
status: vigente
tags: [cai, plantilla, autorizacion, servidor, direccion, relevamiento]
owner: Responsable técnico
updated: 2026-11-09
related:
  - "[[07.08 Relevamiento del Servidor del Centro]]"
  - "[[Plantilla - Inventario de Servidor]]"
  - "[[Plantilla - Informe de Relevamiento de Servidor]]"
  - "[[09.01 Manual de Dirección]]"
---

# Plantilla - Solicitud de Autorización de Intervención en Servidor

> [!info] Cómo usar esta plantilla
> 1. Copiar este documento a un archivo de trabajo fuera de la bóveda, o imprimirlo.
> 2. Completar **todos** los campos entre corchetes. No dejar ninguno vacío.
> 3. Revisar el alcance con el [[07.08 Relevamiento del Servidor del Centro]].
> 4. Firmar el solicitante y pedir la firma de Dirección **antes** de tocar el equipo.
> 5. Archivar el original firmado y entregar una copia al acompañante.
>
> **Sin firma de Dirección no se ejecuta la intervención.** Esta plantilla no reemplaza
> el procedimiento: lo autoriza.

---

## Datos de la solicitud

| Campo | Valor |
|---|---|
| **Centro** | [Nombre completo del centro] |
| **N.º de solicitud** | [AAAAMMDD-NN] |
| **Fecha de la solicitud** | [AAAA-MM-DD] |
| **Solicitante** | [Nombre y apellido] |
| **Cargo o rol** | [Responsable técnico / Administración Técnica / otro] |
| **Documento de identidad** | [C.I. / Pasaporte] |
| **Teléfono de contacto** | [Teléfono] |
| **Correo de contacto** | [Correo institucional] |
| **Equipo o servidor** | [Nombre, etiqueta de inventario o ubicación física] |
| **Marca, modelo y serie** | [Si se conocen; si no, "a relevar"] |
| **Ubicación física** | [Sala, rack, oficina] |
| **Ventana propuesta** | [AAAA-MM-DD], de [HH:MM] a [HH:MM] |
| **Duración estimada** | [X horas] |
| **Acompañante designado** | [Nombre y cargo] |

---

## Texto de la solicitud

```text
[Ciudad], [fecha]

Sra. Directora
[Nombre del centro]
Presente

Ref.: Solicitud de autorización para relevamiento técnico del servidor

De mi mayor consideración:

Por medio de la presente solicito autorización para realizar un relevamiento
técnico del servidor de la institución, identificado como [equipo / etiqueta /
ubicación], con el objetivo de conocer el hardware disponible, el software
instalado, la capacidad de almacenamiento, la configuración de red, los
respaldos existentes y las categorías de datos que aloja.

El relevamiento se realizará en la ventana indicada en la presente solicitud,
con la presencia de [nombre del acompañante], designado/a por Dirección.

Alcance y método

1. La intervención será no destructiva y de solo lectura. No se instalará
   software, no se modificará configuración, no se crearán ni eliminarán
   usuarios y no se cambiarán contraseñas.
2. No se copiarán datos personales, clínicos ni financieros. El mapa de datos
   se hará por categoría, cantidad y tamaño, sin leer el contenido.
3. No se accederá al contenido de notas clínicas, fichas de alumnos ni
   documentación sensible.
4. No se conectará el servidor a internet ni se sacará el equipo del centro.
5. Cada acción quedará registrada en una bitácora con hora, comando y resultado.
6. La evidencia (fotos de etiquetas, salidas de comandos y actas) se guardará
   en un medio cifrado y con un manifiesto de hashes.

Límites

No forman parte de esta autorización la reparación, actualización, reinstalación,
migración ni el borrado de datos. Cualquier hallazgo que requiera una acción
correctiva se informará y se someterá a una nueva autorización.

Riesgos y mitigación

El riesgo principal es interrumpir el servicio si el equipo está en producción.
Para mitigarlo, la intervención se hará en la ventana acordada, con comandos de
solo lectura y con criterios de aborto definidos en el procedimiento. Si se
detecta un riesgo para la disponibilidad o para los datos, la intervención se
detendrá y se informará de inmediato.

Entregables

1. Inventario de hardware, software, almacenamiento, red, cuentas y respaldos.
2. Mapa de datos por categoría y volumen, sin contenido personal.
3. Informe de relevamiento con hallazgos, riesgos y recomendaciones priorizadas.
4. Acta de inicio y acta de cierre firmadas por el solicitante y el acompañante.

Confidencialidad

La información relevada se tratará como confidencial. El informe no contendrá
datos personales de alumnos, familias ni profesionales. La evidencia quedará
bajo custodia del solicitante y del acompañante, y se archivarán o destruirán
según indique Dirección una vez aprobado el informe.

Sin otro particular, solicito la autorización correspondiente y quedo a
disposición para ampliar cualquier punto.

Atentamente,


[Firma]
[Nombre y apellido]
[Cargo]
[Documento de identidad]
```

---

## Autorización

| Rol | Nombre y apellido | Firma | Fecha |
|---|---|---|---|
| **Solicitante** | [Nombre] | | [AAAA-MM-DD] |
| **Autoriza Dirección** | [Nombre de la directora] | | [AAAA-MM-DD] |
| **Acompañante designado** | [Nombre] | | [AAAA-MM-DD] |

> [!warning] La autorización es por esta intervención
> No es un permiso permanente. Si cambia la fecha, el alcance o el equipo, se emite
> una solicitud nueva. La autorización verbal no se registra como autorización.

---

## Anexo A — Checklist de alcance

Marcar lo que **sí** se autoriza y dejar explícito lo que **no**:

| # | Actividad | Sí | No |
|---|---|---|---|
| 1 | Relevamiento físico exterior del equipo | ☐ | ☐ |
| 2 | Lectura de etiquetas, marca, modelo y número de serie | ☐ | ☐ |
| 3 | Consulta de CPU, memoria y discos | ☐ | ☐ |
| 4 | Consulta de sistema operativo, servicios y paquetes | ☐ | ☐ |
| 5 | Consulta de interfaces, rutas y puertos abiertos | ☐ | ☐ |
| 6 | Consulta de usuarios y privilegios, sin contraseñas | ☐ | ☐ |
| 7 | Consulta de tareas programadas y respaldos | ☐ | ☐ |
| 8 | Conteo y dimensionamiento de datos por categoría | ☐ | ☐ |
| 9 | Registro fotográfico de etiquetas y estado físico | ☐ | ☐ |
| 10 | Instalación o actualización de software | ☐ | ☐ |
| 11 | Copia de datos, bases o documentos | ☐ | ☐ |
| 12 | Lectura de contenido clínico o financiero | ☐ | ☐ |
| 13 | Cambio de configuración, usuarios o contraseñas | ☐ | ☐ |
| 14 | Retiro del equipo del centro | ☐ | ☐ |

---

## Anexo B — Declaración de confidencialidad del interviniente

```text
Declaro que:

1. Conozco y respetaré las reglas de manejo de datos del centro.
2. No copiaré, fotografiaré ni divulgaré datos personales, clínicos o
   financieros a los que acceda durante el relevamiento.
3. No usaré la información para fines distintos del relevamiento autorizado.
4. Guardaré la evidencia en el medio cifrado acordado y la entregaré al
   custodio designado.
5. Informaré de inmediato cualquier incidente o exposición accidental.

Nombre: [Nombre y apellido]
Documento: [C.I.]
Firma: ______________________________
Fecha: [AAAA-MM-DD]
```

---

## Documentos relacionados

- [[07.08 Relevamiento del Servidor del Centro]] — el procedimiento que esta solicitud autoriza
- [[Plantilla - Inventario de Servidor]] — dónde se vuelcan los datos relevados
- [[Plantilla - Informe de Relevamiento de Servidor]] — el entregable final
- [[09.01 Manual de Dirección]] — el rol que autoriza
