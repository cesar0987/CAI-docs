---
title: ARQUITECTURA-SISTEMA-CAI (v1 - documento original)
type: arquitectura
status: superseded
tags: [cai, antecedente, arquitectura, historico, v1]
owner: Responsable técnico
updated: 2026-10-22
related:
  - "[[00.04 Plan Maestro de Implementación]]"
  - "[[02.01 Arquitectura General]]"
  - "[[02.02 Arquitectura Modular en Paquetes]]"
  - "[[Índice de ADRs]]"
---

# Sistema Integral de Gestión del Centro de Atención Inclusiva

> Documento técnico de arquitectura. Versión 1.0 — 22 de octubre de 2026.
> Estado: diseño aprobado, pendiente de implementación.

> [!warning] Este documento es un **antecedente**
> Es la **versión 1** del diseño de arquitectura, tal como se redactó antes de
> estructurar la bóveda. Se conserva **sin modificar** por valor histórico: el
> historial de decisiones del proyecto es parte de la evidencia.
>
> **La versión vigente de la arquitectura está distribuida** en:
> [[02.01 Arquitectura General]] · [[02.02 Arquitectura Modular en Paquetes]] ·
> [[02.03 Reglas de Frontera entre Módulos]] · [[02.05 Esquema de Base de Datos por Módulo]] · [[02.06 Modelo de Autorización y Permisos]] y en los documentos de
> modelo de datos (`03 - Modelo de Datos`).
>
> **Donde este documento y la bóveda se contradigan, manda la bóveda.**
> En particular: este texto describe una estructura `app/Domain/`, que fue
> **sustituida** por paquetes Composer por dominio (ver
> [[ADR-0001 Monolito Modular en Paquetes]]).

---

## 0. Resumen ejecutivo

Centro de atención inclusiva con **~300 alumnos en crecimiento**, **20–50 usuarios internos**, atención **mixta (individual y grupal)**, **gestión financiera completa** (cuotas, pagos, deudas, recibos) y **portal para familias en una segunda etapa**.

Se construye un **monolito modular en Laravel + Filament + PostgreSQL**, alojado en **servidor propio dentro del centro**.

Regla rectora del diseño:

> Cada alumno tiene su propia historia de atención, cada familia puede tener una cuenta
> financiera compartida y los datos clínicos se protegen con permisos independientes de
> los administrativos.

**No se incluye Next.js en el MVP.** Se agregará más adelante, si aporta valor, para el
portal familiar consumiendo una API autenticada de Laravel.

---

## 1. Contexto y decisiones tomadas

| Tema | Decisión | Impacto en el diseño |
|---|---|---|
| Modelo de cobro | **Cuenta familiar compartida entre hermanos** | Entidades `family_accounts` + `family_account_members`; los cargos conservan `student_id` |
| Seguimiento profesional | **Registros clínicos o terapéuticos detallados** | Área clínica separada, cifrado en aplicación, permisos propios y trazabilidad de acceso |
| Alojamiento | **Servidor propio en el centro** | Backups externos cifrados, UPS, VPN para acceso remoto, PostgreSQL no expuesto |
| Atención | Mixta: individual + grupal | `sessions.session_type` + `session_participants` con asistencia por participante |
| Portal familiar | Segunda etapa | La lógica de negocio debe quedar fuera de Filament, en acciones/servicios de dominio reutilizables |

---

## 2. Stack tecnológico

| Componente | Elección | Nota |
|---|---|---|
| Backend | PHP 8.3+ | Compatible con la versión de Laravel elegida |
| Framework | Laravel 13 | Verificar compatibilidad con Filament antes de fijar |
| Panel web | Filament (versión compatible con Laravel) | + Livewire |
| Base de datos | PostgreSQL | Integridad referencial, restricciones, índices |
| Permisos | Policies + Gates (+ paquete compatible para Filament si facilita la administración) | Las policies **nunca** se sustituyen por permisos visuales |
| Archivos | Almacenamiento privado local (compatible con S3 a futuro) | Nada sensible en `public/` |
| Colas | Laravel Queue; Redis solo si se justifica | No instalar Redis en el MVP sin necesidad real |
| Pruebas | PHPUnit o Pest | Enfoco en autorización y consistencia financiera |
| Control de versiones | Git | Entornos: desarrollo / pruebas / producción |
| Infraestructura | Linux, Nginx, PHP-FPM, HTTPS, backups externos | Ver §9 |

