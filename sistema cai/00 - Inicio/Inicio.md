---
title: Inicio
type: moc
status: vigente
tags: [cai, mapa]
owner: Responsable técnico
updated: 2026-10-22
related:
  - "[[00.04 Plan Maestro de Implementación]]"
  - "[[Índice de ADRs]]"
  - "[[01.07 Preguntas Abiertas y Decisiones Pendientes]]"
---

# Sistema Integral de Gestión del Centro de Atención Inclusiva — Bóveda de Documentación

> [!abstract] Qué es esto
> Bóveda de documentación completa del sistema CAI. **Todo el diseño, las decisiones, los
> pasos de implementación y los manuales de uso están aquí.** No se escribe código hasta
> que la fase correspondiente esté documentada y aprobada.

**Estado actual:** 📋 Documentación en construcción · **Código:** no iniciado
**Versión del plan:** 1.0 · **Última actualización:** 2026-10-22

---

## 1. Cómo usar esta bóveda

| Si sos… | Empezá por… |
|---|---|
| **Dirección del centro** | [[01.01 Visión, Objetivos y Principios]] → [[01.02 Alcance del MVP]] → [[09.01 Manual de Dirección]] |
| **Responsable de implementar** | [[00.04 Plan Maestro de Implementación]] → [[08.01 Hoja de Ruta]] → fase actual en `08 - Plan de Trabajo` |
| **Profesional o usuario del sistema** | `09 - Manuales del Centro` → tu rol |
| **Alguien que entra al proyecto** | [[00.01 Convenciones de la Vault]] → [[02.01 Arquitectura General]] → [[06.01 Estrategia de Versionado]] |
| **Auditoría / revisión legal** | [[04.07 Checklist Legal y Respuesta a Incidentes]] → [[03.08 Catálogo de Enumeraciones e Integridad]] |

---

## 2. Mapa de la bóveda

### `00 - Inicio`
- [[00.01 Convenciones de la Vault]] — cómo está organizada, cómo se nombra, cómo se enlaza
- [[00.02 Glosario]] — términos del dominio y técnicos
- [[00.03 Stack, Versiones y Dependencias]] — qué se usa y por qué
- [[00.04 Plan Maestro de Implementación]] — el plan completo con análisis y comparaciones
- [[00.05 Configuracion de la Boveda]] — configuración de Obsidian, adjuntos y búsquedas guardadas

### `01 - Requisitos`
- [[01.01 Visión, Objetivos y Principios]]
- [[01.02 Alcance del MVP]] — qué entra, qué no, qué se pospone
- [[01.03 Actores y Roles del Centro]]
- [[01.04 Reglas de Negocio]] — las reglas del centro, escritas
- [[01.05 Requisitos Funcionales]] — RF-001 … RF-nnn
- [[01.06 Requisitos No Funcionales]] — RNF-001 … RNF-nnn
- [[01.07 Preguntas Abiertas y Decisiones Pendientes]] — lo que falta definir

### `02 - Arquitectura`
- [[02.01 Arquitectura General]]
- [[02.02 Arquitectura Modular en Paquetes]]
- [[02.03 Reglas de Frontera entre Módulos]]
- [[02.04 Capas Internas de un Paquete]]
- [[02.05 Esquema de Base de Datos por Módulo]]
- [[02.06 Modelo de Autorización y Permisos]]
- [[02.07 Almacenamiento de Archivos Privados]]

### `03 - Modelo de Datos`
- [[03.01 Identidad, Roles y Sesiones]]
- [[03.02 Alumnos, Tutores y Cuentas Familiares]]
- [[03.03 Servicios, Profesionales y Matrículas]]
- [[03.04 Grupos, Sesiones y Asistencia]]
- [[03.05 Planes de Atención y Notas Clínicas]]
- [[03.06 Finanzas Familiares]]
- [[03.07 Documentos, Consentimientos y Notificaciones]]
- [[03.08 Catálogo de Enumeraciones e Integridad]]

### `04 - Seguridad y Privacidad`
- [[04.01 Modelo de Seguridad]]
- [[04.02 Matriz de Permisos por Rol]]
- [[04.03 Autorización por Registro]]
- [[04.04 Datos Clínicos: Cifrado y Acceso]]
- [[04.05 Auditoría de Datos Sensibles]]
- [[04.06 Consentimientos y Privacidad]]
- [[04.07 Checklist Legal y Respuesta a Incidentes]]

### `05 - Proceso de Desarrollo`
- [[05.01 Flujo de Trabajo]]
- [[05.02 Commits, Ramas y Versionado SemVer]]
- [[05.03 Convenciones de Código]]
- [[05.04 Checklist de Pull Request]]
- [[05.05 Estrategia de Pruebas]]
- [[05.06 Guía de Contribución]]
- [[05.07 Gobierno del Cambio]] — las reglas de control, escalabilidad y legibilidad

