---
title: ADR-0018 Verificación de Trazabilidad en un Punto
type: adr
status: aceptado
tags: [cai, adr, gobernanza, trazabilidad, herramientas, calidad]
owner: Responsable técnico
updated: 2026-10-22
related:
  - "[[ADR-0017 Registro y Trazabilidad de Cambios]]"
  - "[[05.08 Revision de Calidad de las Herramientas de Gobernanza]]"
  - "[[05.09 Herramientas de Gobernanza]]"
  - "[[12.01 Política de Cambios y Trazabilidad]]"
  - "[[05.07 Gobierno del Cambio]]"
---

# ADR-0018 — Verificación de Trazabilidad en un Punto

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-10-22 |
| **Decide** | Responsable técnico — aprobado al autorizar la tanda T1 el 2026-10-22 |
| **Alcance** | Herramientas de gobernanza del repositorio de documentación |

---

## 1. Contexto

La política de trazabilidad se implementó en tres lugares distintos:

| Motor | Archivo | Qué verifica |
|---|---|---|
| Hook de Git | `bin/hooks/pre-commit` | Cita de `REG`, existencia del ID, borrados (solo aviso) |
| Plugin de OpenCode | `.opencode/plugins/cai-log.ts` | Cita de `REG`, existencia, borrados (bloqueo), cierre de sesión |
| Registrador | `bin/cai-log.py` | Formato del ID, motivo mínimo, rastreo obligatorio, sesión existente |

Los tres se escribieron con la misma intención y **hoy no coinciden**:
el hook advierte lo que el plugin bloquea; el plugin busca el ID como subcadena y
el hook como encabezado; el correlativo de sesión se calcula distinto en cada
uno. Además, el hook valida el mensaje del commit anterior y el plugin
reemplaza el bloque de sesiones al escribir (ver
[[05.08 Revision de Calidad de las Herramientas de Gobernanza]], HC-01 a HC-03).

**Restricciones:**
- Un solo desarrollador part-time: cada regla nueva no puede exigir tres cambios.
- El control debe ser mecánico y local: sin servicios, sin internet
  ([[ADR-0017 Registro y Trazabilidad de Cambios]] §1).
- Los commits de personas y de agentes deben pasar por el mismo control.
- El registro es de solo agregar: ninguna herramienta puede reescribirlo.

**Qué sabemos:**
- Git expone puntos de control estables: `pre-commit` no recibe el mensaje;
  `commit-msg` lo recibe como primer argumento.
- Un comando local puede leer el mensaje y el índice, y devolver un código.
- El plugin depende de una API alpha y no ve los commits hechos fuera del agente.

**Qué no sabemos:**
- Cuánto trabajo futuro hará el agente y cuánto una persona. El mecanismo debe
  servir a ambos sin distinguirlos.
- Si la API de plugins de OpenCode seguirá existiendo con la misma forma.

---

## 2. Decisión

**La verificación de la trazabilidad vive en un único comando,
`bin/cai-log.py verificar`, invocado por los hooks nativos de Git; el plugin
observa la sesión y bloquea comandos destructivos, pero no verifica la política
ni escribe en la bóveda durante la validación.**

**En detalle:**
- `pre-commit` valida la forma de la bóveda cuando el commit la toca y falla
  cerrado si falta el validador.
- `commit-msg` recibe el archivo del mensaje, invoca `verificar` y bloquea si el
  comando devuelve `1`.
- `verificar` es la única implementación de las reglas de trazabilidad: cita de
  `REG`, existencia como encabezado y justificación de borrados.
- El plugin deja de interpretar comandos y de escribir entradas: registra
  atribución en `.cai/sessions/` y no escribe en la bóveda.
- Toda escritura en el registro es una sola operación atómica, insertada
  después del marcador `START` y sin tocar el texto anterior.

**Alternativa elegida porque:**
- Un solo lugar para una sola regla elimina el desvío actual (HC-03).
- Los hooks de Git son el punto que ningún commit puede evitar, sea de persona
  o de agente (GE-12).
- `commit-msg` es el único punto donde el mensaje real existe (HC-02).
- No agrega dependencias: usa el intérprete de Python que ya ejecuta el
  registrador.

---

## 3. Alternativas consideradas

### 3.1 Mantener las tres implementaciones

| Aspecto | Detalle |
|---|---|
| **Descripción** | Corregir cada motor por separado y dejar la política triplicada |
| **Ventajas** | Cero refactor; cada herramienta evoluciona sola |
| **Desventajas** | Cada regla exige tres cambios coordinados; el desvío ya ocurrió; las pruebas se triplican |
| **Por qué se descartó** | El costo no es el primer cambio, es el quinto: cuando las reglas se separen otra vez, nadie va a notarlo hasta que un commit indebido pase |

### 3.2 Verificar solo en el plugin

| Aspecto | Detalle |
|---|---|
| **Descripción** | El plugin es el único verificador y bloquea el commit desde el agente |
| **Ventajas** | Ve modelo, sesión y archivos; no necesita hooks |
| **Desventajas** | No cubre commits hechos en la terminal; depende de una API alpha; ya demostró falsos positivos al interpretar texto de comandos |
| **Por qué se descartó** | El control tiene que valer también para el humano que commitea sin el agente ([[ADR-0017 Registro y Trazabilidad de Cambios]] §1) |

### 3.3 Verificar solo con hooks, sin comando

