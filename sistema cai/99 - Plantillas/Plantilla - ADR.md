---
title: Plantilla - ADR
type: plantilla
status: vigente
tags: [cai, plantilla, adr, decisiones, arquitectura]
owner: Responsable técnico
updated: 2026-10-22
related:
  - "[[00.01 Convenciones de la Vault]]"
  - "[[Índice de ADRs]]"
---

# Plantilla - ADR

> [!info] Qué es un ADR
> Un **Architecture Decision Record** (registro de decisión de arquitectura) es un
> documento breve que registra **una decisión técnica**: qué se decidió, por qué, qué
> alternativas se descartaron y qué consecuencias tiene.
>
> Su valor no está en la decisión (esa está en el código), sino en el **porqué**. Sin
> el porqué, dentro de seis meses alguien va a "arreglar" algo y a romper el sistema.

---

## Cómo se nombra

```text
ADR-NNNN Título en Español.md
```

| Campo | Regla |
|---|---|
| Número | 4 dígitos, correlativo, **nunca** se reutiliza |
| Título | En español, en forma nominal ("Esquema por Módulo") |
| Ubicación | `11 - Decisiones ADR/` |

> [!danger] El número es perpetuo
> Cuando un ADR se reemplaza, el **antiguo no se borra**: se marca como `superseded` y
> el nuevo ADR lo referencia. El historial de decisiones es lineal y no se reescribe.
> Un ADR "reemplazado" que se borra pierde el contexto de por qué se cambió de idea.

---

## Los cinco estados de un ADR

| Estado | Significado |
|---|---|
| `borrador` | En discusión. No vincula |
| `aceptado` | Decidido. **Vincula** |
| `revisado` | Vigente, pero merece reevaluación |
| `reemplazado` | Sustituido por otro ADR. Se marca y se referencia |
| `descartado` | La decisión se consideró y se rechazó |

---

## La plantilla

```markdown
---
title: ADR-NNNN Título en Español
type: adr
status: aceptado
tags: [cai, adr, <tema>]
owner: <rol>
updated: YYYY-MM-DD
related:
  - "[[ADR-XXXX Otro ADR]]"
---

# ADR-NNNN — Título en Español

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | YYYY-MM-DD |
| **Decide** | <rol> |
| **Alcance** | <módulos o áreas afectadas> |

---

## 1. Contexto

<La situación. Qué problema o necesidad existe, qué restricciones hay, qué presión
hay. Sin adelantar la solución todavía.>

**Restricciones:**
- ...

**Qué sabemos:**
- ...

**Qué no sabemos:**
- ...

---

## 2. Decisión

<Lo que se decide, en una frase, en presente de indicativo y en voz activa.

"Usamos un esquema de base de datos por módulo."

No: "Se decidió que se usaría...".>

**En detalle:**
- ...

**Alternativa elegida porque:**
- ...

---

## 3. Alternativas consideradas

### 3.1 <Alternativa A>

| Aspecto | Detalle |
|---|---|
| **Descripción** | |
| **Ventajas** | |
| **Desventajas** | |
| **Por qué se descartó** | |

### 3.2 <Alternativa B>

| Aspecto | Detalle |
|---|---|
| **Descripción** | |
| **Ventajas** | |
| **Desventajas** | |
| **Por qué se descartó** | |

---

## 4. Consecuencias

### 4.1 Positivas

- ...

### 4.2 Negativas (lo que aceptamos)

- ...

### 4.3 Neutras / equilibradas

- ...

---

## 5. Verificación

<Cómo se comprueba que la decisión se está aplicando. Un ADR sin verificación es una
intención.>

```text
☐ ...
```

---

## 6. Reversibilidad

| Aspecto | Detalle |
|---|---|
| **¿Se puede revertir?** | Sí / No / Parcialmente |
| **Cómo** | |
| **Costo de revertir** | |
| **Señal de que hay que revertir** | |

---

## 7. Referencias

- [[Documento]]
- [[Otro documento]]
```

---

## Ejemplo comentado

### El encabezado

```markdown
# ADR-0002 — Un esquema de base de datos por módulo
```

El número y el título. El título describe **la decisión**, no el tema.

### El contexto

```markdown
## 1. Contexto

El centro necesita nueve dominios de datos (identidad, alumnos, agenda, clínico,
financiero, documentos, notificaciones, reportes) con reglas de acceso distintas. Una
base única con todas las tablas juntas hace que la separación entre dominios sea
solo una convención de nombres.

**Restricciones:**
- Un solo servidor PostgreSQL (no hay presupuesto para más).
- Un solo desarrollador part-time (no puede operar varios servicios).
- El proyecto debe ser reversible si la modularidad resulta contraproducente.
```

> [!tip] El contexto es la parte más importante
> Si alguien lee el ADR dentro de dos años y no entiende **por qué** se decidió
> esto, el contexto está mal escrito. El contexto es lo que permite evaluar si la
> decisión sigue siendo válida.

### Las consecuencias negativas

```markdown
### 4.2 Negativas (lo que aceptamos)

- `migrate:fresh` no borra los esquemas de los módulos: hay que usar `cai:db:reset`.
- `hasTable()` falla con nombres cualificados: hay que usar nombres cortos con `search_path`.
- Cada módulo necesita su propia conexión en `config/database.php`.
```

> [!important] Todo ADR tiene consecuencias negativas
> Un ADR que solo lista ventajas no fue evaluado honestamente. **La sección de
> consecuencias negativas es la que demuestra que la decisión pasó por un proceso
> real de comparación.** Y es la que evita que alguien proponga la misma idea dentro
> de un año.

### La reversibilidad

```markdown
## 6. Reversibilidad

| Aspecto | Detalle |
|---|---|
| **¿Se puede revertir?** | Sí |
| **Cómo** | Un solo esquema con prefijos de tabla (`students_students`) |
| **Costo de revertir** | Bajo: son cambios de migración, no de lógica |
| **Señal de que hay que revertir** | Las limitaciones de `search_path` empiezan a costar más que el aislamiento |
```

> [!danger] La reversibilidad se decide de antemano
> Decidir "esto se puede revertir" sin escribir **cómo** es una forma de no decidir
> nada. La sección de reversibilidad obliga a responder la pregunta antes de que
> sea tarde.

---

## Los errores frecuentes en los ADR

| Error | Por qué es un problema | Cómo evitarlo |
|---|---|---|
| **Escribir un diseño, no una decisión** | El diseño evoluciona; la decisión es el ancla | Que la sección 2 quepa en una frase |
| **No registrar las alternativas** | Se repiten discusiones ya resueltas | Mínimo 2 alternativas reales |
| **Solo ventajas** | No se evaluó honestamente | Sección obligatoria de negativas |
| **Sin fecha** | No se sabe si está al día | Fecha en el encabezado y en el frontmatter |
| **Sin verificación** | Es una intención | Checklist verificable |
| **Reemplazar el ADR anterior en vez de marcarlo** | Se pierde el historial | Nuevo ADR que referencia al anterior |
| **Decidir sin quien decide** | Nadie se hace cargo | Campo "Decide" con un rol |
| **Escribirlo tarde** | Ya está implementado y no hay decisión que tomar | Escribirlo **antes** de implementar |

---

## Documentos relacionados

- [[00.01 Convenciones de la Vault]]
- [[Plantilla - Documento]]
- [[Índice de ADRs]]