**Fuera del MVP:** microservicios, IA, app móvil propia, mensajería en tiempo real,
portal familiar completo, Next.js.

---

## 3. Arquitectura funcional

### 3.1 Usuarios del sistema

`Dirección` · `Secretaría` · `Profesionales` · `Coordinación` · `Administración financiera` · `Recepción` · `Administrador técnico`

### 3.2 Capas

```
Panel administrativo — Filament
  Secretaría · Dirección · Profesionales · Finanzas

Gestión académica
  Alumnos, tutores, matrículas, grupos, sesiones, asistencia

Gestión financiera
  Cuentas familiares, cargos, pagos, imputaciones, recibos

Atención profesional
  Planes, objetivos, evaluaciones, evolución

Área clínica restringida
  Notas terapéuticas, documentos sensibles, auditoría de acceso

PostgreSQL
  Integridad referencial · Transacciones · Restricciones · Índices

Infraestructura local
  Servidor Linux · HTTPS · Almacenamiento privado · Backups externos
```

Todos los módulos comparten **una única base de datos** y reglas de negocio comunes.

### 3.3 Módulos del MVP

| # | Módulo | Contenido |
|---|---|---|
| 1 | Alumnos y familias | Ficha, identificador interno, estado; tutores, contactos de emergencia, autorizados a retirar; documentos y autorizaciones; historial de matrículas |
| 2 | Profesionales y servicios | Ficha, especialidad, disponibilidad; catálogo de servicios y tipos de atención; asignaciones; grupos, horarios y capacidad |
| 3 | Agenda y asistencia | Sesiones individuales y grupales; profesional responsable, fecha, horario, lugar; participantes y asistencia individual; cancelaciones, reprogramaciones, recuperaciones; bloqueo de superposiciones |
| 4 | Seguimiento clínico | Planes de atención, objetivos, observaciones, informes periódicos; autoría y fecha; acceso restringido por asignación y función |
| 5 | Finanzas | Planes de cuotas y aranceles; cargos, vencimientos, descuentos, ajustes; pagos totales y parciales, imputación a deudas, saldos; recibos numerados, anulaciones, caja diaria |
| 6 | Reportes | Alumnos activos/inactivos; asistencia por periodo, servicio y profesional; programadas vs. realizadas; deudas, recaudación, ingresos, caja |
| 7 | Seguridad y administración | Usuarios, roles, permisos, asignaciones; auditoría; configuración del centro y numeración de recibos; backups y control de errores |
| 8 | Comunicación | Datos de contacto y preferencias; registro de comunicaciones administrativas; recordatorios de cuotas/citas |

---

## 4. Modelo de datos definitivo

Seis dominios. Las tablas de salud/terapia **no se mezclan** con las fichas administrativas.

### A. Identidad y familias

`users`, `roles`, `permissions`, `students`, `guardians`, `student_guardians`,
`family_accounts`, `family_account_members`

- Un alumno puede tener varios tutores.
- Una familia puede tener varios alumnos.
- Una cuenta familiar puede incluir a varios hermanos y uno o más responsables de pago.
- **Acceder al estado de cuenta no concede acceso a la historia clínica de los hijos.**

### B. Servicios y agenda

`professionals`, `services`, `enrollments`, `groups`, `group_memberships`,
`sessions`, `session_professionals`, `session_participants`, `attendance_records`

### C. Atención clínica y terapéutica

`care_plans`, `care_plan_professionals`, `care_goals`, `clinical_notes`,
`clinical_note_access_grants`, `clinical_documents`, `consents`

### D. Finanzas familiares

`fee_plans`, `charges`, `payments`, `payment_allocations`, `receipts`,
`cash_sessions`, `financial_adjustments`

### E. Archivos y autorizaciones

`documents`, `authorized_pickups`, `document_access_events`

### F. Auditoría y administración

`audit_events`, `security_events`, `system_settings`, `receipt_sequences`

### 4.1 Relaciones fundamentales

