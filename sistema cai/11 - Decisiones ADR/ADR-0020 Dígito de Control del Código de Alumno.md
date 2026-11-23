---
title: ADR-0020 Dígito de Control del Código de Alumno
type: adr
status: aceptado
tags: [cai, adr, alumnos, estudiantes, codigo, checksum, importacion]
owner: Responsable técnico
updated: 2026-11-23
related:
  - "[[08.05 F3 Alumnos Tutores y Cuentas Familiares]]"
  - "[[03.02 Alumnos, Tutores y Cuentas Familiares]]"
  - "[[ADR-0007 Cuentas Familiares Compartidas]]"
  - "[[12.01 Política de Cambios y Trazabilidad]]"
---

# ADR-0020 — Dígito de control del código de alumno

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-11-23 |
| **Decide** | Responsable técnico — aprobación explícita del operador Cesar Benitez el 2026-11-23, para el cierre del paso 2 de F3 |
| **Alcance** | Módulo `students`: generador de códigos, validación e importador de la planilla |

---

## 1. Contexto

[[08.05 F3 Alumnos Tutores y Cuentas Familiares]] §2.2 pide un `student_code`
estable y legible, "generado con secuencia + checksum". El pseudocódigo del
documento muestra el formato `ALU-AAAA-NNNN` y **no define el algoritmo del
checksum**. REG-2026-058, que implementó ese pseudocódigo, dejó la decisión
pendiente y advirtió que no se inventaría un algoritmo sin resolución.

El código aparece en planillas, listas de asistencia y carpetas físicas del
centro. Se escribe y se transcribe a mano: un error en una cifra del año o del
correlativo produce un alumno equivocado o un duplicado. La planilla actual
todavía no se importó y no hay datos reales en el repositorio.

**Restricciones:**

- El código debe seguir siendo legible: `ALU-2026-0042` es preferible a un UUID
  para el uso diario del centro ([[08.05 F3 Alumnos Tutores y Cuentas Familiares]] §2.2).
- Debe detectar errores de transcripción **también en el año**, no solo en el
  correlativo.
- No puede depender de servicios externos ni de una tabla de lookup adicional.
- El importador necesita distinguir "código sin dígito" de "código con dígito
  incorrecto" para producir un reporte de rechazos útil (§2.6).

---

## 2. Decisión

**El formato del código de alumno pasa a `ALU-AAAA-NNNN-C`, donde `C` es un
dígito de control Luhn (módulo 10) calculado sobre los ocho dígitos `AAAANNNN`.**

**En detalle:**

- `StudentCodeGenerator::generate()` genera el dígito con `checkDigit()` sobre
  el payload `sprintf('%04d%04d', $year, $sequence->current)`.
- `StudentCodeGenerator::isValid()` exige el patrón completo con el dígito y
  comprueba que coincida; el patrón con guion y el dígito son obligatorios.
- Un código preferido pasado a `generate()` se reutiliza solo si es válido;
  si no lo es, se lanza `InvalidArgumentException` en lugar de aceptarlo.
- El importador rechaza con `missing_checksum` una fila cuyo código no trae el
  dígito, y con `invalid_checksum` una fila cuyo dígito no coincide.
- El correlativo por año sigue protegido con `lockForUpdate` dentro de una
  transacción: el checksum detecta errores de transcripción, no reemplaza a la
  unicidad.

**Alternativa elegida porque:**
- Luhn es determinista, de un solo dígito y ya se usa para documentos y tarjetas:
  el centro no necesita aprender un formato nuevo.
- Calcularlo sobre los ocho dígitos incluye el año, que es justo el dato que
  antes podía transcribirse mal sin consecuencias.
- No agrega tablas, migraciones ni dependencias.

---

## 3. Alternativas consideradas

### 3.1 Mantener `ALU-AAAA-NNNN` sin checksum

| Aspecto | Detalle |
|---|---|
| **Descripción** | Dejar el formato de REG-2026-058 y no implementar el checksum que el texto de 08.05 menciona |
| **Ventajas** | Cero cambios; no hay que avisar al centro |
| **Desventajas** | Un error de una cifra pasa desapercibido y puede imputar una ficha a otro alumno |
| **Por qué se descartó** | El centro transcribe estos códigos a mano; la detección de errores es el propósito del checksum pedido en 08.05 |

