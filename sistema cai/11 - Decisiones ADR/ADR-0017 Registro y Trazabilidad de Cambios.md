---
title: ADR-0017 Registro y Trazabilidad de Cambios
type: adr
status: aceptado
tags: [cai, adr, gobernanza, trazabilidad, versionado, ia]
owner: Responsable técnico
updated: 2026-10-22
related:
  - "[[12.01 Política de Cambios y Trazabilidad]]"
  - "[[12.04 Versionado de la Documentación]]"
  - "[[05.07 Gobierno del Cambio]]"
  - "[[ADR-0004 Trunk-based con Tags SemVer]]"
---

# ADR-0017 — Registro y Trazabilidad de Cambios

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-10-22 |
| **Decide** | Responsable técnico |
| **Alcance** | Proceso de trabajo completo: documentación, código, configuración y agentes de IA |

---

## 1. Contexto

Al terminar la documentación del sistema CAI (95 documentos, ADR-0001 a ADR-0010)
se constató un problema que el propio plan asumía resuelto: **el proyecto
tenía reglas para versionar el código, pero la documentación —que es la fuente
de verdad— no estaba versionada en absoluto**.

Todo el diseño del proyecto (trunk-based, SemVer por paquete, expand–contract,
cuatro niveles de rollback, gates por fase) da por hecho que existe un
historial confiable. Ese historial cubría el código que aún no existe, y no
cubría los 95 documentos que ya definían el sistema.

**Restricciones:**
- Un solo desarrollador part-time: no hay un segundo revisor ni un equipo de
  calidad.
- El trabajo se realiza en buena parte con agentes de IA, que pueden modificar
  decenas de archivos en segundos sin dejar registro.
- El sistema manejará datos de menores: la trazabilidad no es comfort, es
  requisito.
- El centro opera en Paraguay: la normativa de protección de datos aplica.
- No hay infraestructura nueva: lo que se use debe correr en el servidor del
  centro o en la máquina del desarrollador, sin servicios que sostener.

**Qué sabemos:**
- Git ya está en la máquina y es la herramienta de versionado de facto del
  ecosistema.
- OpenCode (la herramienta con la que se trabaja) permite definir **permisos**
  por acción y recurso, con efectos `allow`, `ask` y `deny`, y permite instalar
  **plugins** que interceptan la ejecución de herramientas.
- Los hooks de `git` son el punto de control natural antes de un commit.

**Qué no sabemos:**
- Qué proporción del trabajo futuro será hecha por personas y qué proporción por
  IA. El mecanismo tiene que servir para ambos casos sin distinguirlos.
- Cuánto va a durar el proyecto: la documentación va a ser consultada durante
  años, mucho después de que quien la escribió deje de estar.

---

## 2. Decisión

**Versionamos la bóveda con Git y con tags documentales propios, registramos
todo cambio en un log de solo agregar con atribución explícita del modelo de
IA, y bloqueamos mecánicamente las operaciones que no se pueden permitir.**

**En detalle:**
- La bóveda entra al mismo repositorio que el código, y se versiona con
  `doc@vX.Y.Z`, donde `X` es cambio estructural, `Y` son documentos nuevos o
  decisiones aceptadas, y `Z` son correcciones.
- Todo cambio se registra en un log append-only
  (`12 - Registro de Cambios/12.02`) con: motivo, archivos afectados,
  severidad, verificación ejecutada y **modelo de IA exacto**
  (`proveedor/modelo#variante`).
- Las sesiones se registran aparte (`12.03`), para poder atribuir sin duplicar
  el historial.
- **Nada se borra.** Un documento que deja de servir se marca
  `deprecated`/`superseded` y se redirige; una entrada de registro no se edita
  nunca.
- El control de las reglas es **mecánico, no de disciplina**: permisos de
  OpenCode (`deny`/`ask`) para operaciones peligrosas, y un hook de
  `pre-commit` que bloquea el commit si no existe la entrada de registro.
- Las reglas de gobierno viven en `AGENTS.md` en la raíz del repositorio, de
  modo que viajan con el proyecto y son leídas por cualquier agente al entrar.

**Alternativa elegida porque:**
- El problema central no es "falta disciplina", sino "falta mecanismo": con un
  solo desarrollador y agentes de IA, una regla que depende de que alguien se
  acuerde se rompe el día que hay prisa.
- Git ya está disponible y no requiere operar ningún servicio nuevo.
- Los permisos y los hooks de OpenCode son configuración y scripts pequeños:
  no agregan dependencias ni procesos al servidor del centro.

---

## 3. Alternativas consideradas

### 3.1 Solo Git, sin log documental

