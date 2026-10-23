# AGENTS.md — Reglas obligatorias del proyecto CAI

> **Este archivo es la puerta de entrada. Cualquier agente (humano o IA) que
> trabaje en este repositorio lo lee ANTES de tocar nada.**
>
> No es una sugerencia ni una guía de estilo. Es el contrato de trabajo.

---

## 0. La regla cero

**Antes de modificar un solo archivo, lee esto:**

| # | Documento | Qué te da |
|---|---|---|
| 1 | `AGENTS.md` (este archivo) | Las reglas no negociables |
| 2 | `sistema cai/12 - Registro de Cambios/12.01 Política de Cambios y Trazabilidad.md` | Qué se puede cambiar, quién lo autoriza, cómo se registra y cómo se revierte |
| 3 | `sistema cai/12 - Registro de Cambios/12.03 Bitácora de Sesiones con IA.md` | Si hay otra sesión en curso sobre los mismos archivos |
| 4 | El documento objetivo **y** los que declara en `related:` | El contexto de lo que vas a tocar |
| 5 | `sistema cai/11 - Decisiones ADR/Índice de ADRs.md` → los ADR que apliquen | Las decisiones ya tomadas, para no repetirlas ni contradecirlas |

> **Si un agente puede actuar sin leer estos cinco puntos, algo anda mal.**
> La existencia de este archivo en la raíz es justamente para que no se pueda
> saltar el punto 2.

---

## 1. Lo que NUNCA se hace

| # | Prohibido | Por qué |
|---|---|---|
| 1 | **Borrar** un archivo, una carpeta, un ADR o una entrada de registro | El histórico es el activo. Se **retira** (`deprecated` / `superseded`) y se redirige. Ver §6 de `12.01` |
| 2 | **Editar un ADR aceptado** | Un ADR se sustituye por otro que lo referencia. Ver §4 de `Índice de ADRs` |
| 3 | **Cerrar un cambio sin entrada de registro** | El hook de commit lo bloquea. Ver §5 |
| 4 | **Introducir datos reales** de alumnos, familias o profesionales | Se usan datos ficticios. El repositorio es el lugar con menos control de acceso |
| 5 | **Escribir credenciales** (`.env`, claves, tokens, `.pem`) | Un secreto en Git es un secreto filtrado para siempre |
| 6 | **Hacer `push` a `main`**, forzar pushes o reescribir historia publicada | `main` siempre verde; los tags deben seguir apuntando a lo que dicen apuntar |
| 7 | **Tocar lo que no se pidió** (mejoras oportunistas) | El cambio no revisado es el que se escapa del control. Ver `GC-11` en `05.07` |
| 8 | **Romper una frontera entre paquetes** | El aislamiento lo impone la herramienta (Deptrac), no la disciplina |
| 9 | **Reescribir entradas de registro** ya escritas | El registro es de solo agregar. Las correcciones se **agregan** |
| 10 | **Avanzar de fase sin el gate firmado** | El gate de `08 - Plan de Trabajo` define qué se puede empezar |
| 11 | **Que la IA ejecute `git push`** | El `push` lo hace el operador manualmente; la IA avisa cuando hay commits locales pendientes de publicar |

> [!tip] Evolucionar, no romper
> **Prefiere hacer cambios incrementales y compatibles hacia atrás.** Añade antes que
> sustituyas. Si algo va a desaparecer, márcalo `@deprecated` y convive al menos
> **2 versiones menores** antes de retirarlo en `MAJOR`. Todo cambio con ruptura
> necesita [[06.09 Guía de Actualización]].

---

## 1.1 Comandos rápidos

```bash
# Registrar un cambio
bin/cai-log.py cambio --tipo edición --severidad N2 \
  --motivo "..." --archivos "ruta1.md,ruta2.md" \
  --rastreo "ADR-0001" --verificacion "bin/validate-vault.py -> 0 errores" \
  --autor "Cesar Benitez" --modelo "opencode/big-pickle#default"

# Registrar/cerrar sesión
bin/cai-log.py sesion --operador "Cesar Benitez" \
  --modelo "opencode/big-pickle#default" --agente build \
  --objetivo "..." --area "12 - Registro de Cambios" --resultado completado

# Validar la bóveda
bin/validate-vault.py
```

---

## 2. Lo que SIEMPRE se hace

