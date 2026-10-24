# CAI — Documentación

Repositorio de documentación, gobernanza, trazabilidad y validación del Sistema
Integral de Gestión del Centro de Atención Inclusiva (CAI).

El código de producto vive en un repositorio separado. Acá viven la bóveda, las
reglas de trabajo y las herramientas que las hacen cumplir.

---

## Contenido

| Ruta | Qué hay |
|---|---|
| `sistema cai/` | Bóveda completa de documentación (más de 100 documentos) |
| `AGENTS.md` | Contrato de trabajo obligatorio para personas y agentes de IA |
| `bin/validate-vault.py` | Validador de frontmatter, wikilinks, tablas, caracteres e índices |
| `bin/cai-log.py` | Registro de cambios (12.02), bitácora de sesiones (12.03) y verificación del mensaje de commit |
| `bin/hooks/pre-commit` | Hook que valida la bóveda cuando el commit la toca |
| `bin/hooks/commit-msg` | Hook que exige un `REG` existente en el mensaje real del commit |
| `bin/tests/` | Pruebas del validador, la política, el registro y los hooks (biblioteca estándar) |
| `bin/install-hooks.sh` | Instalador de los hooks en `.git/hooks/` |
| `.opencode/` | Configuración del agente y plugin de atribución |
| `.cai/` | Estado local de sesiones (no versionado) |

---

## Requisitos

- Python 3.10 o superior (biblioteca estándar; sin dependencias externas)
- Git
- Bash

---

## Uso

```bash
# 1. Instalar los hooks (una vez por clon)
bin/install-hooks.sh

# 2. Validar la bóveda antes de commitear
bin/validate-vault.py            # informe legible
bin/validate-vault.py --quiet    # solo errores
bin/validate-vault.py --json     # salida para máquinas

# 3. Registrar la sesión y el cambio
bin/cai-log.py sesion --operador "Cesar Benitez" \
  --modelo "opencode/big-pickle#default" --agente build \
  --objetivo "..." --area "05 - Proceso de Desarrollo" \
  --resultado completado

bin/cai-log.py cambio --tipo edición --severidad N2 \
  --motivo "..." --archivos "ruta1.md,ruta2.md" \
  --rastreo "ADR-0017" \
  --verificacion "bin/validate-vault.py -> 0 errores" \
  --autor "Cesar Benitez" --modelo "opencode/big-pickle#default"

# 4. Commit con el ID del registro en el mensaje (lo exige commit-msg)
git commit -m "docs: <descripción> (REG-AAAA-NNN)"
```

El orden no es opcional: `AGENTS.md` §5 explica por qué los hooks bloquean el
commit cuando falta el registro. Para comprobar un mensaje sin commitear:

```bash
bin/cai-log.py verificar --mensaje .git/COMMIT_EDITMSG
```

---

## Pruebas

```bash
python3 -m unittest discover -s bin/tests -v
```

Cubren la matriz T-01 a T-23 de `05.09` §9: validador, registro, hooks y
política (59 casos al 2026-10-23). No requieren dependencias externas; `mypy`
solo se usa en CI y de forma opcional en local.

## Estado de calidad de las herramientas

La revisión de calidad está cerrada (T1 a T4, 2026-10-22): los tres hallazgos
P0 se corrigieron, el registro se escribe una sola vez de forma atómica, el
índice se inserta bajo un marcador estable y el CI valida la bóveda y las
herramientas. El plugin ya no escribe en la bóveda y el mensaje del commit se
verifica donde existe (`commit-msg`):

- Diagnóstico y plan: `sistema cai/05 - Proceso de Desarrollo/05.08 Revision de Calidad de las Herramientas de Gobernanza.md`
- Contrato y matriz de pruebas: `sistema cai/05 - Proceso de Desarrollo/05.09 Herramientas de Gobernanza.md`
- Decisión aceptada: `sistema cai/11 - Decisiones ADR/ADR-0018 Verificación de Trazabilidad en un Punto.md`
- Trabajo priorizado: `sistema cai/08 - Plan de Trabajo/08.12 Backlog Maestro.md` §3.9

---

## Reglas que no se negocian

1. Nada se borra: se retira con `status: deprecated` o `superseded`.
2. Todo cambio lleva entrada en 12.02 y sesión en 12.03, con el modelo exacto.
3. Un ADR aceptado no se edita: se sustituye por otro.
4. No se commitean datos reales de personas ni credenciales.
5. `main` no se toca directo ni se reescribe la historia publicada.

El detalle está en `AGENTS.md`, `sistema cai/12 - Registro de Cambios/12.01 Política de Cambios y Trazabilidad.md`
y `sistema cai/05 - Proceso de Desarrollo/05.07 Gobierno del Cambio.md`.

---

## Integración continua

`.github/workflows/ci.yml` valida este repositorio en cada `push` y en cada
pull request: ejecuta el validador de la bóveda, las 59 pruebas de `bin/tests/`
y `mypy` sobre las herramientas. No usa Composer ni necesita el código de
producto.

La verificación local obligatoria antes de commitear es:

```bash
bin/validate-vault.py --quiet
python3 -m unittest discover -s bin/tests
```

---

## Patrón operativo para IA

Este repositorio no acepta trabajo de IA sin evidencia. Todo agente debe seguir este ciclo:

1. `pre-vuelo`: leer `AGENTS.md`, definir alcance y archivos exactos.
2. `anti-slop`: no inventar hechos, no ampliar el problema ni mejorar estilísticamente sin necesidad.
3. `validación`: ejecutar la comprobación relevante antes de cerrar.
4. `cierre`: registrar la sesión, el cambio y el resultado real.

El documento operativo de referencia es `DESIGN.md`.

---

## Plantilla de inicio de sesión para IA

Usá esta plantilla cada vez que una IA o agente comience a trabajar en este repositorio:

```text
TAREA:
- Objetivo real:
- Alcance exacto:
- Qué NO se toca:

FUENTES DE VERDAD:
- Documento objetivo:
- Archivos relevantes:
- ADR / RN / RF / RNF que aplican:

AGENTE / MODELO:
- Operador:
- Herramienta:
- Proveedor:
- Modelo exacto:
- Variante:
- Agente / modo:

VALIDACIÓN:
- Comando esperado:
- Resultado esperado:
- Qué evidencia haría aceptar el cierre:

RIESGOS / ANTI-SLOP:
- Inventos posibles:
- Cambios fuera de alcance:
- Suposiciones sin fuente:

CIERRE:
- Estado: completado / parcial / fallido
- Archivos tocados:
- Verificación ejecutada:
- Entradas de registro / sesión:
- Pendiente:
```

Si no se puede responder con evidencia, la tarea no se cierra como completada.

### Versión mínima (para uso diario)

```text
Antes de empezar:
- leer AGENTS.md y el documento objetivo
- definir alcance y no tocar módulos ajenos
- registrar operador, herramienta, proveedor y modelo exacto
- decidir la validación antes de cerrar

Durante la sesión:
- no inventar hechos ni resultados
- no ampliar el problema por gusto
- dejar todo en evidencia

Al cerrar:
- ejecutar la validación real
- registrar sesión y entrada de cambio
- no cerrar si falta evidencia
- si hay algo pendiente, dejarlo anotado
```

> [!important] Push manual
> La IA no ejecuta `git push`. El operador lo hace manualmente cuando la rama está lista.