```
FAMILY_ACCOUNTS ─── contiene ──→ FAMILY_ACCOUNT_MEMBERS ─── pertenece ──→ STUDENTS
        │                                                              │
        │                                                              │
        └── recibe ──→ PAYMENTS ── distribuye ──→ PAYMENT_ALLOCATIONS ──→ CHARGES
                                                                             │
STUDENTS ── tiene ──→ STUDENT_GUARDIANS ──→ GUARDIANS                    │
   ├── ofrece ──→ ENROLLMENTS ──→ SERVICES
   ├── participa ──→ SESSION_PARTICIPANTS ──→ SESSIONS ──→ SESSION_PROFESSIONALS ──→ PROFESSIONALS
   │                      │
   │                   registra ──→ ATTENDANCE_RECORDS
   ├── tiene ──→ CARE_PLANS ── define ──→ CARE_GOALS
   └── documenta ──→ CLINICAL_NOTES
```

### 4.2 Distinción clave: inscripción ≠ sesión ≠ asistencia

| Concepto | Significado | Ejemplo |
|---|---|---|
| **Inscripción / matrícula** (*enrollment*) | Qué servicio recibe el alumno y durante qué periodo | Alumno A · Logopedia · 2026-03-01 → vigente |
| **Sesión** (*session*) | Qué atención se programa, cuándo, dónde y con qué profesional | Martes 10:00, Sala 2, Log. Pérez |
| **Asistencia** (*attendance*) | Qué ocurrió con **cada alumno** en esa sesión | Alumno A presente; Alumno B ausente justificado |

> Una sesión grupal de 10 alumnos tiene **un** registro de sesión y **diez** registros de
> participación/asistencia. Nunca 10 sesiones duplicadas.

### 4.3 Precisión sobre el modelo financiero

Aunque el cargo esté asociado a la **cuenta familiar**, debe conservar `student_id` y,
cuando corresponda, `enrollment_id`. Así se sabe a qué hijo y servicio pertenece cada deuda,
sin perder la visión consolidada de la familia.

---

## 5. Diseño financiero: cuentas familiares compartidas

### 5.1 Ejemplo

```
Cuenta familiar FA-0001
  Responsable de pago: Tutor autorizado

  Alumno A · Servicio individual  · Cargo mensual: G. 400.000
  Alumno B · Actividad grupal   · Cargo mensual: G. 250.000
  ─────────────────────────────────────────────────────────
  Total facturado a la familia                    G. 650.000
  Pago recibido                                  G. 500.000
  Saldo familiar pendiente                       G. 150.000
```

El pago de G. 500.000 se distribuye entre los cargos de ambos hermanos. El sistema registra
exactamente qué importe se aplica a cada cargo.

### 5.2 Reglas

1. `family_accounts` representa la cuenta financiera.
2. `family_account_members` relaciona la cuenta con los alumnos y **mantiene el historial de
   pertenencia** (alta y baja con fechas, sin borrado).
3. `charges` registra cada cargo, el alumno beneficiario y el servicio/matrícula que lo origina.
4. `payments` registra el dinero efectivamente recibido.
5. `payment_allocations` registra cómo se distribuye cada pago.
6. `receipts` identifica el comprobante de cobro emitido.
7. Correcciones = anulaciones o ajustes trazables, **nunca borrado** de operaciones confirmadas.
8. **Un tutor no ve los datos de otros integrantes de la familia por el solo hecho de pagar
   una cuota.** El acceso financiero y el acceso a los datos personales son permisos distintos.

### 5.3 Flujo operativo

```
1. Generar cargos del periodo según el plan de cuotas
2. Registrar pago (importe, método, fecha, usuario responsable)
3. Imputar el pago a uno o varios cargos  → TRANSACCIÓN
4. Emitir recibo con numeración controlada y conservar el comprobante
5. Recalcular saldo pendiente a partir de cargos + imputaciones válidas
6. Anulaciones/ajustes con motivo + auditoría
```

### 5.4 Ejemplo de estado de cuenta

| Concepto | Importe |
|---|---|
| Cargo mensual | G. 300.000 |
| Pago recibido | G. 200.000 |
| Saldo pendiente | G. 100.000 |
| Cobertura | 66,7 % |

La fuente de verdad son **cargos + imputaciones**. No se guarda un saldo editable a mano:
un saldo solo existe si hay un movimiento contable que lo justifique.

### 5.5 Recibo interno ≠ comprobante fiscal

El recibo interno de cobro **no sustituye** al comprobante tributario. Si el centro debe
emitir comprobantes fiscales, ese flujo se diseña aparte según la normativa paraguaya
aplicable (ver §11).

---

## 6. Migraciones de Laravel: orden y diseño

No se crea una migración gigante. El orden respeta las claves foráneas.

