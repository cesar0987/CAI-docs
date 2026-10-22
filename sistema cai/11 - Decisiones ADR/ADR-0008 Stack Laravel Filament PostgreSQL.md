---
title: ADR-0008 Stack Laravel Filament PostgreSQL
type: adr
status: aceptado
tags: [cai, adr, stack, laravel, filament, postgresql, arquitectura]
owner: Dirección
updated: 2026-10-22
related:
  - "[[02.01 Arquitectura General]]"
  - "[[02.04 Capas Internas de un Paquete]]"
  - "[[08.02 F0 Cimientos del Entorno]]"
---

# ADR-0008 — Laravel + Filament + PostgreSQL

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-10-22 |
| **Decide** | Dirección, con el Responsable técnico |
| **Alcance** | Stack tecnológico del sistema completo |

---

## 1. Contexto

El centro necesita un sistema de gestión que cubra: alumnos y matrículas,
planificación de atención, seguimiento clínico, agenda, finanzas y
administración. Todo en **un solo sistema**, instalado **en un servidor propio
del centro**, mantenido por **un desarrollador part-time**.

**Restricciones:**

- **Sin dependencias de internet** en el día a día: el servidor es local al
  centro y todo tiene que funcionar sin conexión (ver [[07.01 Arquitectura del Servidor del Centro]]).
- **Un solo desarrollador part-time** (≈ 8 h/semana). El stack tiene que ser
  conocido, estable y con pocas piezas móviles.
- **Un solo servidor** con recursos modestos. No hay cluster, ni balanceador, ni
  réplica.
- **Registro de datos sensibles** (notas clínicas de menores) con necesidades de
  cifrado y auditoría.
- **Usuarios internos con roles heterogéneos**: Recepción, Secretaría,
  Coordinación, Dirección, Administración Financiera, Profesionales, Administración
  Técnica. El sistema no puede exigir perfil técnico a ninguno.
- **Cero dependencias de servicios externos** en el MVP: ni pasarela de pagos,
  ni email transaccional, ni SMS, ni almacenamiento de archivos en la nube.

**Qué sabemos:**

- El volumen de datos es **bajo**: unos 300 alumnos, unos 30 profesionales,
  unas pocos miles de notas clínicas al año. Del orden de miles de filas por
  tabla, no de millones.
- El sistema tiene muchas **pantallas de formularios y listados** con validaciones
  y permisos por fila. Es un sistema CRUD con reglas de negocio, no un producto
  de datos.
- Laravel es **el** framework PHP con el ecosistema más amplio para panel
  administrativo, y Filament construye exactamente ese panel.
- PostgreSQL tiene **esquemas por módulo**, tipos enumerados, restricciones
  `CHECK`, `EXCLUDE`, vistas materializadas y cifrado a nivel de columna con
  `pgcrypto`.

**Qué no sabemos:**

- Si el centro crece, el volumen no va a cambiar el stack.
- Si la Direction exigirá un portal de familias (etapa 2). El stack actual lo
  permite (Laravel tiene su propio sistema de autenticación), pero **no** se
  construye en el MVP (ver [[01.07 Preguntas Abiertas y Decisiones Pendientes]]).

---

## 2. Decisión

**El sistema se construye con PHP 8.3 + Laravel 11 + Filament 3 sobre
PostgreSQL 16, desplegado en el servidor propio del centro. Filament es la única
interfaz del sistema en el MVP: no hay panel de administración propio ni API
pública de consumo masivo.**

En detalle:

### 2.1 La pila

| Capa | Tecnología | Versión | Por qué |
|---|---|---|---|
| Lenguaje | PHP | 8.3 | Tips del lenguaje, enums, readonly, `match`. Extensiones `bcmath` y `gd` son **requisitos**. |
| Framework | Laravel | 11 | Ecosistema, ORM (Eloquent), colas, scheduler, testing (Pest), auth. |
| Panel | Filament | 3 | Panel administrativo con recursos, tablas, formularios, acciones, permisos. Es exactamente lo que el centro necesita. |
| Base de datos | PostgreSQL | 16 | Esquemas por módulo, `CHECK`, `EXCLUDE`, vistas, `pgcrypto`. |
| Cola | `database` | — | Sin Redis ni Horizon en el MVP (ver [[ADR-0009 Sin Redis en el MVP]]). |
| Cache | `file` | — | Sin Redis ni Memcached en el MVP. |
| Sesión | `database` | — | Sin dependencia externa. |
| Build | Vite | — | Solo para los pocos assets propios. |
| Tests | Pest + PHPUnit | — | Sintaxis más legible para las reglas de negocio. |
| Calidad | PHPStan + Pint + Deptrac | — | Análisis estático, estilo, fronteras entre módulos. |

