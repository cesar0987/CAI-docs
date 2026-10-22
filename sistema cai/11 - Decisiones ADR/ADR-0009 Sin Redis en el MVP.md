---
title: ADR-0009 Sin Redis en el MVP
type: adr
status: aceptado
tags: [cai, adr, infraestructura, redis, cola, cache, bajo-costo]
owner: Responsable técnico
updated: 2026-10-22
related:
  - "[[00.03 Stack, Versiones y Dependencias]]"
  - "[[07.01 Arquitectura del Servidor del Centro]]"
  - "[[08.12 Backlog Maestro]]"
---

# ADR-0009 — Cola y caché sobre el driver `database`, sin Redis

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-10-22 |
| **Decide** | Responsable técnico, con Dirección (P10) |
| **Alcance** | Infraestructura del servidor, cola de trabajos, caché y sesiones |

---

## 1. Contexto

El sistema necesita:

- **Cola de trabajos** para enviar notificaciones, generar documentos, importar
  datos y ejecutar tareas programadas.
- **Caché** para no recalcular listados pesados ni repetir consultas en la
  pantalla.
- **Sesiones** de usuario autenticado.

**Restricciones:**

- El servidor es **propio del centro**, con recursos modestos y **sin
  redundancia** (ver [[07.01 Arquitectura del Servidor del Centro]]).
- El mantenimiento lo hace **una persona part-time** que además es el
  desarrollador. Cada servicio que corre en el servidor es un servicio que hay
  que recordar reiniciar, actualizar y respaldar.
- La decisión D0 es **independencia de internet**: nada puede requerir un
  servicio externo.
- La extensión `ext-redis` **no está instalada** en el entorno verificado, y su
  instalación requiere privilegios de `root` en el servidor (P13).
- El volumen de trabajo es **bajo**: unos 300 alumnos, notificaciones
  puntuales, importaciones esporádicas y un cron cada minuto.

**Qué sabemos:**

- El driver `database` de Laravel es **suficiente** para el volumen esperado: la
  tabla `jobs` con `SELECT ... FOR UPDATE SKIP LOCKED` es un patrón maduro.
- Redis aporta tres cosas que el driver `database` no da: **velocidad**,
  **persistencia separada** y **estructuras** (colas, locks, pub/sub). Con este
  volumen, las dos primeras no se notan.
- El caché `file` es suficiente para lo que se cachea, y no introduce un
  proceso más.

**Qué no sabemos:**

- Si el MVP se extiende con el portal de familias (etapa 2) y notificaciones
  masivas, el volumen de cola puede crecer. Está en el backlog como ítem a
  reevaluar (D-05).

---

## 2. Decisión

**No instalamos Redis. La cola usa el driver `database`, el caché usa el driver
`file` y las sesiones usan el driver `database`. No hay ningún servicio
adicional que dependa de Redis: si mañana Redis no existiera, el sistema
seguiría funcionando completo.**

En detalle:

### 2.1 La configuración

| Componente | Driver | Por qué |
|---|---|---|
| `QUEUE_CONNECTION` | `database` | Volumen bajo. Una tabla `jobs` con `SKIP LOCKED`. |
| `CACHE_STORE` | `file` | El caché son datos regenerables. No necesita estar en la base. |
| `SESSION_DRIVER` | `database` | Permite invalidar sesiones y auditar sesiones activas. |
| `BROADCAST_CONNECTION` | `null` | No hay websockets en el MVP. |
| `REDIS_HOST` | — | **No existe.** No se configura. |

```dotenv
# .env de producción
QUEUE_CONNECTION=database
CACHE_STORE=file
SESSION_DRIVER=database
SESSION_LIFETIME=120
```

> [!important] La regla de no configurar Redis
> Si `REDIS_HOST` no existe en el `.env`, es **imposible** que una parte del
> sistema dependa de Redis por accidente. La ausencia de la variable es la
> barrera, no un recordatorio en un documento.

### 2.2 Cómo funciona la cola con `database`

```text
1. El código encola un job → INSERT en la tabla jobs
2. El worker (php artisan queue:work) toma el job más antiguo
3. Lo bloquea con SELECT ... FOR UPDATE SKIP LOCKED
4. Lo ejecuta
5. Si tiene éxito → DELETE
6. Si falla → failed_jobs (con el motivo y el rastro)
7. Si agotó los reintentos → failed_jobs
```

| Aspecto | Valor |
|---|---|
| **Worker** | `php artisan queue:work --tries=3 --backoff=60 --max-time=3600` |
| **Supervisión** | `supervisor` (ya previsto en [[07.01 Arquitectura del Servidor del Centro]]) |
| **Reintentos** | 3, con espera creciente (60 s, 120 s, 300 s) |
| **Jobs fallidos** | Tabla `failed_jobs` + alerta en el panel |
| **Reinicio tras despliegue** | `php artisan queue:restart` (ver [[ADR-0005 Release por Symlink]]) |
| **Programados** | `php artisan schedule:run` cada minuto (cron) |