| Orden | Migraciones | Objetivo |
|---|---|---|
| 1 | `users`, roles y permisos | Autenticación y control de acceso |
| 2 | `guardians`, `students`, `student_guardians` | Identidad y relaciones familiares |
| 3 | `family_accounts`, `family_account_members` | Cuentas familiares compartidas |
| 4 | `professionals`, `services`, `enrollments` | Estructura de atención |
| 5 | `groups`, `group_memberships`, `sessions`, participantes | Agenda individual y grupal |
| 6 | `attendance_records` | Asistencia por participante |
| 7 | `care_plans`, `care_goals`, `clinical_notes` | Seguimiento clínico |
| 8 | `documents`, `consents`, `authorized_pickups` | Documentación privada |
| 9 | `fee_plans`, `charges`, `payments`, `payment_allocations` | Cuentas y cobros |
| 10 | `receipts`, `cash_sessions`, `financial_adjustments` | Comprobantes y conciliación |
| 11 | `audit_events`, `security_events`, índices finales | Trazabilidad y endurecimiento |

### 6.1 Migración: cuentas familiares

```php
<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('family_accounts', function (Blueprint $table) {
            $table->id();
            $table->string('account_code', 30)->unique();
            $table->string('display_name', 180);
            $table->string('status', 20)->default('active');
            $table->char('currency', 3)->default('PYG');
            $table->timestamps();

            $table->index('status');
        });

        Schema::create('family_account_members', function (Blueprint $table) {
            $table->id();

            $table->foreignId('family_account_id')
                ->constrained('family_accounts')
                ->restrictOnDelete();

            $table->foreignId('student_id')
                ->constrained('students')
                ->restrictOnDelete();

            $table->date('valid_from');
            $table->date('valid_until')->nullable();

            $table->timestamps();

            $table->index(['family_account_id', 'student_id']);
            $table->index(['student_id', 'valid_from', 'valid_until']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('family_account_members');
        Schema::dropIfExists('family_accounts');
    }
};
```

> **Nota de diseño:** no se aplica `UNIQUE(student_id)` en `family_account_members` sin
> considerar el historial. Si un alumno cambia de cuenta familiar, la relación anterior debe
> conservarse. Para impedir dos cuentas activas simultáneas se usará una **restricción de
> exclusión en PostgreSQL** (o una estrategia transaccional equivalente), según la política
> de negocio definitiva.

### 6.2 Migración: notas clínicas

```php
<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('clinical_notes', function (Blueprint $table) {
            $table->id();

            $table->foreignId('student_id')
                ->constrained('students')
                ->restrictOnDelete();

            $table->foreignId('author_user_id')
                ->constrained('users')
                ->restrictOnDelete();

            $table->foreignId('session_id')
                ->nullable()
                ->constrained('sessions')
                ->restrictOnDelete();

            $table->string('note_type', 40);
            $table->string('status', 20)->default('draft');

            // El contenido sensible se cifra en la aplicación.
            $table->text('content');

            $table->timestampTz('recorded_at');
            $table->timestampTz('finalized_at')->nullable();

            $table->timestamps();

            $table->index(['student_id', 'recorded_at']);
            $table->index(['author_user_id', 'recorded_at']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('clinical_notes');
    }
};
```

**Cifrado:** el contenido usa cifrado de aplicación (cast `encrypted` de Laravel), con gestión
segura de claves y **copias de seguridad de las claves** necesarias para recuperar los datos.
Consecuencia: el contenido no es indexable ni buscable con SQL convencional → los metadatos
necesarios para filtrar (alumno, autor, tipo, fecha, estado) viven **fuera** del campo cifrado.

**Ciclo de vida:** borrador → finalizada. Una nota finalizada **no se edita silenciosamente**:
las correcciones conservan el original, identifican al autor de la corrección y registran el motivo.

### 6.3 Esquema SQL ilustrativo (referencia visual del modelo relacional)

> Base ilustrativa, **no** es una migración lista para ejecutar. Faltan tablas auxiliares,
> estrategias de borrado, auditoría, índices adicionales y validaciones transaccionales.

