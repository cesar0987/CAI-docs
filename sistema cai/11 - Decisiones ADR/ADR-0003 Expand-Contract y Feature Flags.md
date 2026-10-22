---
title: ADR-0003 Expand-Contract y Feature Flags
type: adr
status: aceptado
tags: [cai, adr, versionado, migraciones, feature-flags, kill-switch, rollback]
owner: Responsable técnico
updated: 2026-10-22
related:
  - "[[06.03 Expand-Contract]]"
  - "[[06.04 Feature Flags y Kill Switches]]"
  - "[[06.06 Procedimiento de Rollback]]"
---

# ADR-0003 — Expand–Contract y feature flags como estrategia de versionado

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-10-22 |
| **Decide** | Responsable técnico |
| **Alcance** | Migraciones de base de datos, compatibilidad entre releases, control de funcionalidad |

---

## 1. Contexto

El sistema se despliega en un **único servidor** con un proceso de release por
symlink. Un rollback de código tarda **un minuto**. El problema es que **el rollback
de código no revierte la base de datos**.

Si una migración destruye datos o cambia el esquema de forma incompatible con el
código anterior, el rollback de código deja al sistema en un estado inconsistente: el
código viejo talking con un esquema nuevo.

**Restricciones:**
- **Nunca** se hace `migrate:rollback` en producción. Es una regla de seguridad de
  datos, no una preferencia.
- Un solo servidor: no hay rolling deploy con dos versiones corriendo a la vez.
- El rollback de código debe ser **siempre** posible y **rápido**.
- Dirección puede necesitar apagar una funcionalidad **en caliente**, sin esperar un
  deploy (por ejemplo, si una funcionalidad está mandando datos equivocados).

**Qué sabemos:**
- La incompatibilidad entre versiones es la causa más común de que un rollback no
  funcione.
- El patrón *expand–contract* resuelve la incompatibilidad **por diseño**.
- Un interruptor que se apaga desde la base de datos no requiere redesplegar.

---

## 2. Decisión

**Adoptamos el patrón expand–contract para todas las migraciones que rompan
compatibilidad, y mantenemos una tabla de feature flags en la base de datos que
permite apagar funcionalidades en caliente, incluidos los kill switches.**

En detalle:

### 2.1 Expand–Contract

Toda migración que cambie el esquema incompatiblemente se divide en **tres
deploys**:

| Paso | Nombre | Qué hace | Cuándo se ejecuta |
|---|---|---|---|
| 1 | **Expand** | Agrega lo nuevo (columna, tabla, índice). No rompe nada. | Deploy N |
| 2 | **Migrate** | Copia los datos, escribe en lo nuevo y en lo viejo (dual write). | Deploy N+1 |
| 3 | **Contract** | Elimina lo viejo. | Deploy N+2, cuando el release N ya no está en el servidor |

> [!important] La regla operativa
> **El paso de contract solo se ejecuta cuando el release anterior ya no es
> desplegable.** Como solo hay un release en el servidor a la vez, eso significa que
> el contract se ejecuta **un release después** del expand, como mínimo.

Ejemplo:

```php
// DEPLOY 1 — EXPAND
Schema::table('charges', function (Blueprint $table) {
    $table->decimal('total', 14, 2)->nullable();   // Nueva columna
});

// DEPLOY 2 — MIGRATE (dual write)
$charge->total = $charge->amount + $charge->tax;
$charge->save();   // Se escribe en 'total' y en 'amount'

// DEPLOY 3 — CONTRACT (solo cuando el release 1 ya no está)
Schema::table('charges', function (Blueprint $table) {
    $table->dropColumn('amount');
});
```

### 2.2 Los feature flags y kill switches

```sql
CREATE TABLE identity.feature_flags (
    id           BIGSERIAL PRIMARY KEY,
    key          VARCHAR(100) NOT NULL UNIQUE,
    enabled      BOOLEAN NOT NULL DEFAULT TRUE,
    description  TEXT,
    changed_by   BIGINT REFERENCES identity.users(id),
    changed_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    change_note  TEXT
);
```

| Tipo | Comportamiento | Ejemplo |
|---|---|---|
| **Feature flag** | Activa/desactiva una funcionalidad **nueva** | `care.new_evaluation_flow` |
| **Kill switch** | Apaga una funcionalidad **existente y crítica** | `billing.payments.enabled` |

**La diferencia es importante:** un feature flag se enciende cuando la funcionalidad
está lista; un kill switch se apaga cuando algo está mal. Los kill switches
**nunca** se eliminan del código: se quedan para siempre.

> [!danger] Un interruptor que se elimina es un interruptor que falta
> La tentación es "ya está estable, saco el flag". Si se saca, y tres meses después
> hay que apagar esa funcionalidad de nuevo, hay que desplegar código para hacerlo.
> Un interruptor cuesta 3 líneas de código. **Se quedan.**

