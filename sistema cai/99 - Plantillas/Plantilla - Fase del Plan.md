---
title: Plantilla - Fase del Plan
type: plantilla
status: vigente
tags: [cai, plantilla, fase, plan, trabajo, gate]
owner: Responsable técnico
updated: 2026-10-22
related:
  - "[[00.01 Convenciones de la Vault]]"
  - "[[08.01 Hoja de Ruta]]"
  - "[[08.12 Backlog Maestro]]"
---

# Plantilla - Fase del Plan

> [!info] Qué es una fase
> Una **fase** es un bloque de trabajo con un objetivo, una duración estimada, tareas
> concretas, entregables verificables y un **gate** (condición de salida) que define
> cuándo se puede avanzar.
>
> La fase es la unidad de control del plan: no se avanza a la siguiente sin pasar el
> gate de la actual.

---

## Las reglas de una fase

| Regla | Detalle |
|---|---|
| **El gate es verificable** | Cada punto del gate tiene un test o una comprobación concreta. "Está listo" no es un gate |
| **Los entregables son verificables** | No "el módulo funciona" sino "el módulo tiene 11 tablas migradas" |
| **Los riesgos son reales** | Si el riesgo no tendría ningún efecto, no es un riesgo |
| **Lo pospuesto va al backlog** | Nada se descarta en silencio |
| **Lo bloqueado se escala** | Si una decisión de Dirección bloquea, se escala en 48 h, no se improvisa |
| **Se replanifica al cierre** | Con las horas reales, no con las estimaciones heredadas |

---

## La plantilla

```markdown
---
title: FN <Nombre de la Fase>
type: plan
status: vigente
tags: [cai, plan, fase, fN, <tema>]
owner: <rol responsable>
updated: YYYY-MM-DD
related:
  - "[[08.01 Hoja de Ruta]]"
  - "[[Documento de modelo de datos]]"
  - "[[ADR-XXXX Decisión relevante]]"
---

# FN — <Nombre de la Fase>

> [!info] Objetivo
> <Qué logra esta fase, en una frase. Si no se puede escribir en una frase, la fase
> está demasiado grande.>

> [!warning] Bloqueos
> <Si la fase depende de una decisión externa, declararlo aquí desde el principio,
> no descubrirlo en la semana 2.>

---

## 1. Duración

| Dedicación | Duración |
|---|---|
| 8 h/semana | ~X semanas |
| 15 h/semana | ~X semanas |

---

## 2. Tareas

### 2.1 Migraciones de `<schema>`

```text
schema.tabla_1
schema.tabla_2
```

### 2.2 <Componente principal>

<El trabajo de fondo, con el código o los criterios que importan.>

```php
// packages/modulo/src/Accion/AccionPrincipal.php
```

### 2.3 Filament: recursos

| Resource | Notas |
|---|---|
| `ModuloResource` | ... |

### 2.4 Tests

```php
it('...', function () {
    // ...
});
```

---

## 3. Entregables

| # | Entregable | Verificable |
|---|---|---|
| E-01 | ... | ... |
| E-02 | ... | ... |

---

## 4. Gate de salida

> [!success] Condición para pasar a F<N+1>
> - [ ] <Condición verificable 1>
> - [ ] <Condición verificable 2>
> - [ ] <Prueba de la línea roja de seguridad>

---

## 5. Riesgos

| Riesgo | Mitigación |
|---|---|
| ... | ... |

---

## 6. Qué se pospone

| Se pospone a | Qué |
|---|---|
| F<N+1> | ... |
| Etapa 2 | ... |

---

## 7. Documentos relacionados

- [[08.01 Hoja de Ruta]]
- [[...]]
```

---

## Cómo escribir el gate de salida

> [!danger] Un gate que se puede "cumplir" sin verificar nada no es un gate
> La diferencia entre un gate útil y uno decorativo:

| ❌ Gate decorativo | ✅ Gate verificable |
|---|---|
| "El módulo funciona" | "Un profesional no puede ver notas de alumnos no asignados (test de denegación)" |
| "Los pagos se registran bien" | "Dos pagos concurrentes no producen saldo negativo ni doble imputación" |
| "El cifrado está implementado" | "El valor de `content` en la base no es el texto plano (test)" |
| "Se probó el rollback" | "Los 4 niveles de rollback fueron probados en el servidor real (acta)" |
| "La documentación está escrita" | "Todos los wikilinks resuelven; no hay destinos rotos" |

> [!tip] La fórmula
> **Condición + cómo se verifica.**
>
> "- [ ] Un documento no es accesible por URL directa sin sesión y permiso"
> "- [ ] Un profesional no ve notas de alumnos no asignados (test de denegación)"
>
> El paréntesis con el mecanismo de verificación es lo que convierte una intención en
> un gate.

---

## Cómo escribir los riesgos

> [!important] Un riesgo que no tiene mitigación es una queja
> Cada riesgo tiene: **qué puede pasar**, **qué se hace para evitarlo** y, si el
> riesgo ocurre igual, **qué se hace para contenerlo**.

| Riesgo | Mitigación |
|---|---|
| La planilla actual tiene datos sucios | Importador con `--dry-run` y reporte de rechazos; limpieza previa por parte del centro |
| El centro no valida a tiempo | Calendario de validación fijo al final de cada fase |
| El servidor del centro no está listo | Prepararlo en paralelo desde F0 |

---

## El registro de cierre de fase

> [!tip] Al cerrar una fase, completar esta tabla
> Es lo que permite replanificar con datos reales en lugar de estimaciones.

```text
Fase:            FN
Fecha de cierre: YYYY-MM-DD
Horas estimadas: ___    Horas reales: ___    Desvío: ___%

Ítems completados:  ___/___
Ítems no completados: ___
Motivo: ______________________________________

Hallazgos técnicos relevantes:
- _____________________________________________

Decisiones pendientes que siguen abiertas:
- P___: ____________________

¿El calendario restante sigue siendo válido?  Sí / No
Nuevo calendario estimado: ___ semanas
```

---

## Documentos relacionados

- [[00.01 Convenciones de la Vault]]
- [[Plantilla - Documento]]
- [[08.01 Hoja de Ruta]]
- [[08.12 Backlog Maestro]]
- [[08.13 Calendario y Estimativas]]