### 2.3 La caché en archivo

```dotenv
CACHE_STORE=file
```

| Aspecto | Detalle |
|---|---|
| **Ubicación** | `shared/storage/framework/cache/data` (sobrevive a los despliegues) |
| **Limpieza** | `php artisan cache:clear` en la verificación de salud del deploy |
| **TTL por defecto** | 300 s (5 minutos) para listados |
| **Qué NO se cachea** | Saldos financieros, datos clínicos, agenda del día |

> [!danger] Lo que no se cachea, y por qué
> Un saldo cacheado que no se refresca es un saldo que se le dice a una familia
> que no es real. Una nota clínica cacheada en un archivo en disco es una nota
> clínica que sale del perímetro del cifrado. La agenda del día cambia con
> frecuencia y una versión cacheada muestra huecos que ya no existen.
>
> **La caché es solo para lo que se puede recalcular sin consecuencias.**

### 2.4 El coste real

| Concepto | Con Redis | Sin Redis |
|---|---|---|
| Servicios que hay que operar | 2 (app + Redis) | 1 (app) |
| Memoria del servidor | +50 a 100 MB | 0 |
| Extensión PHP | `ext-redis` o `predis` | ninguna |
| Reinicio del servicio de caché | Sí (pérdida de caché) | No |
| Persistencia de la cola | Separada | En la misma base (y en el backup) |
| Latencia en el peor caso | ~1 ms | ~10 ms |

A este volumen, la última fila es **irrelevante**: ninguna acción del sistema
necesita menos de 100 ms.

---

## 3. Alternativas consideradas

### 3.1 Redis + Horizon

| Aspecto | Detalle |
|---|---|
| **Descripción** | Redis como cola, caché y locks, con Horizon como supervisor de workers. |
| **Ventajas** | Cola rápida. Locks atómicos. Métricas de Horizon. Vistas en vivo. |
| **Desventajas** | Un servicio más (que hay que instalar, configurar, respaldar, monitorear y reiniciar). Extensión `ext-redis` que **no está instalada**. Horizon añade su propia configuración y su propio formato de logs. |
| **Por qué se descartó** | Se paga el coste operativo completo a cambio de una latencia que este sistema no nota. El beneficio real de Redis —locks, colas de alto volumen, pub/sub— no aparece en el alcance del MVP. |

### 3.2 Memcached

| Aspecto | Detalle |
|---|---|
| **Descripción** | Solo para caché, manteniendo la cola en base de datos. |
| **Ventajas** | Más simple que Redis para un solo uso. |
| **Desventajas** | Sigue siendo un servicio más, con la misma extensión que instalar. No aporta nada que el driver `file` no cubra a este volumen. |
| **Por qué se descartó** | Un servicio más para cachear la misma información que ya se puede regenerar. |

### 3.3 Todo en `database` (cola, caché y sesiones)

| Aspecto | Detalle |
|---|---|
| **Descripción** | Usar el driver `database` también para el caché. |
| **Ventajas** | Una sola opción en toda la configuración. La caché se sobrevive a los despliegues sin esfuerzo. |
| **Desventajas** | La caché va a la base de datos y **contamina** las tablas con miles de filas de datos regenerables. La tabla `cache` crece. |
| **Por qué se descartó** | Es **válido** y sería una decisión defendible. Se descarta solo porque el driver `file` separa mejor lo desechable de lo importante: un `truncate` de la caché no toca la base de datos. **Queda como la opción de repliegue si el caché en archivo da problemas.** |

### 3.4 Cola sin workers (solo cron)

| Aspecto | Detalle |
|---|---|
| **Descripción** | No usar cola. Todo se ejecuta en el scheduler cada minuto, o de forma síncrona. |
| **Ventajas** | Cero infraestructura de cola. Cero workers. Nada que reiniciar. |
| **Desventajas** | Los trabajos se ejecutan **en el contexto de la petición web** o del cron: un trabajo lento (importar 300 alumnos, generar 300 recibos) bloquea la web o el cron. Sin reintentos automáticos. Sin `failed_jobs`. |
| **Por qué se descartó** | Es la opción más simple, pero no escala ni en manejo de errores. El sistema tiene importaciones masivas de datos iniciales (ver [[09.07 Importación de Datos Iniciales]]), y esas **no pueden** ejecutarse en el ciclo de una petición web. La cola existe para eso. |

### 3.5 SQLite