---

## 3. Alternativas consideradas

### 3.1 `migrate:rollback` para revertir

| Aspecto | Detalle |
|---|---|
| **Descripción** | Cada migración tiene su `down()`. Si algo sale mal, se revierte. |
| **Ventajas** | Simple. Ya está en el framework. |
| **Desventajas** | Un `down()` mal escrito puede **perder datos**. Y la reversión de datos es el problema más común. |
| **Por qué se descartó** | Es una operación que **destruye información** y no se puede deshacer. En un sistema con datos de menores y de facturación, una reversión automática de una migración es un riesgo inaceptable. **Regla: nunca `migrate:rollback` en producción.** |

### 3.2 No hacer migraciones: recrear la base

| Aspecto | Detalle |
|---|---|
| **Descripción** | En cada deploy, `cai:db:reset` y se reimportan los datos. |
| **Ventajas** | Siempre limpio. |
| **Desventajas** | **Destruye todos los datos.** Imposible. |
| **Por qué se descartó** | No es una opción. Se menciona para descartarla explícitamente. |

### 3.3 Mantener dos versiones del código corriendo

| Aspecto | Detalle |
|---|---|
| **Descripción** | Blue/green deployment: dos releases activos, se cambia el balanceador de carga. |
| **Ventajas** | Rollback instantáneo sin tocar la base. Ambas versiones pueden coexistir. |
| **Desventajas** | Requiere **dos instancias** de la aplicación y una de base de datos, con todo lo que implica en memoria y complejidad. |
| **Por qué se descartó** | Con un servidor modesto, duplicar la aplicación (PHP-FPM + workers) no es viable. Y aun así, el problema de la incompatibilidad de esquema **no se resuelve**: las dos versiones siguen compartiendo la misma base. |

---

## 4. Consecuencias

### 4.1 Positivas

- **El rollback de código siempre es viable.** El esquema nunca queda ahead de forma
  incompatible.
- **Se puede apagar una funcionalidad en caliente**, sin deploy, en segundos.
- **Los deployments se pueden hacer en cualquier momento**, incluso en viernes a la
  tarde, porque el riesgo de dejar el sistema inconsistente es casi nulo.
- **El kill switch da tiempo para diagnosticar** sin la presión de "hay que arreglar
  ya".

### 4.2 Negativas (lo que aceptamos)

- **Tres deploys por cada cambio incompatible.** Un cambio grande tarda tres ciclos
  en completarse.
- **El código con dual write es más complejo** durante el período de transición.
- **Hay que ser disciplinado con el orden.** Un contract antes de tiempo rompe la
  compatibilidad y **no hay rollback que lo arregle**.
- **Los feature flags se acumulan.** Hay que limpiarlos periódicamente (los que no
  son kill switches), pero **nunca** los kill switches.
- **Un flag mal configurado** puede activar una funcionalidad a medias. Por eso los
  flags tienen descripción y `change_note`.
- **El dual write duplica la lógica de escritura**: si el modelo escribe en las dos
  columnas, hay que acordarse de hacerlo en **todos** los caminos de escritura.

### 4.3 Neutras

- La tabla `identity.feature_flags` es mínima y no requiere migración.
- Los flags se leen desde caché, por lo que el cambio es casi instantáneo.

---

## 5. Verificación

```text
☐ Una migración rename de columna se hace en 3 pasos y la CI lo verifica
☐ Un test verifica que el release N-1 puede leer el esquema del release N
☐ Un kill switch apaga la funcionalidad en menos de 5 segundos, sin deploy
☐ La tabla feature_flags tiene descripción y change_note en todas sus filas
☐ Existe un procedimiento documentado para NO ejecutar un contract antes de tiempo
☐ Los kill switches están listados en el runbook con su Procedimiento de activación
☐ Un test verifica que un kill switch de pagos bloquea el registro de pagos
```

> [!important] La verificación que importa
> **Un kill switch que nunca se probó no es un kill switch.** Igual que un rollback
> no probado. El ensayo de §5 del checklist de F8 incluye apagar y encender un
> kill switch.

---

## 6. Reversibilidad

| Aspecto | Detalle |
|---|---|
| **¿Se puede revertir?** | No aplica: es una estrategia, no una implementación |
| **Cómo** | El patrón es el estándar de la industria para bases relacionales. Abandonarlo sería retroceder al problema original. |
| **Señal de que hay que revisar** | Si el costo de los tres deploys resulta insostenible para el ritmo de trabajo, se puede **relajar el rigor** (por ejemplo, permitir contract y rollback manual coordinados) asumiendo el riesgo explícitamente. |

---

## 7. Referencias

- [[06.03 Expand-Contract]]
- [[06.04 Feature Flags y Kill Switches]]
- [[06.06 Procedimiento de Rollback]]
- [[02.05 Esquema de Base de Datos por Módulo]]
