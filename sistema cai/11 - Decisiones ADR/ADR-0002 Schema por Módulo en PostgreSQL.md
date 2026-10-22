---
title: ADR-0002 Schema por Módulo en PostgreSQL
type: adr
status: aceptado
tags: [cai, adr, base-de-datos, postgres, schema, search_path, arquitectura]
owner: Responsable técnico
updated: 2026-10-22
related:
  - "[[02.05 Esquema de Base de Datos por Módulo]]"
  - "[[02.05 Esquema de Base de Datos por Módulo]]"
  - "[[08.03 F1 Andamiaje Técnico y Frontera Modular]]"
---

# ADR-0002 — Un esquema de base de datos por módulo

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-10-22 |
| **Decide** | Responsable técnico |
| **Alcance** | Estructura de la base de datos, migraciones, comandos de gestión |

---

## 1. Contexto

Cada módulo del sistema tiene sus propias tablas. Necesitamos una separación que:

- Permita **revisar los permisos** de la base de datos por dominio.
- Facilite **backups separados** (los datos clínicos no deberían viajar juntos con los
  financieros).
- Dé soporte a las **fronteras** entre módulos.

**Restricciones:**
- Un solo servidor PostgreSQL 16. No hay presupuesto para más.
- Un solo desarrollador part-time: la configuración de la base no puede ser un
  proyecto en sí mismo.
- El framework (Laravel) trabaja con **nombres de tabla sin cualificar** en la
  mayoría de los casos.

**Qué sabemos:**
- PostgreSQL soporta schemas de forma nativa y gratuita.
- Laravel soporta **conexiones múltiples**, cada una con su propio `search_path`.
- Las limitaciones de `search_path` son conocidas y **documentadas**, no anecdóticas.

---

## 2. Decisión

**Cada módulo tiene su propio esquema de PostgreSQL, con su propia conexión en
Laravel configurada mediante `search_path`, y las migraciones de cada módulo se
ejecutan de forma aislada.**

En detalle:

- **Nueve esquemas**: `identity`, `students`, `scheduling`, `care`, `billing`,
  `documents`, `notifications`, `reporting`, y `public` para los objetos shared.
- **Nueve conexiones** en `config/database.php`, cada una con
  `'search_path' => '<schema>,public'`.
- **Los modelos** usan `protected $connection = '<schema>';` y **nombres de tabla
  cortos** (`students`, `sessions`, `charges`), nunca cualificados.
- **Las claves foráneas entre esquemas** solo se permiten hacia `identity.users` y
  `students.students`, con `ON DELETE RESTRICT`.
- **Los backups** se hacen **por esquema**, cifrados por separado.
- **El comando `cai:migrate`** ejecuta las migraciones de todos los módulos.
- **El comando `cai:db:reset`** recrea todo desde cero (incluyendo los esquemas).

---

## 3. Alternativas consideradas

### 3.1 Una tabla de prefijos en un solo esquema

| Aspecto | Detalle |
|---|---|
| **Descripción** | `students_students`, `care_clinical_notes`, etc. Todo en `public`. |
| **Ventajas** | Cero configuración. `migrate:fresh` funciona. Los backups son únicos. Sin sorpresas con `hasTable()`. |
| **Desventajas** | La separación es **nominal**: un `GRANT` sobre `public` da acceso a todo. Los backups mezclan datos clínicos y financieros. |
| **Por qué se descartó** | Los dos problemas de la lista de "desventajas" son exactamente los que este ADR busca resolver: separación de permisos y separación de datos sensibles. |

### 3.2 Una base de datos por módulo

| Aspecto | Detalle |
|---|---|
| **Descripción** | Nueve bases PostgreSQL, nueve conexiones. |
| **Ventajas** | Aislamiento máximo. Permisos por base. Backup por base trivial. |
| **Desventajas** | Nueve bases que respaldar y restaurar. Las transacciones entre módulos son imposibles. El dump y la restauración se multiplican por 9. |
| **Por qué se descartó** | Multiplica el trabajo operativo sin beneficio proporcional. Un schema da el 80 % del aislamiento por el 10 % del costo. |

### 3.3 Nombres de tabla cualificados

| Aspecto | Detalle |
|---|---|
| **Descripción** | `Schema::create('students.students', ...)`. |
| **Ventajas** | Sin `search_path`, sin ambigüedad. |
| **Desventajas** | **Laravel no las soporta bien**: `hasTable()` falla, los modelos requieren `setTable()` con nombre cualificado, los Scout y los factories se complican, `migrate:fresh` no las detecta. |
| **Por qué se descartó** | Se "avanza" por la API del framework a costa de pelear contra ella en cada línea. Un schema + `search_path` da lo mismo sin pelear. |