| Aspecto | Detalle |
|---|---|
| **Descripción** | Dos scripts de shell (uno por hook) con toda la lógica |
| **Ventajas** | Menos piezas; no hay dependencia de Python |
| **Desventajas** | Repite el parseo en shell; las reglas de formato y de tabla son frágiles; no se puede probar con la misma facilidad |
| **Por qué se descartó** | Cambiar el motor de verificación a shell cambia un problema de diseño por un problema de lenguaje |

### 3.4 Adoptar un framework de hooks

| Aspecto | Detalle |
|---|---|
| **Descripción** | Usar `pre-commit` (Python) o `lefthook` como orquestador |
| **Ventajas** | Ecosistema probado; configuración declarativa |
| **Desventajas** | Una dependencia nueva y un archivo de configuración más para un solo repositorio con dos hooks |
| **Por qué se descartó** | GE-11: menos piezas, mejor. Los dos hooks caben en 30 líneas |

### 3.5 Verificar solo en integración continua

| Aspecto | Detalle |
|---|---|
| **Descripción** | Dejar el control al CI y no bloquear localmente |
| **Ventajas** | Un solo punto; no hay hooks que instalar |
| **Desventajas** | El error llega después del commit; todavía no hay remoto; el CI de este repositorio no ejecuta el validador |
| **Por qué se descartó** | El objetivo es impedir el commit indebido, no detectarlo después (GC-01) |

---

## 4. Consecuencias

### 4.1 Positivas

- Una regla nueva se implementa una vez y se prueba una vez.
- El commit de una persona y el de un agente pasan por la misma verificación.
- El mensaje validado es el del commit en curso, no el anterior.
- El plugin deja de tener poder de escritura sobre el histórico: se elimina la
  vía por la que se perdieron entradas el 2026-10-22.
- Las escrituras atómicas impedirán el estado parcial “entrada sin fila de
  índice” (T2).

### 4.2 Negativas (lo que aceptamos)

- **Más pasos en el commit.** `verificar` se ejecuta una vez por commit y agrega
  décimas de segundo. Se acepta a cambio de un control real.
- **El plugin pierde autonomía.** Ya no puede cerrar la sesión solo; el cierre
  vuelve a ser explícito o queda a cargo del agente con `cai-log.py`.
  Es un costo deliberado: el plugin no puede ser juez y parte.
- **Una dependencia interna más.** `commit-msg` depende de Python 3 y de la
  ruta relativa al repositorio. Si el intérprete no existe, el hook falla
  cerrado y bloquea; es el comportamiento buscado.
- **Migración de hábitos.** Hay que registrar el cambio (`REG`) antes de
  commitear, o el bloqueo explicará qué falta.

### 4.3 Neutras / equilibradas

- El plugin sigue siendo útil para recordar las reglas, atribuir el modelo y
  frenar comandos destructivos; deja de ser el árbitro de la trazabilidad.
- `opencode.jsonc` conserva los permisos, que son una segunda barrera
  independiente del hook, no una copia de sus reglas.

---

## 5. Verificación

Implementado en T1 el 2026-10-22. La matriz completa y la escritura atómica
pertenecen a T2–T4 ([[05.08 Revision de Calidad de las Herramientas de Gobernanza]] §6).

```text
[x] Un commit con REG válido pasa
[x] Un commit sin REG se bloquea en commit-msg
[x] Un commit con REG inexistente se bloquea y nombra el ID faltante
[x] Un commit que elimina un archivo sin justificación se bloquea
[x] El mensaje validado es el del commit en curso (no el anterior)
[x] Una inserción sobre 3 entradas deja las 3 intactas y agrega 1
[x] Un comando que solo menciona `git commit` no escribe en la bóveda
[x] Las reglas de la política existen en un solo archivo
[ ] La matriz T-01…T-22 de 05.09 §9 pasa completa (T2–T4)
```

### 5.1 Señales de alarma

| Señal | Qué significa |
|---|---|
| Una regla nueva se implementa en dos archivos | El punto único se rompió |
| El plugin vuelve a escribir durante una validación | Se reintrodujo HC-04 |
| Un commit sin REG pasa | El hook no está instalado o se usa `--no-verify` |
| El registro pierde entradas | Se reintrodujo una escritura destructiva |

---

## 6. Reversibilidad

| Aspecto | Detalle |
|---|---|
| **¿Se puede revertir?** | Sí |
| **Cómo** | Restaurar los tres motores desde el commit anterior a la implementación; el comando `verificar` queda como herramienta de diagnóstico sin invocación desde los hooks |
| **Costo de revertir** | Bajo: son scripts y hooks, no datos. Las entradas escritas durante la vigencia no se tocan |
| **Señal de que hay que revertir** | `verificar` bloquea commits legítimos de forma repetida y la causa no se corrige en una sesión; o el costo de mantener el comando supera el de mantener los hooks separados |

---

## 7. Referencias

- [[05.08 Revision de Calidad de las Herramientas de Gobernanza]] — diagnóstico que origina la decisión
- [[05.09 Herramientas de Gobernanza]] — contrato y matriz de pruebas
- [[ADR-0017 Registro y Trazabilidad de Cambios]] — decisión vigente sobre registro y atribución
- [[12.01 Política de Cambios y Trazabilidad]] — severidad y aprobación
- [[05.07 Gobierno del Cambio]] — GC-01, GC-06, GC-07, GE-12
- [[08.12 Backlog Maestro]] — ítems de implementación
- [[00.01 Convenciones de la Vault]] — formato de ADR