### `06 - Versionado y Rollback`
- [[06.01 Estrategia de Versionado]]
- [[06.02 Versionado de Esquema de BD]]
- [[06.03 Expand-Contract]]
- [[06.04 Feature Flags y Kill Switches]]
- [[06.05 Release y Deploy]]
- [[06.06 Procedimiento de Rollback]]
- [[06.07 Backups y Recuperación]]

### `07 - Infraestructura`
- [[07.01 Arquitectura del Servidor del Centro]]
- [[07.02 Requisitos de Hardware y Software]]
- [[07.03 Instalación del Sistema]]
- [[07.04 Configuración de Entornos]]
- [[07.05 Configuración de PostgreSQL]]
- [[07.06 Red, HTTPS y VPN]]
- [[07.07 Monitoreo y Mantenimiento]]

### `08 - Plan de Trabajo`
- [[08.01 Hoja de Ruta]] — las 10 fases y sus gates
- [[08.02 F0 Cimientos del Entorno]] · [[08.03 F1 Andamiaje Técnico y Frontera Modular]]
- [[08.04 F2 Identidad Permisos y Auditoría]] · [[08.05 F3 Alumnos Tutores y Cuentas Familiares]]
- [[08.06 F4 Servicios Profesionales y Agenda]] · [[08.07 F5 Seguimiento Clínico]]
- [[08.08 F6 Finanzas Familiares]] · [[08.09 F7 Documentos y Comunicaciones]]
- [[08.10 F8 Reportes y Puesta en Producción]] · [[08.11 F9 Endurecimiento y Operación Continua]]
- [[08.12 Backlog Maestro]] · [[08.13 Calendario y Estimativas]]

### `09 - Manuales del Centro`
- [[09.01 Manual de Dirección]] · [[09.02 Manual de Secretaría]] · [[09.03 Manual del Profesional]]
- [[09.04 Manual de Coordinación]] · [[09.05 Manual de Administración Financiera]] · [[09.06 Manual de Recepción y Administración Técnica]]
- [[09.07 Importación de Datos Iniciales]]

### `10 - Operación`
- [[10.01 Runbook Operativo]] · [[10.02 Calendario de Checklists]]
- [[10.03 Gestión de Incidentes]] · [[10.04 Recuperación ante Desastres]]

### `11 - Decisiones ADR`
- [[Índice de ADRs]] — el MOC: qué se decidió, por qué y qué falta decidir
- [[ADR-0001 Monolito Modular en Paquetes]] · [[ADR-0002 Schema por Módulo en PostgreSQL]]
- [[ADR-0003 Expand-Contract y Feature Flags]] · [[ADR-0004 Trunk-based con Tags SemVer]]
- [[ADR-0005 Release por Symlink]] · [[ADR-0006 Cifrado de Notas Clínicas]]
- [[ADR-0007 Cuentas Familiares Compartidas]] · [[ADR-0008 Stack Laravel Filament PostgreSQL]]
- [[ADR-0009 Sin Redis en el MVP]] · [[ADR-0010 Backups Externos Cifrados]]
- [[ADR-0017 Registro y Trazabilidad de Cambios]]

### `12 - Registro de Cambios`
- [[12.01 Política de Cambios y Trazabilidad]] — qué se puede cambiar, quién lo autoriza y cómo se revierte
- [[12.02 Registro de Cambios]] — el historial append-only de todo cambio
- [[12.03 Bitácora de Sesiones con IA]] — quién hizo qué, con qué modelo
- [[12.04 Versionado de la Documentación]] — el esquema `doc@vX.Y.Z` y los cortes de versión

### `98 - Antecedentes`
- [[ARQUITECTURA-SISTEMA-CAI (v1 - documento original)]] — documento superado, conservado por histórico

### `99 - Plantillas`
- [[Plantilla - Documento]] · [[Plantilla - ADR]] · [[Plantilla - Fase del Plan]] · [[Plantilla - Requisito Funcional]]

---

## 3. Reglas de oro del proyecto

1. **Nada de código sin documentación previa.** Cada fase tiene su documento en `08 - Plan de Trabajo` con alcance, entregables, gate de salida y tareas desglosadas.
2. **Cada cambio de esquema pasa por expand–contract.** Ver [[06.03 Expand-Contract]].
3. **Ningún módulo toca datos de otro.** Ver [[02.03 Reglas de Frontera entre Módulos]].
4. **Los datos clínicos no salen del área clínica.** Ver [[04.04 Datos Clínicos: Cifrado y Acceso]].
5. **Todo release se puede deshacer.** Ver [[06.06 Procedimiento de Rollback]].
6. **El backup en el mismo servidor no es un backup.** Ver [[06.07 Backups y Recuperación]].
7. **Una decisión no obvia se escribe como ADR.** Ver [[Índice de ADRs]].
8. **Nada se borra y todo cambio se registra.** Ver [[12.01 Política de Cambios y Trazabilidad]] y [[12.02 Registro de Cambios]].

---

## 4. Estado de las fases