| Aspecto | Detalle |
|---|---|
| **Descripción** | Versionar la bóveda con Git y nada más: el historial de commits es el registro |
| **Ventajas** | Cero trabajo adicional; el diff ya muestra qué cambió; menos documentos que mantener |
| **Desventajas** | El historial no dice **por qué**; no registra el modelo de IA; un commit puede tocar 40 archivos sin que se entienda el motivo; el motivo queda en el mensaje del commit, que es un campo de una línea |
| **Por qué se descartó** | La pregunta "¿por qué este documento dice esto?" es la que más se va a hacer, y Git no la responde. La auditoría de "quién cambió esto" exige un campo estructurado que el commit no tiene |

### 3.2 Log en un gestor de incidencias externo

| Aspecto | Detalle |
|---|---|
| **Descripción** | Registrar cada cambio como incidencia en GitHub (o equivalente), y dejar Git solo para el código |
| **Ventajas** | La bitácora es consultable y notificable; tiene responsable, estado y comentarios de serie |
| **Desventajas** | El centro no puede depender de internet para auditar su propia documentación; el registro queda fuera del control de versiones del proyecto; un corte de internet deja de poder auditar; el coste operativo de mantener un segundo sistema para un dev part-time |
| **Por qué se descartó** | El principio de continuidad del proyecto (servidor propio, sin dependencia de internet, ver [[07.01 Arquitectura del Servidor del Centro]]) choca de frente con esta opción |

### 3.3 Encabezado de historial dentro de cada documento

| Aspecto | Detalle |
|---|---|
| **Descripción** | Cada documento lleva su propia tabla "Registro de cambios" al final, como en la plantilla |
| **Ventajas** | El historial está donde se lee el documento; no hay archivo central que mantener |
| **Desventajas** | Con 100+ documentos, el historial está disperso; no hay vista global; la tabla se desactualiza y es el primero que se deja de llenar; **no registra el modelo de IA** de forma natural |
| **Por qué se descartó** | Es el mecanismo que la plantilla sugiere, y funciona para documentos individuales, pero no escala a un registro de proyecto. Se conserva la tabla por documento para cambios **locales**, y se añade el registro central para el proyecto |

### 3.4 Plugin que registra todo automáticamente

| Aspecto | Detalle |
|---|---|
| **Descripción** | Un plugin de OpenCode intercepta cada herramienta y escribe la entrada de registro sin intervención humana |
| **Ventajas** | No se puede olvidar; la atribución del modelo es exacta y automática; los archivos tocados se registran sin error |
| **Desventajas** | Depende de la API de plugins de OpenCode, que es **alpha** y puede cambiar; un plugin roto puede romper la sesión; no captura el **motivo**, que requiere juicio humano; no sabe qué es "un cambio" y qué es "una lectura" |
| **Por qué se descartó** | Como mecanismo **único**, no: no captura el motivo y ata el proyecto a una API alpha. Como **complemento**, sí: el plugin cubre la atribución técnica (modelo, archivos, hora) y deja el motivo en manos de la persona |

### 3.5 Un gestor de tareas o de tickets para el backlog y el registro

| Aspecto | Detalle |
|---|---|
| **Descripción** | El backlog y el registro de cambios viven en un gestor de incidencias |
| **Ventajas** | Vista de trabajo compartida; asignaciones y estados |
| **Desventajas** | Requiere internet y una cuenta; el plan ya decidió que el backlog vive en la bóveda ([[08.12 Backlog Maestro]]); duplicaría el estado en dos lugares |
| **Por qué se descartó** | Duplica el estado y agrega una dependencia operativa |

### 3.6 No registrar nada: confiar en el historial de commits

| Aspecto | Detalle |
|---|---|
| **Descripción** | El historial de commits ya es el registro; no hace falta nada más |
| **Ventajas** | Simplidad total; nada que mantener |
| **Desventajas** | No hay motivo estructurado; no hay atribución de IA; no hay control mecánico; un commit puede reversarse sin dejar constancia de por qué se hizo |
| **Por qué se descartó** | Es la opción que de hecho está implícitamente en marcha hoy. Funciona hasta el primer incidente |

---

## 4. Consecuencias

### 4.1 Positivas

- La bóveda pasa a ser **verificablemente** la fuente de verdad: cada versión
  tiene un tag, cada cambio tiene una entrada, cada sesión tiene un responsable.
- Las tres preguntas de auditoría —**qué** cambió, **por qué**, **quién**— tienen
  respuesta verificable.
- Los controles son **mecánicos**: el hook bloquea el commit sin registro, los
  permisos bloquean el borrado y el push a `main`. No dependen de la memoria.
- El modelo de IA queda atribuido, lo que permite comparar qué cambió cuando
  se usaron modelos distintos.
- No se agrega **ninguna** dependencia operativa al servidor del centro: todo
  corre en la máquina de desarrollo con herramientas ya presentes.
- El patrón "no se borra, se retira" queda establecido **antes** de que haya
  código que revertir, cuando todavía es barato.

### 4.2 Negativas (lo que aceptamos)