### 2.2 Por qué Filament

Filament resuelve, de fábrica, lo que un sistema de gestión de un centro
necesita:

| Necesidad | Cómo la resuelve Filament |
|---|---|
| Listados con búsqueda, filtros y paginación | `Table` con `filters`, `search`, `sortable` |
| Formularios con validación | `Form` con `->rules()` |
| Acciones sobre registros (anular, confirmar, imprimir) | `Action` con `->requiresConfirmation()` |
| Menú por rol | `->visibleTo()` y la integración con `spatie/laravel-permission` |
| Notificaciones al usuario | `Notification` de Filament |
| Dashboard por rol | `Widget` con `->visibleTo()` |
| Impresión de documentos | Action que genera un PDF |
| Auditoría de acciones | Hooks de acciones + `security_events` |

> [!important] Filament es la interfaz, no el modelo de negocio
> Filament vive **dentro del paquete de dominio** o en un paquete de interfaz
> dedicado, pero **nunca** contiene reglas de negocio. La lógica vive en
> acciones (`Actions/`) y en el modelo, y se puede probar sin levantar la
> interfaz. Un Filament que funciona es un panel; un Filament que además
> contiene el negocio es un sistema que no se puede mantener.

### 2.3 Por qué PostgreSQL y no MySQL

| Capacidad | PostgreSQL | MySQL |
|---|---|---|
| **Esquemas por módulo** (ver [[ADR-0002 Schema por Módulo en PostgreSQL]]) | ✅ Nativo, con `search_path` | ❌ Un schema = una base de datos |
| Restricciones `CHECK` | ✅ | ⚠️ Recién añadida (8.0.16) |
| `EXCLUDE` con `btree_gist` (solapamiento de horarios) | ✅ | ❌ No existe |
| `NUMERIC` con precisión arbitraria | ✅ Exacto | ⚠️ `DECIMAL` sí, pero con matices |
| `JSONB` indexado | ✅ | ⚠️ `JSON` sin indexado directo |
| Cifrado a nivel de columna (`pgcrypto`) | ✅ | ❌ No existe |
| Tipos enumerados y dominios | ✅ | ❌ No existen |
| Vistas materializadas | ✅ | ❌ (no materializadas) |
| CTEs recursivas y `LATERAL` | ✅ | ✅ |

> [!danger] Los tres puntos que no son negociables
> 1. **Esquemas por módulo**: sin ellos, la modularidad es solo de carpetas.
> 2. **`EXCLUDE`**: sin él, el solapamiento de horarios de la agenda se controla
    solo en la aplicación, y un `UPDATE` directo a la base rompe el sistema.
> 3. **Restricciones `CHECK`**: el saldo, los estados y los importes tienen que
>    estar garantizados **por la base**, no solo por la aplicación.

### 2.4 Por qué Laravel y no un framework de otro tipo

| Necesidad | Laravel lo resuelve |
|---|---|
| Panel administrativo completo | Filament |
| Sistema de archivos, colas, eventos, notificaciones | Incluidos y bien documentados |
| Autenticación y autorización | `spatie/laravel-permission` + Policies nativas |
| Migraciones versionadas | Incluidas |
| Pruebas | Pest / PHPUnit / Laravel Dusk para la interfaz |
| Despliegue simple | Un `artisan migrate` y un symlink (ver [[ADR-0005 Release por Symlink]]) |
| Ecosistema en español | Amplio, con documentación y comunidad |

### 2.5 Lo que NO incluye el MVP

| Excluido | Motivo | Cuándo |
|---|---|---|
| **Next.js / portal de familias** | Requisito de la etapa 2. Añadirlo ahora duplica el trabajo de autenticación y de permisos. | Etapa 2 |
| **API pública REST** | Nadie la consume. Se documenta por la vía interna cuando haga falta. | Cuando sea necesario |
| **Redis / Memcached** | Volumen bajo. La cola y la caché en base de datos son suficientes. | Ver [[ADR-0009 Sin Redis en el MVP]] |
| **Microservicios / API gateway** | Un solo servidor. Un solo dev. | No previsto |
| **Email transaccional** | El centro no tiene servicio de correo con dominio propio, y el MVP imprime. | Cuando se defina |
| **Pasarela de pagos** | El centro cobra en ventanilla, en efectivo o por transferencia. | Cuando se defina |