| # | Obligatorio | Cómo se cumple |
|---|---|---|
| 1 | **Declarar el alcance** antes de empezar: qué archivos exactos se van a tocar | Queda en la entrada `REG-…` |
| 2 | **Clasificar la severidad** del cambio (N1 a N4) | N3 y N4 requieren ADR o aprobación previa |
| 3 | **Citar el origen** del cambio con un ID: `RF-nnn`, `RN-nnn`, `RNF-nnn`, `ADR-nnnn`, `P-nn`, `S-nn` | Campo "Rastreo" de la entrada |
| 4 | **Verificar** antes de cerrar, con un comando y su resultado | `bin/validate-vault.py`, `python3 -m unittest discover -s bin/tests`; Deptrac, en el repositorio de producto |
| 5 | **Registrar** el cambio en `12 - Registro de Cambios/12.02 Registro de Cambios.md` | Entrada `REG-AAAA-NNN` |
| 6 | **Registrar** la sesión en `12 - Registro de Cambios/12.03 Bitácora de Sesiones con IA.md`, con el **modelo exacto** | `proveedor/modelo#variante` |
| 7 | **Actualizar los índices** afectados en el mismo commit | `Inicio.md`, `Índice de ADRs.md`, la sección 3 de `12.02` |
| 8 | **Anotar lo pendiente** | Campo "Pendiente" de la entrada |
| 9 | **Commit con mensaje convencional** | Ver `05.02 Commits, Ramas y Versionado SemVer` |
| 10 | **Avisar cuando hay commits locales pendientes de publicar** | El operador ejecuta el `push`; la IA no lo hace |

---

## 3. El modelo de IA se registra

Si hubo IA en el cambio, el identificador exacto del modelo va en la bitácora:

```
opencode/big-pickle#default
anthropic/claude-sonnet-4-5
```

**No** vale "Big Pickle", "Claude", "un modelo", ni "el modelo por defecto".
Sin el identificador exacto, la atribución se pierde para siempre.

---

## 4. Severidad: qué puedo hacer solo

| Nivel | Qué es | Puedo hacerlo sin preguntar |
|---|---|---|
| **N1** | Editorial: formato, typo, enlace roto, `updated` | Sí |
| **N2** | Contenido acotado: reescribir una sección, agregar un requisito no bloqueante | Sí |
| **N3** | Decisión o comportamiento: ADR, migración, contrato entre paquetes, permiso | **No** — necesita ADR o aprobación |
| **N4** | Irreversible o sensible: claves, firewall, backups, datos reales | **No** — necesita aprobación explícita del responsable técnico |

---

## 5. Antes de hacer commit

El hook `commit-msg` **bloquea** el commit si el mensaje no cita una entrada
`REG` que exista en 12.02, o si elimina archivos sin justificar. `pre-commit`
valida la bóveda cuando el commit la toca. Para que pase:

```text
☐ La entrada REG-… de este cambio ya está escrita en 12.02
☐ La sección 3 (índice) de 12.02 la referencia
☐ La sesión está registrada en 12.03 con el modelo exacto
☐ La verificación pasó y su comando está en la entrada
☐ Si el commit elimina archivos: la entrada dice por qué y lo aprueba alguien
☐ Los índices que correspondan están actualizados
☐ El mensaje del commit es convencional y cita los IDs
```

Para comprobar el mensaje antes de commitear:

```bash
bin/cai-log.py verificar --mensaje .git/COMMIT_EDITMSG
```

### 5.1 Cómo se escribe el registro rápido

```bash
# Entrada de cambio
bin/cai-log.py cambio \
  --tipo "edición" \
  --severidad N2 \
  --motivo "Corregir el wikilink roto del ADR-0006 en 03.05" \
  --archivos "sistema cai/03 - Modelo de Datos/03.05 Planes de Atención y Notas Clínicas.md" \
  --rastreo "ADR-0006" \
  --verificacion "bin/validate-vault.py -> 0 errores"

# Cierre de sesión
bin/cai-log.py sesion \
  --operador "Cesar Benitez" \
  --modelo "opencode/big-pickle" \
  --variante "default" \
  --agente "build" \
  --objetivo "Sanear los enlaces de 03 - Modelo de Datos" \
  --area "03 - Modelo de Datos" \
  --resultado completado
```

---

## 6. En vez de borrar, se retira

```markdown
---
status: superseded   # o: deprecated
---

> [!warning] Documento sustituido
> Este documento fue reemplazado por [[Otro Documento]] el 2026-10-22.
> Motivo: <razón>. No se borra: forma parte del histórico.
```