```sql
-- ALUMNOS Y FAMILIAS
CREATE TABLE students (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_code VARCHAR(30) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    birth_date DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'inactive', 'withdrawn')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE guardians (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(40),
    email VARCHAR(254),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE student_guardians (
    student_id BIGINT NOT NULL REFERENCES students(id),
    guardian_id BIGINT NOT NULL REFERENCES guardians(id),
    relationship VARCHAR(50) NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    can_pick_up BOOLEAN NOT NULL DEFAULT FALSE,
    receives_admin_messages BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (student_id, guardian_id)
);

-- SERVICIOS Y MATRÍCULAS
CREATE TABLE services (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    default_duration_minutes INTEGER
        CHECK (default_duration_minutes > 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE enrollments (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id),
    service_id BIGINT NOT NULL REFERENCES services(id),
    start_date DATE NOT NULL,
    end_date DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'paused', 'completed', 'cancelled')),
    CHECK (end_date IS NULL OR end_date >= start_date),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- PROFESIONALES Y SESIONES
CREATE TABLE professionals (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT UNIQUE REFERENCES users(id),
    display_name VARCHAR(200) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE sessions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_id BIGINT NOT NULL REFERENCES services(id),
    session_type VARCHAR(20) NOT NULL
        CHECK (session_type IN ('individual', 'group')),
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled'
        CHECK (status IN ('scheduled', 'completed', 'cancelled', 'rescheduled')),
    location VARCHAR(150),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (ends_at > starts_at)
);

CREATE TABLE session_professionals (
    session_id BIGINT NOT NULL REFERENCES sessions(id),
    professional_id BIGINT NOT NULL REFERENCES professionals(id),
    assignment_role VARCHAR(50) NOT NULL DEFAULT 'responsible',
    PRIMARY KEY (session_id, professional_id)
);

CREATE TABLE session_participants (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES sessions(id),
    student_id BIGINT NOT NULL REFERENCES students(id),
    enrollment_id BIGINT REFERENCES enrollments(id),
    UNIQUE (session_id, student_id)
);

CREATE TABLE attendance_records (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    participant_id BIGINT NOT NULL UNIQUE REFERENCES session_participants(id),
    status VARCHAR(20) NOT NULL
        CHECK (status IN ('present', 'absent', 'late', 'excused')),
    recorded_by BIGINT NOT NULL REFERENCES users(id),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes TEXT
);

-- FINANZAS (orientativo; la versión definitiva usa family_accounts)
CREATE TABLE charges (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    family_account_id BIGINT NOT NULL REFERENCES family_accounts(id),
    student_id BIGINT NOT NULL REFERENCES students(id),
    enrollment_id BIGINT REFERENCES enrollments(id),
    description VARCHAR(200) NOT NULL,
    period DATE,
    due_date DATE NOT NULL,
    amount NUMERIC(14, 2) NOT NULL CHECK (amount > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'voided')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE payments (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    family_account_id BIGINT NOT NULL REFERENCES family_accounts(id),
    amount NUMERIC(14, 2) NOT NULL CHECK (amount > 0),
    paid_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    method VARCHAR(30) NOT NULL,
    reference VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'confirmed'
        CHECK (status IN ('confirmed', 'voided')),
    received_by BIGINT NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE payment_allocations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    payment_id BIGINT NOT NULL REFERENCES payments(id),
    charge_id BIGINT NOT NULL REFERENCES charges(id),
    amount NUMERIC(14, 2) NOT NULL CHECK (amount > 0),
    UNIQUE (payment_id, charge_id)
);

CREATE TABLE receipts (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    payment_id BIGINT NOT NULL UNIQUE REFERENCES payments(id),
    receipt_number VARCHAR(50) NOT NULL UNIQUE,
    issued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status VARCHAR(20) NOT NULL DEFAULT 'issued'
        CHECK (status IN ('issued', 'voided'))
);

-- ÍNDICES DE CONSULTA FRECUENTE
CREATE INDEX idx_enrollments_student_status ON enrollments (student_id, status);
CREATE INDEX idx_sessions_start_status      ON sessions (starts_at, status);
CREATE INDEX idx_participants_student        ON session_participants (student_id, session_id);
CREATE INDEX idx_charges_account_due         ON charges (family_account_id, due_date);
CREATE INDEX idx_payments_account_date       ON payments (family_account_id, paid_at);
```

---

## 7. Estructura del proyecto