- **Costo de escritura.** Todo cambio, incluso un typo, genera una entrada. Es
  deliberado: el objetivo es que el registro no tenga huecos. Pero en la
  práctica hay que aceptar que el proceso es más lento que "editar y ya".
- **Un solo archivo más que mantener.** La bóveda crece con la carpeta `12` y
  con la carpeta de proceso `05`. Un proyecto con 1 dev part-time no debería
  tener 15 documentos de proceso; se limita a 4 documentos nuevos y se acepta el
  resto.
- **Fricción con la IA.** El hook puede bloquear un commit y obligar a un ciclo
  extra. Es el comportamiento buscado, pero se va a sentir como un obstáculo
  hasta que se vuelva automático.
- **El registro depende de que alguien lo llene.** El hook garantiza que
  *exista* una entrada; no garantiza que el **motivo** sea bueno. La calidad
  del registro depende de la revisión humana.
- **El plugin depende de una API alpha.** Si OpenCode cambia la API de
  plugins, la atribución automática se rompe. Por eso el registro también
  acepta entrada manual: la atribución no depende del plugin.
- **La bóveda y el código comparten repositorio.** Los commits de documentación
  y de código se mezclan en el historial. Se acepta: la granularidad del tag
  (`doc@` frente a `cai/paquete@`) permite separarlos.
- **No hay repositorio remoto todavía.** La trazabilidad existe localmente. La
  copia en GitHub privado (decisión D1) sigue pendiente, y hasta que exista,
  el historial solo vive en esta máquina.

### 4.3 Neutras / equilibradas

- La convención `doc@vX.Y.Z` convive con SemVer por paquete y con
  `sistema@vYYYY.MM.P`. Tres esquemas de versión, pero cada uno con un alcance
  distinto y sin ambigüedad.
- Los tags documentales se crean por **hito**, no por cambio. Si se crean
  demasiados, se vuelve ilegible; la regla de §5 lo evita.

---

## 5. Verificación

```text
☐ La bóveda está en un repositorio Git y existe un tag doc@vX.Y.Z del último hito
☐ El hook de pre-commit bloquea un commit cuando falta la entrada de registro
☐ El hook de pre-commit exige justificación cuando el commit elimina archivos
☐ opencode.jsonc deniega: rm, git clean, git push a main, git push --force
☐ opencode.jsonc pide confirmación antes de tocar 11 - Decisiones ADR/
☐ AGENTS.md existe en la raíz y enumera el orden de lectura obligatorio
☐ bin/validate-vault.py se ejecuta y devuelve 0 errores
☐ Existe una entrada en 12.02 por cada commit desde la entrada en vigor
☐ Existe una entrada en 12.03 por cada sesión, con proveedor/modelo#variante
☐ Un cambio de ADR aceptado se registra como decisión nueva, no como edición
```

### 5.1 Señales de alarma

| Señal | Qué significa |
|---|---|
| El hook se desactiva "para ir más rápido" | La primera barrera cayó; el registro deja de ser confiable |
| Entradas de registro con el motivo vacío o genérico | La trazabilidad es formal, no real |
| El índice de la bóveda queda viejo | El contrato de navegación se rompió |
| Sesiones que nunca se cierran | El control de concurrencia no funciona |

---

## 6. Reversibilidad

| Aspecto | Detalle |
|---|---|
| **¿Se puede revertir?** | Sí, y en dos niveles distintos |
| **Cómo** | **Nivel 1**: borrar la carpeta `12`, el archivo `AGENTS.md`, `opencode.jsonc` y `.opencode/`, y revertir los commits correspondientes con `git revert`. **Nivel 2**: restaurar la bóveda al tag `doc@v0.1.0` con `git checkout doc@v0.1.0 -- "sistema cai/"`. La decisión de no borrar los documentos de proceso se revierte por completo, porque nada se borró: se deja de usar |
| **Costo de revertir** | Bajo. Son documentos y configuración, no migraciones. El coste real es perder el control, no recuperarlo |
| **Señal de que hay que revertir** | El proceso se aplica de forma mecánica pero no aporta valor: se registra por obligación y no se consulta nunca. Si en dos revisiones de fase nadie mira `12.02`, la política es burocracia y hay que simplificar |

---

## 7. Referencias

- [[12.01 Política de Cambios y Trazabilidad]] — la política que implementa esta decisión
- [[12.02 Registro de Cambios]] — el registro
- [[12.03 Bitácora de Sesiones con IA]] — la atribución por sesión y modelo
- [[12.04 Versionado de la Documentación]] — el esquema `doc@vX.Y.Z`
- [[05.07 Gobierno del Cambio]] — las reglas de trabajo
- [[ADR-0004 Trunk-based con Tags SemVer]] — la decisión de versionado del código
- [[ADR-0009 Sin Redis en el MVP]] — la norma de no agregar servicios
- [[00.01 Convenciones de la Vault]] — convenciones de la bóveda
- [[08.12 Backlog Maestro]] — dónde vive el trabajo pendiente