| Aspecto | Detalle |
|---|---|
| **Descripción** | Usar SQLite como base de datos, sin servidor de base de datos. |
| **Ventajas** | Cero servicios. Una sola dependencia. |
| **Desventajas** | **Sin concurrencia de escritura** (un escritor a la vez). Sin `CHECK` útil, sin `EXCLUDE`, sin esquemas, sin `JSONB`, sin cifrado por columna. Un sistema con agenda, finanzas y acceso simultáneo de muchas personas **no puede** funcionar sobre SQLite. |
| **Por qué se descartó** | Es la decisión que invalida toda la arquitectura modular por esquema. No es una alternativa menor. |

---

## 4. Consecuencias

### 4.1 Positivas

- **Un solo servicio que operar** en el servidor. Menos superficie de fallo, menos
  respaldos, menos "se cayó Redis".
- **No hay nada nuevo que instalar** que requiera `root` (P13 deja de ser
  bloqueante para el sistema).
- **La cola está respaldada** junto con el resto de la base de datos: si se
  pierde el servidor, los jobs pendientes se recuperan con el restore.
- **El caché no contiene datos sensibles**: está en archivo, sin cifrar, y por
  diseño solo guarda datos regenerables.
- **El sistema tiene menos puntos de fallo**: menos componentes significa menos
  modos de falla que documentar en [[10.03 Gestión de Incidentes]].

### 4.2 Negativas (lo que aceptamos)

- **La cola en base de datos escala peor.** Con miles de jobs pendientes, la
  tabla `jobs` crece y el `SELECT` del worker la recorre. A este volumen no
  pasa. Si pasa, es la señal para cambiar (D-05 en el backlog).
- **No hay locks distribuidos.** Las operaciones concurrentes se resuelven con
  bloqueos de fila de PostgreSQL (`SELECT ... FOR UPDATE`), que son mejores
  que un lock de Redis porque están en la misma transacción.
- **No hay pub/sub**: los eventos en vivo se resuelven con polling desde el
  navegador o con la recarga de la página. En el MVP no hace falta.
- **El caché en archivo no se comparte** entre procesos. Con PHP-FPM y un solo
  servidor, no hace falta.
- **Cambiar a Redis más adelante es un cambio de configuración**, no una
  reescritura: `QUEUE_CONNECTION=redis`, `CACHE_STORE=redis` y un servicio más.
  La aplicación no cambia.
- **La fila `failed_jobs` hay que mirarla.** Sin Redis no hay Horizon que
  avise: hay que tener una verificación programada que avise si la tabla no está
  vacía (ver [[10.02 Calendario de Checklists]]).

### 4.3 Neutras

- El driver `database` **es** el mecanismo estándar de Laravel. No es una
  solución artesanal: es una opción soportada de primera clase.
- La extensión `ext-redis` que falta en el entorno verificado deja de ser un
  problema. Se documenta su ausencia como **coherente con la decisión**, no
  como un faltante.

---

## 5. Verificación

```text
☐ `REDIS_HOST` no existe en el `.env` de producción
☐ `php artisan queue:work` corre y procesa un job de prueba
☐ Un job que falla 3 veces queda en `failed_jobs` con su motivo
☐ `php artisan queue:restart` reinicia los workers tras un despliegue
☐ El scheduler corre cada minuto (cron) y dispara las tareas programadas
☐ El caché se invalida con TTL sin dejar filas basura en la base
☐ La tabla `jobs` está vacía en horario de baja actividad
☐ La tabla `failed_jobs` se revisa en la verificación diaria
☐ El sistema funciona completo con el servicio de Redis apagado (o inexistente)
☐ El backup de la base incluye la tabla `jobs`
```

---

## 6. Reversibilidad

| Aspecto | Detalle |
|---|---|
| **¿Se puede revertir?** | Sí, muy fácilmente |
| **Cómo** | `QUEUE_CONNECTION=redis`, `CACHE_STORE=redis`, instalar Redis, `predis` o `ext-redis`, `queue:restart`. **El código de la aplicación no cambia.** |
| **Costo de revertir** | Bajo. Una tarde de trabajo, más el coste operativo recurrente. |
| **Señal de que hay que revertir** | La tabla `jobs` tiene más de unos miles de filas pendientes de forma sostenida, o el tiempo de espera de una notificación supera el aceptable para el centro. |

---

## 7. Referencias

- [[00.03 Stack, Versiones y Dependencias]]
- [[07.01 Arquitectura del Servidor del Centro]]
- [[07.01 Arquitectura del Servidor del Centro]]
- [[08.12 Backlog Maestro]]
- [[10.02 Calendario de Checklists]]
- [[09.07 Importación de Datos Iniciales]]
