---
title: Índice de ADRs
type: moc
status: vigente
tags: [cai, adr, indice, decisiones, moc]
owner: Responsable técnico
updated: 2026-10-22
related:
  - "[[00.01 Convenciones de la Vault]]"
  - "[[00.04 Plan Maestro de Implementación]]"
---

# Índice de ADRs

> [!info] Qué es un ADR
> Un **ADR (Architecture Decision Record)** es el registro de una decisión
> estructural: **qué** se decidió, **por qué**, **qué alternativas** se
> descartaron, y **qué consecuencias** tiene. No es una nota de reunión ni un
> informe: es un documento que, leído dentro de seis meses, permite entender
> por qué el sistema es como es.
>
> Los ADR son **inmutables en su contenido de decisión**. Si una decisión cambia,
> se escribe un ADR nuevo que **sustituye** al anterior, y el anterior pasa a
> estado `sustituido` con el enlace al nuevo.

---

## 1. Las decisiones registradas

| ADR | Título | Estado | Decide | Ámbito principal |
|---|---|---|---|---|
| [[ADR-0001 Monolito Modular en Paquetes]] | Monolito modular en paquetes | Aceptado | Responsable técnico | Arquitectura |
| [[ADR-0002 Schema por Módulo en PostgreSQL]] | Schema por módulo en PostgreSQL | Aceptado | Responsable técnico | Datos |
| [[ADR-0003 Expand-Contract y Feature Flags]] | Expand-Contract y feature flags | Aceptado | Responsable técnico | Versionado |
| [[ADR-0004 Trunk-based con Tags SemVer]] | Trunk-based con tags SemVer | Aceptado | Responsable técnico | Versionado |
| [[ADR-0005 Release por Symlink]] | Release por symlink | Aceptado | Responsable técnico | Despliegue |
| [[ADR-0006 Cifrado de Notas Clínicas]] | Cifrado de notas clínicas | Aceptado | Dirección | Seguridad |
| [[ADR-0007 Cuentas Familiares Compartidas]] | Cuentas familiares compartidas | Aceptado | Dirección | Finanzas |
| [[ADR-0008 Stack Laravel Filament PostgreSQL]] | Stack Laravel + Filament + PostgreSQL | Aceptado | Dirección | Tecnología |
| [[ADR-0009 Sin Redis en el MVP]] | Sin Redis en el MVP | Aceptado | Responsable técnico | Infraestructura |
| [[ADR-0010 Backups Externos Cifrados]] | Backups externos cifrados | Aceptado | Dirección | Continuidad |
| [[ADR-0017 Registro y Trazabilidad de Cambios]] | Registro y trazabilidad de cambios | Aceptado | Responsable técnico | Proceso |

---

## 2. Por dominio

### 2.1 Arquitectura y estructura

- [[ADR-0001 Monolito Modular en Paquetes]] — **por qué** paquetes Composer por
  dominio y no un `app/` monolítico ni microservicios.
- [[ADR-0002 Schema por Módulo en PostgreSQL]] — **por qué** un schema por
  módulo con `search_path` en lugar de nombres cualificados.
- [[ADR-0008 Stack Laravel Filament PostgreSQL]] — **por qué** este stack y no
  otro.

### 2.2 Versionado, despliegue y rollback

- [[ADR-0003 Expand-Contract y Feature Flags]] — **por qué** las migraciones son
  siempre retrocompatibles y cómo se apaga una funcionalidad.
- [[ADR-0004 Trunk-based con Tags SemVer]] — **por qué** trunk-based, tags y
  versionado por paquete.
- [[ADR-0005 Release por Symlink]] — **por qué** el despliegue es un symlink y
  no un `git pull` en caliente.

### 2.3 Seguridad y datos sensibles

- [[ADR-0006 Cifrado de Notas Clínicas]] — **por qué** el contenido de las
  notas clínicas va cifrado con AES-256-GCM y con clave separada.

### 2.4 Dominio de negocio

- [[ADR-0007 Cuentas Familiares Compartidas]] — **por qué** el cobro es por
  alumno con imputación de pagos a nivel de familia.

### 2.5 Infraestructura y continuidad

- [[ADR-0009 Sin Redis en el MVP]] — **por qué** la cola y la caché van sobre
  `database` y `file`, sin ningún servicio adicional.
- [[ADR-0010 Backups Externos Cifrados]] — **por qué** hay una copia externa
  cifrada, con la clave en manos de otra persona.

---

## 3. Decisiones pendientes de ADR

Estas decisiones están **pendientes de respuesta de Dirección** (ver
[[01.07 Preguntas Abiertas y Decisiones Pendientes]]). Cuando se resuelvan,
cada una genera un ADR nuevo:

| Pregunta | Tema | ADR esperado | Bloquea |
|---|---|---|---|
| **P1** | Cobro fijo mensual o por unidad de sesión | ADR-0011 Modelo de Cuotas | F6 |
| **P2** | Redondeo de importes en guaraníes | ADR-0012 Redondeo y Presentación Monetaria | F6 |
| **P3** | Política de asistencia y ausencias | ADR-0013 Reglas de Asistencia | F5 |
| **P4** | Conservación de notas clínicas | ADR-0014 Retención y Depuración Clínica | F5, F9 |
| **P7** | Alcance del cifrado fuera de `clinical_notes.content` | ADR-0015 Alcance del Cifrado | F5 |
| **P10** | Aceptación del modelo sin Redis | (cubierto por [[ADR-0009 Sin Redis en el MVP]]) | — |
| **P16** | Política de contraseñas y acceso al servidor | ADR-0016 Política de Contraseñas | F8 |

---

## 4. Cómo se escribe un ADR

La plantilla completa está en [[Plantilla - ADR]]. El proceso:

```mermaid
flowchart LR
  A["Problema<br/>que hay que decidir"] --> B["Borrador<br/>§1 Contexto"]
  B --> C["Alternativas<br/>§3"]
  C --> D["Decisión<br/>§2"]
  D --> E["Revisión<br/>Dirección + técnico"]
  E --> F["ADR aceptado<br/>status: aceptado"]
  F --> G["Cambio de realidad"] --> H["ADR nuevo<br/>que sustituye"]
```

| Paso | Qué se hace | Quién |
|---|---|---|
| 1 | Se identifica el problema que **no** se resuelve con una regla ya escrita | Cualquiera |
| 2 | Se rellena §1 (Contexto) **antes** de decidir nada | Quien propone |
| 3 | Se listan las alternativas reales, con sus desventajas | Quien propone |
| 4 | Se elige y se redacta §2 (Decisión) | Quien propone |
| 5 | Se revisan §4 (Consecuencias) y §5 (Verificación) | Revisor |
| 6 | Se acepta: `status: aceptado` y fecha | Dirección (o el rol competente) |

### 4.1 Reglas de estilo

| Regla | Detalle |
|---|---|
| **El ADR registra el porqué, no el cómo** | El cómo está en los documentos de arquitectura y en el código. |
| **Contexto honesto** | Si hay restricciones que el negocio no satisface, se dicen. Un ADR con contexto idealizado no sirve para nada. |
| **Al menos dos alternativas** | Siempre. Una decisión sin alternativas descartadas es una decisión sin pensar. |
| **Consecuencias negativas obligatorias** | Toda decisión tiene un costo. Un ADR sin costos es propaganda. |
| **Reversibilidad explícita** | Cómo se deshace y qué señal lo indicaría. |
| **Sin fechas de "vence"** | Un ADR no caduca. Cambia el mundo, y entonces se escribe otro. |

---

## 5. Cómo se citan los ADR

Desde cualquier documento:

```markdown
La decisión está en [[ADR-0006 Cifrado de Notas Clínicas]].
```

Desde un ADR, en la sección de referencias, se citan **los documentos
relacionados** (no los ADR, salvo que haya una relación directa de
dependencia):

```markdown
## 7. Referencias

- [[04.04 Datos Clínicos: Cifrado y Acceso]]
- [[03.05 Planes de Atención y Notas Clínicas]]
```

---

## 6. Relación con el resto de la bóveda

| Documento | Relación |
|---|---|
| [[00.01 Convenciones de la Vault]] | Define el formato y la numeración |
| [[00.04 Plan Maestro de Implementación]] | Define las fases que los ADRs condicionan |
| [[02.03 Reglas de Frontera entre Módulos]] | Concreta [[ADR-0001 Monolito Modular en Paquetes]] |
| [[02.05 Esquema de Base de Datos por Módulo]] | Concreta [[ADR-0002 Schema por Módulo en PostgreSQL]] |
| [[06.01 Estrategia de Versionado]] | Concreta [[ADR-0004 Trunk-based con Tags SemVer]] |
| [[06.03 Expand-Contract]] | Concreta [[ADR-0003 Expand-Contract y Feature Flags]] |
| [[06.06 Procedimiento de Rollback]] | Concreta [[ADR-0005 Release por Symlink]] |
| [[10.04 Recuperación ante Desastres]] | Concreta [[ADR-0010 Backups Externos Cifrados]] |
| [[12.01 Política de Cambios y Trazabilidad]] | Concreta [[ADR-0017 Registro y Trazabilidad de Cambios]] |
| [[12.02 Registro de Cambios]] | Evidencia [[ADR-0017 Registro y Trazabilidad de Cambios]] |
| [[05.07 Gobierno del Cambio]] | Concreta [[ADR-0017 Registro y Trazabilidad de Cambios]] |
| [[08.12 Backlog Maestro]] | Recoge las consecuencias pendientes de cada ADR |
