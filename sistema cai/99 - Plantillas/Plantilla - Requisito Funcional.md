---
title: Plantilla - Requisito Funcional
type: plantilla
status: vigente
tags: [cai, plantilla, requisito, rf, trazabilidad]
owner: Responsable técnico
updated: 2026-10-22
related:
  - "[[00.01 Convenciones de la Vault]]"
  - "[[01.05 Requisitos Funcionales]]"
  - "[[01.04 Reglas de Negocio]]"
---

# Plantilla - Requisito Funcional

> [!info] Qué es un requisito funcional
> Un **requisito funcional** describe **qué debe hacer el sistema** desde el punto de
> vista de quien lo usa, sin especificar cómo lo hace.
>
> La diferencia con una regla de negocio:
> - **Requisito**: "el sistema debe permitir registrar un pago" (el sistema lo hace).
> - **Regla de negocio**: "un pago no puede superar la suma de los cargos pendientes"
>   (la realidad lo impone, con o sin sistema).

---

## Los tipos de requisito

| Tipo | Prefijo | Qué describe |
|---|---|---|
| **Funcional** | `RF-XXX` | Una capacidad del sistema |
| **No funcional** | `RNF-XXX` | Una cualidad (rendimiento, disponibilidad, seguridad) |
| **Regla de negocio** | `RN-XXX` | Una restricción del dominio, exista o no el sistema |
| **Dato** | `D-XXX` | Una entidad o atributo que el sistema debe manejar |

---

## La plantilla

```markdown
---
title: Requisito Funcional RF-XXX <Título>
type: requisito
status: vigente
tags: [cai, requisito, rf, <modulo>]
owner: <rol>
updated: YYYY-MM-DD
related:
  - "[[01.05 Requisitos Funcionales]]"
  - "[[01.04 Reglas de Negocio]]"
  - "[[Documento del módulo]]"
---

# RF-XXX — <Título del requisito>

| Campo | Valor |
|---|---|
| **ID** | RF-XXX |
| **Módulo** | <identity / students / scheduling / care / billing / documents / notifications / reporting> |
| **Prioridad** | P0 / P1 / P2 |
| **Fase** | FN |
| **Estado** | Vigente |
| **Actor principal** | <rol> |
| **Reglas relacionadas** | RN-XXX, RN-YYY |

---

## 1. Descripción

<Qué debe hacer el sistema, en una o dos frases, en voz activa y sin jerga técnica.>

---

## 2. Actor y precondiciones

**Actor:** <rol que ejecuta la acción>

**Precondiciones:**
- El usuario está autenticado.
- Tiene el permiso `<permiso.especifico>`.
- <Otras condiciones necesarias.>

---

## 3. Comportamiento

### 3.1 Regla general

<El flujo normal, paso a paso.>

1. ...
2. ...
3. ...

### 3.2 Casos alternos

| # | Condición | Resultado esperado |
|---|---|---|
| A-1 | ... | ... |

### 3.3 Casos de error

| # | Condición | Resultado esperado | Mensaje al usuario |
|---|---|---|---|
| E-1 | ... | ... | ... |

---

## 4. Reglas de negocio aplicables

| Regla | Enunciado |
|---|---|
| RN-XXX | ... |

---

## 5. Datos

**Entidades involucradas:**
- `schema.tabla`

**Campos nuevos o modificados:**

| Tabla | Campo | Tipo | Regla |
|---|---|---|---|
| ... | ... | ... | ... |

---

## 6. Criterios de aceptación

> [!danger] Sin criterios de aceptación, un requisito no es verificable
> Y un requisito que no se puede verificar no se puede decir que esté "cumplido".

```text
☐ <Criterio observable, redactado en positivo>
☐ <Criterio observable>
☐ <Caso de error con su comportamiento esperado>
☐ <Prueba de la línea roja de seguridad, si aplica>
```

---

## 7. Trazabilidad

| Elemento | Dónde |
|---|---|
| **Implementado en** | `packages/<modulo>/src/...` |
| **Pruebas** | `tests/Feature/<modulo>/...` |
| **Manual del usuario** | [[09.XX Manual de ...]] |
| **Documentación técnica** | [[03.XX ...]] |

---

## 8. Preguntas abiertas

| # | Pregunta | Quién responde | Estado |
|---|---|---|---|
| | | | Abierta |
```