---

## 3. Alternativas consideradas

### 3.1 Laravel + Filament + MySQL/MariaDB

| Aspecto | Detalle |
|---|---|
| **Descripción** | Lo mismo, pero con MySQL. |
| **Ventajas** | Más familiar para algunos administradores. Hospedaje barato. |
| **Desventajas** | Sin esquemas por módulo (la modularidad se vuelve de carpetas). Sin `EXCLUDE`. Sin `CHECK` confiable en versiones antiguas. |
| **Por qué se descartó** | La modularidad es un **requisito** del proyecto, no una preferencia. Y las restricciones de la base (CHECK, EXCLUDE, NUMERIC exacto) son la barrera que protege el dinero y las agendas. MySQL no las da. |

### 3.2 Django + Django admin

| Aspecto | Detalle |
|---|---|
| **Descripción** | Python, Django, su panel de administración nativo y Django REST Framework. |
| **Ventajas** | Panel administrativo incluido.ORM excelente. Sistema de permisos nativo. |
| **Desventajas** | El panel nativo es **básico**: filtros y formularios limitados frente a Filament. Para cubrir un sistema con agenda, wizards e impresión hay que construir mucho a mano. |
| **Por qué se descartó** | Filament da el 80 % de un panel moderno. Django admin da el 40 %, y el 60 % restante es trabajo que alguien tiene que escribir y mantener. |

### 3.3 NestJS / Next.js + PostgreSQL (API + SPA)

| Aspecto | Detalle |
|---|---|
| **Descripción** | Backend en Node/TypeScript, panel en React (Next.js), PostgreSQL como base. |
| **Ventajas** | TypeScript de punta a punta. Ecosistema moderno. El portal de familias sería natural en el mismo stack. |
| **Desventajas** | Dos stacks (front y back), dos procesos en el servidor, doble complejidad de despliegue. TypeORM/Prisma con esquemas por módulo es frágil. Mucho código repetitivo de formularios. |
| **Por qué se descartó** | El servidor del centro tiene que ser **simple de operar** por una persona que no es desarrolladora. Dos stacks es el doble de superficie. Y el volumen de la interfaz es CRUD administrativo, donde Filament ya está resuelto. |

### 3.4 WordPress / Drupal con módulos a medida

| Aspecto | Detalle |
|---|---|
| **Descripción** | CMS como base, con módulos personalizados para alumnos, agenda y finanzas. |
| **Ventajas** | Panel listo. Gestión de contenido lista. |
| **Desventajas** | Los datos de negocio (cargos, imputaciones, notas clínicas, reglas de agenda) quedan en un modelo genérico de contenido o en tablas a medida. No hay tipado, ni restricciones, ni transacciones de negocio limpias. La lógica de negocio queda en hooks. |
| **Por qué se descartar** | Un CMS resuelve edición de contenido. Este sistema es **gestión de datos de negocio con reglas**. Meter un ER con 9 schemas y controles de concurrencia dentro de un CMS es pelear contra la herramienta. |

### 3.5 Low-code / Google Apps Script / Airtable

| Aspecto | Detalle |
|---|---|
| **Descripción** | Construir el sistema con una herramienta sin código. |
| **Ventajas** | Rapidez inicial. Sin servidor. |
| **Desventajas** | Sin control sobre los datos. Sin auditoría real. Sin cifrado de columna. Sin concurrencia segura. Dependencia de un proveedor externo (contradice el servidor propio). |
| **Por qué se descartó** | Contradice la decisión D0 (servidor propio, sin internet) y los requisitos de datos clínicos. |

### 3.6 Paquete de gestión escolar de terceros (base lista para usar)

| Aspecto | Detalle |
|---|---|
| **Descripción** | Usar un paquete de gestión escolar listo para usar. |
| **Ventajas** | Arranque rápido. |
| **Desventajas** | El modelo de datos, los permisos y las reglas son **ajenos** al centro. Adaptarlos suele costar más que construirlos. No hay soporte ni control sobre lo que contiene. Y en el caso clínico, "listo para usar" casi nunca significa "cumple lo que exigimos". |
| **Por qué se descartó** | Este sistema tiene reglas que **no son estándar**: cuenta familiar compartida con imputación, notas clínicas cifradas con grants de acceso, planes de atención por alumno. Ningún paquete las trae. |

---

## 4. Consecuencias

### 4.1 Positivas

- **Un solo stack, un solo lenguaje**: el dev trabaja en PHP de punta a punta.
- **Filament acelera el desarrollo del panel** sin sacrificar la separación de
  la lógica de negocio.