```
centro-inclusivo/
├── app/
│   ├── Domain/
│   │   ├── Students/
│   │   │   ├── Actions/
│   │   │   ├── DTOs/
│   │   │   └── Services/
│   │   ├── Scheduling/
│   │   │   ├── Actions/
│   │   │   └── Services/
│   │   ├── Attendance/
│   │   ├── Care/
│   │   ├── Finance/
│   │   │   ├── Actions/
│   │   │   └── Services/
│   │   └── Documents/
│   ├── Models/
│   ├── Policies/
│   ├── Observers/
│   ├── Jobs/
│   └── Providers/
├── database/
│   ├── migrations/
│   ├── factories/
│   └── seeders/
├── resources/
│   └── views/
├── routes/
│   ├── web.php
│   └── api.php
├── tests/
│   ├── Feature/
│   │   ├── Students/
│   │   ├── Scheduling/
│   │   ├── Attendance/
│   │   ├── Care/
│   │   ├── Finance/
│   │   └── Security/
│   └── Unit/
├── storage/
├── config/
└── composer.json
```

> `Domain/` es una organización propia del proyecto, no una carpeta obligatoria de Laravel.
> Los modelos Eloquent y las migraciones se mantienen en sus ubicaciones convencionales;
> los servicios y acciones de dominio se usan donde la lógica sea importante o compleja.

### 7.1 Organización de Filament

```
app/Filament/
├── Resources/
│   ├── Students/
│   ├── Guardians/
│   ├── FamilyAccounts/
│   ├── Professionals/
│   ├── Services/
│   ├── Enrollments/
│   ├── Groups/
│   ├── Sessions/
│   ├── Attendance/
│   ├── CarePlans/
│   ├── ClinicalNotes/
│   ├── Charges/
│   ├── Payments/
│   └── Receipts/
├── Pages/
├── Widgets/
└── Clusters/
```

> La estructura exacta depende de la versión de Filament, cuyas convenciones de generación de
> recursos pueden variar.

### 7.2 Regla de oro: la lógica no vive en Filament

La acción de registrar un pago **no** se implementa en el método del formulario. Llama a un
servicio de dominio (por ejemplo `RegisterPayment`) que valida el importe, distribuye las
imputaciones, registra la operación y emite el recibo dentro de una transacción. Así la lógica
se reutiliza sin duplicación en un futuro portal Next.js o API.

---

## 8. Seguridad: acceso mínimo y datos sensibles

### 8.1 Las cinco capas de autorización

| Capa | Pregunta que responde |
|---|---|
| **Rol** | ¿Qué función desempeña el usuario? |
| **Asignación** | ¿Qué alumnos, servicios o sesiones tiene bajo su responsabilidad? |
| **Tipo de dato** | ¿La información es administrativa, financiera o clínica? |
| **Estado de la operación** | ¿Borrador o registro finalizado? |
| **Motivo excepcional** | ¿Acceso extraordinario autorizado y registrado? |

### 8.2 Matriz inicial de permisos

| Función | Acceso previsto |
|---|---|
| Dirección | Indicadores generales y acceso específico aprobado a otros módulos |
| Secretaría | Alumnos, tutores, matrículas y documentación administrativa |
| Profesional | Alumnos asignados, agenda, asistencia y notas autorizadas |
| Coordinación | Asignaciones, planes y supervisión clínica según competencia |
| Finanzas | Cuentas familiares, cargos, pagos, recibos y reportes |
| Recepción | Agenda y datos de contacto mínimos |
| Administrador técnico | Usuarios y configuración; **sin acceso ordinario al contenido clínico** |

> Base de trabajo, no autorización automática. Los permisos de un paquete de roles **complementan**
> las policies, nunca las reemplazan. Un profesional puede tener permisos de coordinación sin
> acceso a finanzas.

### 8.3 Policy de notas clínicas (ejemplo)

```php
<?php

namespace App\Policies;

use App\Models\ClinicalNote;
use App\Models\User;

class ClinicalNotePolicy
{
    public function view(User $user, ClinicalNote $note): bool
    {
        // El permiso clínico no se hereda del acceso administrativo.
        if (! $user->hasPermissionTo('clinical-notes.view')) {
            return false;
        }

        // El autor puede consultar sus notas.
        if ($note->author_user_id === $user->id) {
            return true;
        }

        // Verifica una asignación vigente al alumno
        // y el permiso profesional correspondiente.
        return $user->hasActiveClinicalAssignmentFor($note->student_id);
    }

    public function create(User $user): bool
    {
        return $user->hasPermissionTo('clinical-notes.create')
            && $user->hasActiveProfessionalProfile();
    }

    public function update(User $user, ClinicalNote $note): bool
    {
        return $note->status === 'draft'
            && $note->author_user_id === $user->id
            && $user->hasPermissionTo('clinical-notes.update-own-drafts');
    }
}
```

