# Tabla de verificaciones por entregable

Comandos ejecutados en el repo de producto (`~/Desktop/CAI`, rama `main`) salvo
donde diga **bóveda** (`~/Desktop/CAI-docs`). Todos son de lectura/análisis.
La columna "Categoría" decide si la casilla puede cerrarse en local:
`local` / `GitHub` / `credenciales` / `destructivo`.

Resultados de referencia obtenidos el 2026-10-27 (F0/F1, `main` en `f724e87`):
sirven como forma esperada, **no** como resultado — siempre se vuelve a ejecutar.

## F1 — Andamiaje Técnico y Frontera Modular (08.03)

| # | Entregable | Comando | Evidencia que cierra la casilla | Categoría |
|---|---|---|---|---|
| E-01 | Proyecto Laravel en la raíz | `php artisan --version` | `Laravel Framework <versión>` | local |
| E-02 | 9 paquetes con `composer.json`, ServiceProvider y README | `ls packages/*/composer.json \| wc -l` | `9` | local |
| E-03 | `deptrac.yaml` con la matriz | `vendor/bin/deptrac analyse` | `Violations 0 · Errors 0` (anotar también `Uncovered` y `Allowed`) | local |
| E-04 | CI en GitHub Actions con los 5 pasos | — | Badge verde del run en `main`; **no se adivina** | GitHub |
| E-05 | `main` protegida | — | Ajuste de branch protection en GitHub | GitHub |
| E-06 | 9 conexiones con `search_path` | `grep -n search_path config/database.php` | 9 entradas (`public` + 8 schemas). `php artisan db:show` **no** las muestra si la conexión activa es `sqlite` (`grep DB_CONNECTION .env`) → la casilla no cierra solo con el grep | local (config) + credenciales (abrir PG) |
| E-07 | `cai:migrate` y `cai:db:reset` | `php artisan cai:db:reset` | Ejecución exitosa contra PostgreSQL real. **Nunca lo corre la IA**: hace `DROP SCHEMA ... CASCADE` | destructivo |
| E-08 | Arch tests básicos | `composer test:arch` | `10 passed` (A-01 … A-10) | local |
| E-09 | Scripts de Composer | `composer check` | Pasa la cadena `@lint` → `@analyse` → `@deptrac` → `@test` | local |
| E-10 | `phpunit.xml` con 4 suites | `vendor/bin/pest --list-suites` | `Arch · Feature · Smoke · Unit` con conteos | local |
| — | Paquetes y providers cargados (condición del gate, no es E-xx) | `php artisan package:discover` | Los 9 `cai/*` en `DONE`; además listar los 9 ServiceProviders registrados | local |

### Postgres local (bloqueante de E-06/E-07)

Chequeo no destructivo del entorno:

```bash
php -m | grep -E "^(bcmath|gd|pdo_pgsql)$"      # las tres deben estar
systemctl is-active postgresql@16-main          # el servicio puede estar activo
psql -l                                        # y aun así fallar: FATAL: role "fernando" does not exist
```

Si falta rol/base, se **entregan** los comandos al operador (CREATE ROLE /
CREATE DATABASE / credenciales en `.env`) y la casilla queda `[ ]` con el
`FATAL:` textual observado como motivo.

## F0 — Cimientos del Entorno (08.02)

| Condición del gate | Comando | Evidencia | Dónde |
|---|---|---|---|
| `ext-bcmath` y `ext-gd` | `php -m \| grep -E "^(bcmath\|gd\|pdo_pgsql)$"` | las tres presentes | producto |
| Matriz de versiones sin conflictos | `grep version composer.lock` | PHP · Laravel · Filament · Pint reales, coincidentes con [[00.03 Stack, Versiones y Dependencias]] | producto |
| Repo privado con `main` protegida | — | GitHub (misma comprobación que E-04/E-05 de F1) | GitHub |
| Los 6 ADRs escritos | `ls "sistema cai/11 - Decisiones ADR"` | ADRs `aceptado` (hoy son 12: ADR-0001…0010 + 0017 + 0018) | bóveda |
| Runbook con estructura | `ls "sistema cai/10 - Operación"` | 10.01 Runbook · 10.02 Checklists · 10.03 Incidentes · 10.04 Desastres | bóveda |
| Bóveda completa y revisada | `bin/validate-vault.py` | `RESULTADO: OK`, 0 errores y 0 avisos, con conteo de documentos/wikilinks | bóveda |

## F2 en adelante

La tabla de entregables de cada fase está en su documento (`08.04`…`08.11`,
sección 3); se repite el mismo procedimiento: leer la columna "Verificable",
ejecutar lo que sea lectura, y clasificar el resto. Condiciones que implican
`php artisan`, Deptrac, Pest o Composer corren en el producto; las que son de
la bóveda (`validate-vault`, ADRs, registros) corren acá.

## Formato de la subsección 4.1

Encabezado obligatorio con fecha y commit observado:

```markdown
### 4.1 Verificación de entregables (AAAA-MM-DD)

Ejecutada en el repositorio de producto (`~/Desktop/CAI`, `main` en <hash>). Lo que
sigue es lo observado en esa ejecución; lo no verificado queda explícito.

| # | Entregable | Comando | Resultado |
```

Cierre con callout de lo que falta para firmar:

```markdown
> [!warning] Lo único que cierra el gate de F1
> 1. E-06/E-07 contra PostgreSQL real — falta rol y base `cai` (o credenciales para CI).
> 2. E-04/E-05 en GitHub — badge del run, protección de `main`, PR que viola Deptrac falla.
> Hasta entonces F1 queda **abierta** y F2 no se firma (AGENTS.md §1, regla 10).
```

## Trampas conocidas

- Callout roto: dentro de `> [!success]` todas las líneas de lista necesitan el
  prefijo `> - [ ]`; en F0 solo la primera lo tenía y la lista no renderizaba.
- Bash no escapa regex con `(` `)` dentro de `$(...)` (`syntax error near
  unexpected token 'newline'`); para patrones usar la herramienta Grep.
- `.deptrac.cache` aparece modificado tras cada analyse y está fuera del índice
  (REG-2026-036): no commitearlo.
- `php artisan db:show` muestra solo la conexión **activa** (local: `sqlite`),
  no las 9 conexiones pgsql definidas en `config/database.php`.
- `gh` puede no estar instalado: la comprobación GitHub se delega al operador,
  no se reemplaza por suposiciones.