- **PostgreSQL garantiza las reglas de integridad** que el negocio necesita
  (importes, estados, no solapamiento de horarios).
- **La modularidad es real**: paquetes Composer por dominio, con fronteras
  verificadas por Deptrac y por pruebas de arquitectura (ver [[02.03 Reglas de Frontera entre Módulos]]).
- **Despliegue simple**: un `artisan migrate`, un symlink, un healthcheck.
- **Ecosistema conocido**: si el dev falta, hay mucha gente que puede leer el
  código.
- **Todo el stack funciona sin internet**, salvo la descarga inicial de
  dependencias.

### 4.2 Negativas (lo que aceptamos)

- **PHP no es un lenguaje con tipado estático completo.** Se compensa con
  PHPStan en nivel máximo, `strict_types` en todos los archivos y tipos
  declarados en las firmas.
- **Filament impone su propia forma de hacer las cosas.** Hay que aprender sus
  conceptos (Resources, Pages, Actions, Widgets, Notifications) y aceptar que
  para cosas muy especiales hay que salirse del molde.
- **Las extensiones del servidor son una dependencia real**: `bcmath` y `gd`
  **no** están instaladas en el entorno verificado y hacen falta para los casts
  `decimal` y para el procesamiento de imágenes (P12, P13).
- **Eloquent es un ORM con costes**: N+1 y consultas implícitas. Se mitiga con
  `preventLazyLoading` en desarrollo y con pruebas que detecten el problema.
- **Laravel tiene muchas dependencias**: un `composer audit` hay que correrlo
  periódicamente.
- **El panel de Filament es de escritorio primero.** En un teléfono se usa,
  pero no está diseñado para eso. El MVP asume uso en computadoras de escritorio.
- **Sin Next.js, el portal de familias (etapa 2) habrá que construirlo aparte.**
  Es una decisión consciente: es mejor no hacerlo que hacerlo a medias.

### 4.3 Neutras

- El hecho de usar Filament **no** implica que la base de datos sea de Filament.
  Los modelos de negocio son Eloquent propio, en los paquetes de dominio.
- Laravel se despliega con `artisan serve` **solo** en desarrollo. En producción,
  Nginx + PHP-FPM (ver [[07.02 Requisitos de Hardware y Software]]).

---

## 5. Verificación

```text
☐ PHP 8.3 con `bcmath` y `gd` instaladas en el servidor de producción
☐ `composer create-project` arranca y `php artisan about` funciona
☐ Filament se instala y un superusuario puede entrar al panel
☐ Un recurso de prueba (listado + formulario + acción) funciona con permisos
☐ PostgreSQL 16 con `pgcrypto` y `btree_gist` disponibles
☐ Se puede crear un schema por módulo y `search_path` funciona (ver ADR-0002)
☐ Una restricción `CHECK` y una `EXCLUDE` funcionan sobre tablas de prueba
☐ `php artisan test` corre la suite en menos de 2 minutos
☐ PHPStan nivel máximo pasa sin errores
☐ Deptrac no reporta violaciones de frontera
☐ `composer audit` no reporta vulnerabilidades conocidas altas
☐ La aplicación responde con `search_path` configurado y sin internet
```

---

## 6. Reversibilidad

| Aspecto | Detalle |
|---|---|
| **¿Se puede revertir?** | Muy difícil |
| **Cómo** | Teóricamente se puede reescribir el sistema en otro stack. En la práctica, es reescribirlo todo. |
| **Costo de revertir** | Muy alto. |
| **Mitigación** | El **modelo de datos** es la parte más difícil de migrar, y ese es independiente del framework. [[02.05 Esquema de Base de Datos por Módulo]] documenta el modelo por separado, con SQL, para que no quede atado a Laravel. |
| **Señal de que hay que revertir** | El único escenario realista: que el centro requiere una funcionalidad que el stack no puede dar de forma razonable **y** hay presupuesto para una reescritura. Nada de eso está en el horizonte. |

---

## 7. Referencias

- [[02.01 Arquitectura General]]
- [[02.04 Capas Internas de un Paquete]]
- [[02.03 Reglas de Frontera entre Módulos]]
- [[02.05 Esquema de Base de Datos por Módulo]]
- [[07.02 Requisitos de Hardware y Software]]
- [[08.02 F0 Cimientos del Entorno]]
- [[ADR-0002 Schema por Módulo en PostgreSQL]]
- [[ADR-0009 Sin Redis en el MVP]]