> `hasActiveClinicalAssignmentFor()` y `hasActiveProfessionalProfile()` son métodos de dominio
> **ilustrativos** que hay que implementar. No existen automáticamente en Laravel.
>
> Esta policy es un punto de partida: debe verificar además que la asignación sea válida para
> el tipo de atención y el periodo correspondientes.

Policies a crear: `StudentPolicy`, `FamilyAccountPolicy`, `PaymentPolicy`, `ReceiptPolicy`,
`SessionPolicy`, `DocumentPolicy`, `ClinicalNotePolicy`.

### 8.4 Medidas obligatorias

1. Aplicar las policies a **páginas, acciones, relaciones, exportaciones, descargas y endpoints**.
2. Filtrar consultas por alumnos autorizados, **manteniendo la policy como segunda barrera**.
3. **No** mostrar notas clínicas en widgets generales, búsquedas globales ni exportaciones
   administrativas.
4. Registrar accesos extraordinarios y operaciones sensibles en una auditoría protegida.
5. Separar la capacidad de **administrar usuarios** de la de **leer información clínica**.
6. Probar permisos con usuarios distintos, incluyendo **accesos directos a URLs** y solicitudes
   manipuladas.
7. Descarga de documentos por ruta autenticada que comprueba permisos en cada solicitud.
   Nada de enlaces públicos permanentes para archivos sensibles.
8. Contraseñas seguras, limitación de intentos de acceso y **MFA para cuentas privilegiadas**.
9. Recopilar solo los datos necesarios; definir plazos de conservación y gestionar
   consentimientos y solicitudes de acceso.

### 8.5 Accesos excepcionales

Los accesos extraordinarios al área clínica (por ejemplo, una dirección que necesita
verificar un informe puntual) se modelan en `clinical_note_access_grants`:

- Concedidos por un usuario autorizado.
- Con **motivo obligatorio**.
- Con **fecha de expiración**.
- Registrados en `security_events` y visibles en la auditoría.

---

## 9. Infraestructura: servidor propio en el centro

Para 300 alumnos y 20–50 usuarios internos no hace falta un clúster. Sí hace falta que un
fallo del equipo, un robo o un corte eléctrico no dejen al centro sin sistema ni datos.

### 9.1 Equipos

| Equipo | Componentes |
|---|---|
| Centro | Navegador web · HTTPS · Red autorizada o VPN |
| Servidor Linux | Nginx/Apache · PHP-FPM · Laravel · Filament |
| Datos | PostgreSQL + almacenamiento privado · Red interna · Cuentas de servicio · Permisos restringidos |
| Backup local | Copia rápida para recuperar errores operativos |
| Backup externo cifrado | Protección ante robo, incendio o fallo del servidor |

### 9.2 Requisitos operativos

- Servidor Linux con actualizaciones de seguridad y acceso administrativo limitado.
- **UPS** para continuidad breve y apagado controlado.
- **PostgreSQL no expuesto a la red pública.**
- **HTTPS incluso dentro de la red local**, con certificados y renovación gestionada.
- Copias automáticas de base de datos y documentos, con **retención definida** y **pruebas
  periódicas de restauración**.
- Monitoreo de espacio en disco, salud del servidor, errores y estado de los backups.
- Procedimiento de recuperación verificado: el centro debe poder operar de forma segura si el
  servidor no está disponible.

### 9.3 Recomendación de red

La aplicación puede usarse desde las sedes autorizadas, **sin exponer PostgreSQL ni el panel
administrativo directamente a Internet**. El acceso remoto, si se necesita, debe pasar por
**VPN** o una solución de acceso seguro equivalente.

### 9.4 Regla de backup

> Un backup en el mismo servidor **no es suficiente**.

Punto de partida: copias **diarias cifradas** a un destino separado + **una copia externa**,
con **restauración probada**. La frecuencia definitiva depende de cuánto trabajo podría perder
el centro sin causar un perjuicio operativo.

> Claves de cifrado: los backups de base de datos deben poder restaurarse, y las claves de
> cifrado de la aplicación (`APP_KEY`) deben respaldarse **separadamente y de forma segura**.
> Un backup sin su clave es un backup inservible.

---

## 10. Orden de implementación del MVP

