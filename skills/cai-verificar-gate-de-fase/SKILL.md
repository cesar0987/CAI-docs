---
name: cai-verificar-gate-de-fase
description: Verificar el gate de salida de una fase F0-F9 del proyecto CAI ejecutando en el repo de producto (~/Desktop/CAI) las comprobaciones no destructivas de cada entregable E-xx del documento de fase (php artisan --version, ls packages/*/composer.json, vendor/bin/deptrac analyse, composer test:arch, composer check, vendor/bin/pest --list-suites, php artisan package:discover, grep de search_path en config/database.php) y volcar comando + resultado + fecha + commit en la tabla 4.1 del documento 08.0X, marcando solo las casillas con evidencia directa y dejando las restantes explícitamente abiertas con su motivo. Usar cuando se pide cerrar, anclar o revisar el gate de una fase, comprobar el estado diseñado-vs-implementado de 08 - Plan de Trabajo, o cuando un gate tiene casillas vacías pese a tener el producto verde.
---

# Verificación del gate de fase CAI

## Overview

Ancla el gate de salida de una fase (documentos `08.02`–`08.11` de la bóveda
`~/Desktop/CAI-docs`) a evidencia real ejecutada en el repo de producto
`~/Desktop/CAI`. Regla de oro: **una casilla `[x]` solo con el comando corrido
y su resultado copiado de la salida**; todo lo demás queda `[ ]` con motivo
escrito. El gate firmado sin evidencia viola AGENTS.md §1 regla 10.

El cierre (REG/SES, atribución del modelo, validación, commit, aviso de push)
sigue el skill `cai-registro-sesion-cambio`; no duplicar su
protocolo acá.

## Cuándo usar

- "Cerrar / anclar / revisar el gate de F0/F1/…", "verificar los entregables de la fase".
- Un documento de fase tiene casillas vacías o la §4.1 desactualizada.
- Se pide comprobar qué está *implementado* vs solo *diseñado* en el producto.

## Paso 1 — Pre-vuelo

1. Leer `AGENTS.md` (reglas 0, 1, 2 y §8.1 fila "Investigar inconsistencia
   doc-vs-implementación").
2. Leer `sistema cai/12 - Registro de Cambios/12.03 Bitácora de Sesiones con IA.md`
   §4: si otra sesión tiene abierta el mismo documento de fase, esperar o coordinar.
3. Leer el documento de fase: sección **3. Entregables** (tabla E-01…E-nn con
   columna "Verificable") y **4. Gate de salida**. Los IDs E-xx y las condiciones
   del gate son la lista de trabajo; no inventar entregables que no estén ahí.

## Paso 2 — Localizar el repo de producto

- Camino real: `~/Desktop/CAI`, rama `main` (remote `git@github.com:cesar0987/CAI.git`).
- `~/Desktop/CAI-code` es un borrador abandonado: **no usarlo ni borrarlo**.
- Antes de verificar, anclar el estado observado:
  ```bash
  git -C ~/Desktop/CAI log --oneline -1
  git -C ~/Desktop/CAI status -sb
  ```
  El hash va en el encabezado de la §4.1; un árbol sucio ajeno al cambio se
  reporta, no se limpia.

## Paso 3 — Ejecutar las verificaciones no destructivas

Correr en `~/Desktop/CAI` los comandos de `references/verificaciones.md`, uno
por entregable, y guardar la salida textual (últimas líneas útiles, conteos).
Solo comandos de lectura/análisis. Prohibido ejecutar:

- `php artisan cai:db:reset` / `cai:migrate` contra datos reales (`DROP SCHEMA ... CASCADE`).
- Cualquier `sudo`, creación de roles/bases, o comando que pida credenciales.
- Nada que borre o modifique archivos del producto.

## Paso 4 — Clasificar lo que NO cierra en local

Cada entregable cae en una categoría (columna en `references/verificaciones.md`):

| Categoría | Qué hacer |
|---|---|
| **local** | Se marca `[x]` con comando + resultado en §4.1 |
| **GitHub** (CI verde, `main` protegida, PR que viola Deptrac) | Queda `[ ]` con "**No verificable en local**: requiere ver el run/ajuste en GitHub". Si no hay `gh` ni credenciales, no se adivina el badge. |
| **credenciales/sudo** (PostgreSQL: rol, base `cai`) | Queda `[ ]` con el motivo exacto del fallo observado (p. ej. `FATAL: role "fernando" does not exist`) y los comandos que el operador debe ejecutar. |
| **destructivo** (`cai:db:reset`) | **Nunca** se ejecuta sin aprobación explícita; se entrega el comando al operador y la casilla queda abierta. |

## Paso 5 — Escribir la evidencia en el documento de fase

Bajo `## 4. Gate de salida`, agregar o actualizar la subsección:

```markdown
### 4.1 Verificación de entregables (AAAA-MM-DD)

Ejecutada en el repositorio de producto (`~/Desktop/CAI`, `main` en <hash>). Lo que
sigue es lo observado en esa ejecución; lo no verificado queda explícito.

| # | Entregable | Comando | Resultado |
|---|---|---|---|
| E-01 | … | `php artisan --version` | Laravel Framework 13.38.0 |
| E-04 | … | — | **No verificable en local**: requiere ver el run en GitHub |
```

- El resultado se **copia** de la salida real (con conteos: "0 violaciones · 48 sin cubrir"), no se parafrasea como "OK".
- Marcar `[x]` en la lista del gate **solo** si la condición completa está cubierta por una fila de la tabla; si una condición depende de dos entregables y uno está abierto, la casilla queda `[ ]`.
- Bug de formato ya detectado dos veces: dentro del callout `> [!success]`, **todas** las líneas de la lista llevan el prefijo `> - [ ]` (en F0 solo la primera lo tenía y la lista estaba rota). Revisarlo al pasar.
- Al final, un callout `> [!warning]` con "lo único que cierra el gate" enumerando lo que falta y dónde se ejecuta (spec real de 08.03 §4).
- Actualizar `updated:` del frontmatter del documento de fase.

## Paso 6 — Cierre con registro

Delegar en `cai-registro-sesion-cambio`:

- Si el identificador del modelo no está en el log de hooks de Qoder (~4 de 7
  sesiones), **preguntar al operador**; jamás `—`, `no declarado` ni `qfmodel`.
- Una entrada `REG-AAAA-NNN` (tipo `edición`, severidad N2, rastreo "08.0X gate
  de salida", verificación con el resultado de `bin/validate-vault.py`) + su `SES`.
- `bin/validate-vault.py` y `bin/cai-log.py verificar --mensaje .git/COMMIT_EDITMSG`
  en OK antes de commitear; el push lo hace el operador y se le avisa el ahead count de ambos repos.

## Anti-slop

- No declarar "gate cerrado" ni "fase lista para F(n+1)" si queda una condición abierta.
- No copiar resultados de una sesión anterior: la fecha y el hash del encabezado de §4.1 tienen que corresponder a la ejecución actual.
- Bash: un regex con `(...)` dentro de `$(...)` revienta (`syntax error near unexpected token 'newline'`); usar la herramienta Grep para patrones.
- `.deptrac.cache` está fuera del índice (REG-2026-036): no commitearlo aunque aparezca modificado.

## Resources

- `references/verificaciones.md` — tabla entregable → comando → evidencia → categoría, para F1 y checks comunes de F0; formato mínimo del documento de fase.