Después: actualizar todos los wikilinks que apuntaban a él, y registrar el
cambio con `--tipo deprecación`.

---

## 7. Comandos del proyecto

| Comando | Qué hace |
|---|---|
| `bin/validate-vault.py` | Valida la bóveda: wikilinks, frontmatter, tablas, caracteres. Devuelve código de salida 1 si hay errores |
| `bin/cai-log.py --help` | Registra un cambio o una sesión en el log |
| `bin/cai-log.py verificar --mensaje ARCHIVO` | Comprueba un mensaje de commit contra el registro (lo usa el hook `commit-msg`) |
| `python3 -m unittest discover -s bin/tests` | Ejecuta las pruebas de las herramientas (validador, registro, política y hooks) |
| `bin/install-hooks.sh` | Instala los hooks `pre-commit` y `commit-msg` (se ejecuta una vez) |
| `git log --oneline` | Historial de cambios |
| `git show doc@v0.1.0` | La bóveda tal como estaba en la línea base |

---

## 8. Mapa rápido de la bóveda

| Carpeta | Qué hay |
|---|---|
| `00 - Inicio` | Convenciones, glosario, stack, plan maestro |
| `01 - Requisitos` | Visión, alcance, roles, reglas de negocio (RN), requisitos (RF, RNF), preguntas abiertas |
| `02 - Arquitectura` | Arquitectura general, paquetes, fronteras, esquemas, autorización, archivos |
| `03 - Modelo de Datos` | Identidad, alumnos, servicios, agenda, clínico, finanzas, documentos, enumeraciones |
| `04 - Seguridad y Privacidad` | Modelo de seguridad, matriz de permisos, cifrado clínico, auditoría, legal |
| `05 - Proceso de Desarrollo` | Flujo, commits, convenciones de código, PR, pruebas, contribución, **gobernanza** |
| `06 - Versionado y Rollback` | Estrategia, esquema, expand–contract, flags, release, rollback, backups |
| `07 - Infraestructura` | Servidor, hardware, instalación, entornos, PostgreSQL, red, monitoreo |
| `08 - Plan de Trabajo` | Hoja de ruta, las 10 fases con sus gates, backlog, calendario |
| `09 - Manuales del Centro` | Manuales por rol (Dirección, Secretaría, Profesional, Coordinación, Finanzas, Recepción) |
| `10 - Operación` | Runbook, checklists, incidentes, recuperación ante desastres |
| `11 - Decisiones ADR` | Índice y ADR accepted |
| `12 - Registro de Cambios` | Política, registro de cambios, bitácora de IA, versionado documental |

---

## 9. Si algo te bloquea

| Situación | Qué hacer |
|---|---|
| Una decisión no está tomada | No la tomes. Escribe el ADR en `borrador` y anótala en `Índice de ADRs.md` §3 |
| Falta un dato de Dirección | Anótala en `01.07 Preguntas Abiertas y Decisiones Pendientes` con la fase que bloquea y sigue con lo demás |
| El alcance del cambio creció | Vuelve a declarar el alcance (§2.1) y divide el trabajo |
| Otra sesión toca los mismos archivos | Espera o coordina; el estado está en `12.03` |
| La verificación falla | No commitees. Registra el estado `fallido` y corrige |
| No estás seguro de la severidad | Trátala como N3 y pregunta |

---

## 10. Referencias del proyecto

- `sistema cai/12 - Registro de Cambios/12.01 Política de Cambios y Trazabilidad.md` — la política completa
- `sistema cai/05 - Proceso de Desarrollo/05.07 Gobierno del Cambio.md` — las reglas de gobierno
- `sistema cai/05 - Proceso de Desarrollo/05.08 Revision de Calidad de las Herramientas de Gobernanza.md` — diagnóstico de las herramientas y plan P0/P1/P2
- `sistema cai/05 - Proceso de Desarrollo/05.09 Herramientas de Gobernanza.md` — contrato, códigos de salida y matriz de pruebas
- `sistema cai/11 - Decisiones ADR/Índice de ADRs.md` — decisiones tomadas y pendientes
- `sistema cai/11 - Decisiones ADR/ADR-0018 Verificación de Trazabilidad en un Punto.md` — decisión aceptada (2026-10-22) e implementada en T1
- `sistema cai/08 - Plan de Trabajo/08.12 Backlog Maestro.md` — el trabajo pendiente
- `sistema cai/00 - Inicio/00.04 Plan Maestro de Implementación.md` — el plan completo