---

## Ejemplo comentado

### La descripción

```markdown
## 1. Descripción

El sistema debe permitir registrar un pago recibido de una familia y imputarlo
automáticamente a los cargos pendientes de esa cuenta, generando el recibo
correspondiente.
```

> [!tip] "El sistema debe permitir..."
> La frase "El sistema debe" es la convención. Distingue un requisito del sistema de
> una regla del negocio o de una tarea de desarrollo.

### Los casos de error

```markdown
### 3.3 Casos de error

| # | Condición | Resultado esperado | Mensaje al usuario |
|---|---|---|---|
| E-1 | El importe es cero o negativo | La operación se rechaza | "El importe del pago debe ser mayor a cero." |
| E-2 | La suma de las imputaciones supera el pago | La operación se rechaza; nada se escribe | "La suma de las imputaciones no puede superar el importe del pago." |
| E-3 | No hay cargos pendientes en la cuenta | Se permite registrar; el excedente queda como saldo a favor | "El pago se registró como saldo a favor." |
| E-4 | Ya hay una caja abierta para el usuario | La operación se rechaza | "Ya hay una caja abierta." |
```

> [!important] El error más importante de la especificación
> **Qué queda en la base de datos cuando algo falla.** Si el pago y las imputaciones
> no están en la misma transacción, un fallo a mitad de camino deja un pago sin
> imputar. El criterio de aceptación debe cubrir ese caso:
>
> ☐ Si falla la emisión del recibo, no queda ningún pago ni imputación registrados.

### Los criterios de aceptación

```markdown
## 6. Criterios de aceptación

☐ Un pago a una familia con dos hermanos se imputa a los cargos de ambos
☐ Dos pagos concurrentes no producen saldo negativo ni doble imputación
☐ Dos recibos simultáneos no obtienen el mismo número
☐ Un pago nunca se borra: se anula con motivo y restituye las imputaciones
☐ Un profesional no puede registrar ni ver pagos
```

> [!danger] El último criterio no es opcional
> **Cada requisito que toca datos sensibles incluye el criterio de denegación.**
> Sin él, el requisito se cumple a medias: la funcionalidad existe, pero la barrera
> de seguridad no está verificada.

---

## La trazabilidad completa

> [!important] El grafo de trazabilidad
> Cada requisito debe poder seguirse en las dos direcciones:
>
> ```text
> RN-042 (regla de negocio)
>   └─→ RF-018 (requisito funcional)
>         ├─→ RF-018.a (sub-requisito de la cuenta familiar)
>         │     └─→ packages/billing/src/Actions/AllocatePayment.php
>         │           └─→ tests/Feature/Billing/AllocatePaymentTest.php
>         │                 └─→ RF-018.1 (criterio de aceptación)
>         └─→ [[08.08 F6 Finanzas Familiares]] §3.5
>               └─→ [[09.05 Manual de Administración Financiera]] §4
> ```
>
> Cuando un requisito cambia, la trazabilidad dice **qué** hay que revisar. Sin
> ella, el cambio se aplica a medias y queda un código muerto que nadie sabe
> por qué existe.

---

## Errores frecuentes

| Error | Por qué duele | Cómo evitarlo |
|---|---|---|
| Requisito sin criterio de aceptación | No se puede verificar que esté cumplido | La sección 6 es obligatoria |
| Requisito técnico en lugar de funcional | Describe la solución, no la necesidad | "El sistema debe permitir...", no "se usará una tabla" |
| Requisito que mezcla varios casos | Nadie sabe cuándo está completo | Un RF = un comportamiento verificable |
| Sin actor | No se sabe quién lo usa ni qué permisos necesita | La sección 2 es obligatoria |
| Sin regla de negocio asociada | La implementación inventa la regla | Vincular al RN |
| Olvidar el caso de error | El sistema falla de forma inesperada en producción | La sección 3.3 es obligatoria |
| Sin trazabilidad | Los cambios a medias | La sección 7 |

---

## Documentos relacionados

- [[00.01 Convenciones de la Vault]]
- [[01.04 Reglas de Negocio]]
- [[01.05 Requisitos Funcionales]]
- [[01.06 Requisitos No Funcionales]]
- [[Plantilla - Documento]]