| # | Entrega | Contenido | Criterio de aceptación |
|---|---|---|---|
| **01** | Fundación y seguridad | Repositorio, Laravel, Filament, PostgreSQL, migraciones, usuarios, roles, policies, auditoría básica, backups | Un usuario sin permisos no puede acceder a funciones protegidas, **ni por URL directa** |
| **02** | Alumnos, tutores y cuentas familiares | Fichas, relaciones familiares, contactos autorizados, cuentas compartidas, importación de datos existentes | Varios hermanos en la misma cuenta financiera **sin mezclar sus fichas personales** |
| **03** | Servicios, profesionales y agenda | Matrículas, asignaciones, sesiones individuales y grupales, participantes, asistencia, reprogramaciones | Una sesión grupal tiene **un** registro y asistencia independiente por participante |
| **04** | Seguimiento clínico | Planes, objetivos, notas, documentos sensibles, finalización de registros, permisos específicos | Un profesional no puede consultar notas de alumnos ajenos; las notas finalizadas no se alteran sin trazabilidad |
| **05** | Finanzas familiares | Aranceles, cargos, pagos parciales, imputaciones, recibos, caja, ajustes, reportes de deuda | Saldos consistentes, pagos no duplicados, anulaciones conservan historial |
| **06** | Reportes, capacitación y producción | Indicadores, pruebas con usuarios reales, carga validada, capacitación, recuperación ante incidentes | El centro puede operar, consultar informes y **restaurar desde una copia de seguridad probada** |

No se fija un plazo cerrado hasta conocer la calidad de los datos actuales, los procesos de
cobro y el nivel de detalle clínico requerido. Es preferible entregar módulos verificables que
intentar terminar todo en una fecha arbitraria.

---

## 11. Pendientes de resolver antes de producción

1. **Revisión legal.** Al tratarse de menores y registros clínicos, revisar con asesoría
   competente la normativa paraguaya aplicable a: datos personales, información de salud,
   consentimiento de responsables, conservación de registros y derechos de acceso. El diseño
   técnico facilita el cumplimiento, pero **no lo sustituye**.
2. **Políticas de conservación.** Plazo de conservación de notas clínicas, eliminación de
   documentos, atención a solicitudes de acceso y gestión de incidentes. No todo dato se
   conserva indefinidamente; tampoco todo registro se elimina a petición de un usuario sin
   evaluar obligaciones.
3. **Comprobantes fiscales.** Definir si el centro emite comprobantes tributarios y, en ese
   caso, diseñar ese flujo aparte del recibo interno.
4. **Reglas de negocio pendientes.** Documentar cómo se inscribe un alumno, cómo se asigna a
   profesionales, cómo funcionan las cuotas, quién puede consultar cada tipo de información y
   cómo se autoriza un acceso excepcional.
5. **Numeración de recibos.** Definir el formato y la secuencia antes de emitir el primer recibo.
6. **Importación de datos actuales.** Identificadores estables para alumnos, procedimiento
   seguro de importación y controles de calidad.

---

## 12. Checklist de verificación antes de dar el MVP por terminado

- [ ] Un profesional no puede acceder a un alumno no autorizado.
- [ ] Un pago concurrente no genera inconsistencias de saldo.
- [ ] Una anulación conserva el historial completo.
- [ ] Una copia de seguridad puede restaurarse correctamente (probado, no supuesto).
- [ ] Las notas finalizadas no se modifican sin dejar registro del autor y motivo.
- [ ] Los documentos sensibles no son accesibles por URL pública.
- [ ] Las exportaciones administrativas no incluyen contenido clínico.
- [ ] Los permisos funcionan también con acceso directo a URLs.

---

## 13. Recomendación final

Construir el sistema como **monolito modular Laravel + Filament + PostgreSQL**, con:

- Cuentas financieras familiares compartidas y separación estricta de los registros clínicos.
- Lógica de negocio en acciones/servicios de dominio, reutilizables por el futuro portal familiar.
- Servidor propio en el centro con **copias externas verificadas**, **acceso remoto seguro**
  (VPN) y un **procedimiento de recuperación probado**.

El siguiente paso técnico es la **fundación**: usuarios, roles, permisos, auditoría;
luego alumnos, tutores y relaciones; luego cuentas familiares; luego servicios,
profesionales y matrículas; luego agenda y asistencia; luego área clínica restringida;
y por último finanzas, pagos y recibos. Así cada módulo se desarrolla y se prueba sin
comprometer la integridad de los datos.