### 3.2 Usar un UUID como identificador visible

| Aspecto | Detalle |
|---|---|
| **Descripción** | Sustituir el código legible por un UUID |
| **Ventajas** | Unicidad global sin secuencia ni bloqueo |
| **Desventajas** | Imposible de transcribir a mano; contradice 08.05 §2.2 |
| **Por qué se descartó** | El código legible reduce errores humanos frente al UUID (08.05 §2.2) |

### 3.3 Calcular el dígito solo sobre el correlativo `NNNN`

| Aspecto | Detalle |
|---|---|
| **Descripción** | Ignorar el año en el payload del checksum |
| **Ventajas** | Código un dígito más corto en el cálculo |
| **Desventajas** | No detecta un error al transcribir el año; `ALU-2025-0042` y `ALU-2026-0042` tendrían el mismo dígito |
| **Por qué se descartó** | El año es parte del código y es un error de transcripción frecuente |

### 3.4 Usar Verhoeff en lugar de Luhn

| Aspecto | Detalle |
|---|---|
| **Descripción** | Dígito de control Verhoeff, que detecta más transposiciones que Luhn |
| **Ventajas** | Mayor potencia de detección |
| **Desventajas** | Más código, tablas de sustitución y más difícil de verificar a mano; sin una necesidad demostrada en el centro |
| **Por qué se descartó** | GC-11: Luhn cubre el caso real con menos piezas |

---

## 4. Consecuencias

### 4.1 Positivas

- Un código mal transcripto se detecta antes de crear una ficha.
- El importador produce un motivo de rechazo accionable (`missing_checksum` /
  `invalid_checksum`) en el reporte de la planilla.
- No se agrega ninguna tabla ni dependencia nueva.

### 4.2 Negativas (lo que aceptamos)

- El formato publicado en REG-2026-058 cambia: los códigos `ALU-AAAA-NNNN` dejan
  de ser válidos. Hay que comunicar el formato nuevo al centro **antes** de la
  importación de la planilla real.
- Cualquier CSV de prueba armado con el formato anterior se rechaza entero.

### 4.3 Neutras / equilibradas

- No requiere migración de esquema: `student_code` es texto y no hay datos
  reales cargados todavía. Si en el futuro hubiera códigos grabados con el
  formato anterior, el cambio se haría con [[ADR-0003 Expand-Contract y Feature Flags]].

---

## 5. Verificación

Decisión implementada en el repo de producto el 2026-11-23 con la apertura del
paso 2 de F3.

```text
[x] `ALU-2026-0001-1`, `ALU-2026-0002-9`, `ALU-2027-0001-9` generados por la secuencia
[x] `ALU-2026-0042-5` aceptado; `ALU-2026-0042-6` y `ALU-2026-0024-5` rechazados
[x] `ALU-2026-0042` (sin dígito) rechazado; `alu-2026-0042-5` (minúsculas) rechazado
[x] Un código preferido inválido lanza `InvalidArgumentException`
[x] El importador reporta `missing_checksum` e `invalid_checksum` en `--dry-run`
[x] `composer check` OK y suites Unit/Feature/Arch/Smoke verdes
```

---

## 6. Reversibilidad

| Aspecto | Detalle |
|---|---|
| **¿Se puede revertir?** | Sí, mientras no se importen datos reales |
| **Cómo** | Restaurar `StudentCodeGenerator` y el validador al patrón `ALU-AAAA-NNNN`; el ADR pasa a `reemplazado` mediante uno nuevo |
| **Costo de revertir** | Bajo antes de la importación: es código y tests, sin datos grabados |
| **Señal de que hay que revertir** | El centro no puede usar el dígito en sus planillas o el reporte de rechazos es inmanejable |

---

## 7. Referencias

- [[08.05 F3 Alumnos Tutores y Cuentas Familiares]] — origen del requisito de checksum (§2.2 y §2.6)
- [[03.02 Alumnos, Tutores y Cuentas Familiares]] — modelo de `student_code`
- [[ADR-0007 Cuentas Familiares Compartidas]] — contexto de negocio de la ficha del alumno
- [[ADR-0003 Expand-Contract y Feature Flags]] — si hiciera falta migrar códigos ya grabados
- [[12.01 Política de Cambios y Trazabilidad]] — severidad N3 y aprobación