| Fase | Nombre | Estado | Documento |
|---|---|---|---|
| F0 | Cimientos del entorno | 📋 Pendiente | [[08.02 F0 Cimientos del Entorno]] |
| F1 | Andamiaje técnico y frontera modular | 📋 Pendiente | [[08.03 F1 Andamiaje Técnico y Frontera Modular]] |
| F2 | Identidad, permisos y auditoría | 📋 Pendiente | [[08.04 F2 Identidad Permisos y Auditoría]] |
| F3 | Alumnos, tutores y cuentas familiares | 📋 Pendiente | [[08.05 F3 Alumnos Tutores y Cuentas Familiares]] |
| F4 | Servicios, profesionales y agenda | 📋 Pendiente | [[08.06 F4 Servicios Profesionales y Agenda]] |
| F5 | Seguimiento clínico | 📋 Pendiente | [[08.07 F5 Seguimiento Clínico]] |
| F6 | Finanzas familiares | 📋 Pendiente | [[08.08 F6 Finanzas Familiares]] |
| F7 | Documentos y comunicaciones | 📋 Pendiente | [[08.09 F7 Documentos y Comunicaciones]] |
| F8 | Reportes y puesta en producción | 📋 Pendiente | [[08.10 F8 Reportes y Puesta en Producción]] |
| F9 | Endurecimiento y operación continua | 📋 Pendiente | [[08.11 F9 Endurecimiento y Operación Continua]] |

---

## 5. Decisiones registradas (ADR)

> [!info] Una decisión no obvia se escribe, no se conversa
> Los ADR registran **el porqué**. Cada uno tiene contexto, alternativas
> descartadas, consecuencias (positivas y negativas) y cómo se revertiría.

| ADR | Decisión | Ámbito |
|---|---|---|
| [[ADR-0001 Monolito Modular en Paquetes]] | Paquetes Composer por dominio, no `app/` monolítico | Arquitectura |
| [[ADR-0002 Schema por Módulo en PostgreSQL]] | Un schema por módulo con `search_path` | Datos |
| [[ADR-0003 Expand-Contract y Feature Flags]] | Migraciones retrocompatibles + interruptores | Versionado |
| [[ADR-0004 Trunk-based con Tags SemVer]] | `main` siempre verde, tags y SemVer por paquete | Versionado |
| [[ADR-0005 Release por Symlink]] | Despliegue por symlink `current`, rollback en ~1 min | Despliegue |
| [[ADR-0006 Cifrado de Notas Clínicas]] | AES-256-GCM en la columna `content`, clave separada | Seguridad |
| [[ADR-0007 Cuentas Familiares Compartidas]] | Cobro por alumno con imputación a nivel de familia | Finanzas |
| [[ADR-0008 Stack Laravel Filament PostgreSQL]] | PHP 8.3 + Laravel 11 + Filament 3 + PostgreSQL 16 | Tecnología |
| [[ADR-0009 Sin Redis en el MVP]] | Cola y caché sobre `database` y `file` | Infraestructura |
| [[ADR-0010 Backups Externos Cifrados]] | Regla 3-2-1 con copia externa cifrada y custodio aparte | Continuidad |
| [[ADR-0017 Registro y Trazabilidad de Cambios]] | Bóveda versionada, registro append-only y atribución de IA | Gobernanza |

**Pendientes de decisión de Dirección:** P1 (modelo de cuotas), P2 (redondeo),
P3 (asistencia), P4 (retención clínica), P7 (alcance del cifrado) y P16
(política de contraseñas). Ver [[01.07 Preguntas Abiertas y Decisiones Pendientes]].

---

## 6. Registro y trazabilidad

> [!important] Antes de tocar un archivo, lee `AGENTS.md`
> `AGENTS.md` (raíz del repositorio) es la puerta de entrada obligatoria para
> cualquier agente, humano o IA. Enumera el orden de lectura, las prohibiciones y
> lo que hay que registrar.

| Documento | Para qué |
|---|---|
| `AGENTS.md` (raíz) | Las reglas no negociables; se lee antes de actuar |
| [[12.01 Política de Cambios y Trazabilidad]] | Qué se puede cambiar, severidad, aprobación y reversión |
| [[12.02 Registro de Cambios]] | El historial de todo cambio: motivo, archivos, verificación y autor |
| [[12.03 Bitácora de Sesiones con IA]] | Qué modelo intervino en cada sesión y con qué resultado |
| [[12.04 Versionado de la Documentación]] | Cómo se corta y se consulta una versión de la bóveda |
| [[05.07 Gobierno del Cambio]] | Las reglas de control, escalabilidad y legibilidad |

**Versionado de la bóveda:** tag `doc@vX.Y.Z`. Línea base: `doc@v0.1.0`.

---

## 7. Documentos relacionados

- [[01.07 Preguntas Abiertas y Decisiones Pendientes]] — lo que bloquea qué fase
- [[08.13 Calendario y Estimativas]] — plazos
- [[10.01 Runbook Operativo]] — para operar el sistema una vez en producción