---

## 4. Consecuencias

### 4.1 Positivas

- **Permisos por dominio**: `GRANT SELECT ON SCHEMA care TO rol_clinico;` y nada más.
  Es una barrera real, no una convención.
- **Backups separados**: `pg_dump -n care` y `pg_dump -n billing` por separado. Un
  backup que contiene notas clínicas cifradas **no** debería estar en el mismo
  archivo que los recibos.
- **Refactor más seguro**: renombrar una tabla de un módulo no toca los demás.
- **Un solo `pg_dump -Fc` para restaurar todo** sigue siendo posible.

### 4.2 Negativas (lo que aceptamos)

- **`migrate:fresh` no borra los esquemas de los módulos.** Hay que usar
  `cai:db:reset`, que hace `DROP SCHEMA ... CASCADE` y crea de nuevo. Es un golpe:
  perder el comando estándar de Laravel.
- **`hasTable()` falla con nombres cualificados.** Hay que usar `search_path` +
  nombres cortos.
- **Nueve conexiones** que mantener en `config/database.php` (y en el `.env`).
- **El `search_path` es por conexión, no por sesión.** Si dos modelos del mismo
  request usan conexiones distintas, cada uno resuelve bien su esquema. Funciona,
  pero hay que entender el mecanismo.
- **Las claves foráneas entre esquemas** funcionan, pero el planner de PostgreSQL
  tiene menos información para optimizarlas. Con el volumen de este centro
  (300 alumnos) es irrelevante.
- **Los tests** requieren que el esquema exista antes de correr. `cai:db:reset` en el
  setup.
- **`EXCLUDE` (restricciones de no-solapamiento) no se puede aplicar** sobre una
  tabla con FK a otra tabla: en `scheduling.session_professionals` se usan columnas
  denormalizadas `starts_at`/`ends_at` sincronizadas por trigger
  `scheduling.sync_session_times()`.

### 4.3 Neutras

- El **tamaño de la base** es el mismo. Un schema es un namespace, no un storage.
- Las **herramientas de administración** (pgAdmin, DBeaver) pueden trabajar con
  schemas sin problema, pero hay que elegir el schema correcto en el selector.

---

## 5. Verificación

```text
☐ `cai:migrate` crea los 9 schemas y todas sus tablas
☐ `cai:db:reset` deja la base limpia (verificado con `cai:db:status`)
☐ Un modelo de `billing` resuelve `students.students` correctamente con nombres cortos
☐ `hasTable('students')` funciona en la conexión `students`
☐ `migrate:fresh` NO borra los schemas (comportamiento conocido y documentado)
☐ Los permisos de PostgreSQL por schema funcionan (test con un rol limitado)
☐ `pg_dump -n care` genera un dump solo con el módulo clínico
☐ La restauración de un dump por esquema funciona (verificado en el ensayo de restauración)
```

> [!important] El primer caso es el que más sorprende
> Un dev que viene de Laravel y ejecuta `migrate:fresh` en un entorno de pruebas
> **no borra los datos de los módulos**. Por eso el comando `cai:db:reset` existe y
> por eso está documentado en tres lugares. Un olvido aquí puede llevar a un dev a
> "arreglar" datos de prueba en la base equivocada.

---

## 6. Reversibilidad

| Aspecto | Detalle |
|---|---|
| **¿Se puede revertir?** | Sí |
| **Cómo** | Un solo esquema `public` con las tablas actuales renombradas con prefijo (`students_students`), o directamente renombradas. Es un cambio de migración, no de lógica. |
| **Costo de revertir** | Bajo-medio. Un día de trabajo, más el ajuste de los `dump` del backup y de los `GRANT`. |
| **Señal de que hay que revertir** | Si las limitaciones de `search_path` (la lista de §4.2) empiezan a costar más que el aislamiento que aporta. La primera señal concreta sería el número de veces que un dev se tropieza con `hasTable()` o `migrate:fresh` en un mes. |

---

## 7. Referencias

- [[02.05 Esquema de Base de Datos por Módulo]]
- [[02.05 Esquema de Base de Datos por Módulo]]
- [[07.05 Configuración de PostgreSQL]]
- [[06.07 Backups y Recuperación]]
- [[08.03 F1 Andamiaje Técnico y Frontera Modular]]
