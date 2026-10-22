---
title: ADR-0001 Monolito Modular en Paquetes
type: adr
status: aceptado
tags: [cai, adr, arquitectura, modularidad, composer, paquetes]
owner: Responsable técnico
updated: 2026-10-22
related:
  - "[[02.02 Arquitectura Modular en Paquetes]]"
  - "[[02.03 Reglas de Frontera entre Módulos]]"
  - "[[08.03 F1 Andamiaje Técnico y Frontera Modular]]"
---

# ADR-0001 — Monolito modular en paquetes Composer

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-10-22 |
| **Decide** | Responsable técnico |
| **Alcance** | Estructura del repositorio, reglas de dependencia entre módulos |

---

## 1. Contexto

El sistema tiene nueve dominios de datos con reglas de acceso distintas: identidad,
alumnos, agenda, clínico, financiero, documentos, notificaciones y reportes.

La separación entre ellos es una **necesidad de seguridad**, no una preferencia
estética: el profesional no debe poder leer datos financieros, Finanzas no debe poder
leer notas clínicas, el Administrador Técnico no debe poder leer ninguna de las dos.

**Restricciones:**
- Un solo servidor, un solo despliegue, un solo desarrollador part-time.
- Presupuesto de infraestructura esencialmente nulo.
- El proyecto debe poder abandonarse sin dejar un sistema huérfano que nadie
  entiende.

**Qué sabemos:**
- La complejidad real del dominio justifica separación.
- El equipo es de **una** persona: cada artefacto extra tiene un costo real.
- Los frameworks PHP modernos (Laravel) ya resuelven gran parte de lo que motivaría
  a un microservicio.

**Qué no sabemos:**
- Cuánto va a crecer el sistema.
- Si el centro va a necesitar otras sedes con otros sistemas.
- Si en dos años va a haber un segundo desarrollador.

---

## 2. Decisión

**Organizamos el sistema como un monolito modular: una única aplicación y una única
base de datos, con el código agrupado en paquetes Composer independientes, uno por
dominio, y con las dependencias entre dominios declaradas y verificadas
automáticamente.**

En detalle:

- **Nueve paquetes** en `packages/`, cada uno con su `composer.json`:
  `cai/core`, `cai/identity`, `cai/students`, `cai/scheduling`, `cai/care`,
  `cai/billing`, `cai/documents`, `cai/notifications`, `cai/reporting`.
- **Cada paquete expone contratos** (interfaces) como su API pública. Un paquete no
  accede a las clases internas de otro: accede a sus contratos.
- **Las dependencias entre paquetes están declaradas** en `composer.json` y en
  `deptrac.yaml`.
- **La CI falla** si un PR viola la frontera.
- **Cada paquete tiene sus propias migraciones**, con su propio esquema de base de
  datos (ver [[ADR-0002 Schema por Módulo en PostgreSQL]]).

---

## 3. Alternativas consideradas

### 3.1 Carpeta por dominio en `app/`

| Aspecto | Detalle |
|---|---|
| **Descripción** | `app/Alumnos/`, `app/Agenda/`, `app/Clinico/`, etc. Un solo `composer.json`. |
| **Ventajas** | Cero ceremonia. Autocompletado fácil. Migraciones en un solo lugar. |
| **Desventajas** | Nada impide que `app/Clinico/` importe `app/Finanzas/`. La frontera es una convención, no una regla. |
| **Por qué se descartó** | La frontera de seguridad **necesita** ser verificable, no nominal. Una convención que depende de que todos se acuerden es una convención que se rompe la primera vez que hay prisa. |

### 3.2 Microservicios

| Aspecto | Detalle |
|---|---|
| **Descripción** | Un servicio por dominio, con API HTTP entre ellos, base de datos por servicio. |
| **Ventajas** | Aislamiento máximo. Despliegue independiente. Escalado independiente. |
| **Desventajas** | Red de Observabilidad, despliegue, manejo de fallos distribuidos, transactions distribuidas, debugging distribuido. |
| **Por qué se descartó** | Con un servidor y un dev part-time, el costo operativo supera con creces el beneficio. Un microservicio que nadie puede monitorear es peor que un monolito. |

### 3.3 Modularidad dentro de `app/Domain/`

| Aspecto | Detalle |
|---|---|
| **Descripción** | Una sola aplicación con `app/Domain/Alumnos/`, `app/Domain/Clinico/`, etc., y una regla de dependencias por capa. |
| **Ventajas** | Separa el dominio de la infraestructura. Menos ceremonia que un paquete. |
| **Desventajas** | Sigue siendo un solo `composer.json`: los `use` entre dominios siguen siendo legales. |
| **Por qué se descartó** | Es el punto medio sin la propiedad que importa: la **frontera verificable**. |

---

## 4. Consecuencias

### 4.1 Positivas

- La frontera entre dominios es **verificable por la CI**, no por goodwill.
- Cada módulo se puede **extraer** a un servicio real más adelante, si hace falta,
  porque ya vive detrás de contratos.
- El concepto de "propiedad" queda explícito: cada paquete tiene su esquema, sus
  migraciones, sus tests y su documentación.
- Los tests de arquitectura (`arch tests`) verifican las reglas que un reviewer
  dejaría pasar.

### 4.2 Negativas (lo que aceptamos)

- **Ceremonia real**: cada paquete tiene su `composer.json`, su `ServiceProvider`,
  sus `composer.json` con `repositories` de tipo `path`. Hay que actualizar varios
  archivos para un cambio de API.
- **Los contratos hay que mantenerlos**: un contrato que cambia obliga a tocar todos
  los consumidores a la vez.
- **El autoload de Composer puede desincronizarse** si se edita un `composer.json` sin
  correr `composer dump-autoload`.
- **Un solo `vendor/`**: todos los paquetes comparten dependencias. Si dos paquetes
  quieren versiones distintas de la misma librería, hay que resolverlo.
- **El IDE indexa peor** que con un solo `app/`: el autoload de paquetes con
  `repositories: path` requiere `composer dump-autoload` para que el IDE los vea.
- **El `composer install` de producción es más lento** (por eso se usa
  `COMPOSER_MIRROR_PATH_REPOS=1`).

### 4.3 Neutras

- El sistema sigue siendo **una sola aplicación y un solo despliegue**: no cambia la
  operación para el centro.
- La separación es **lógica antes que física**: los paquetes viven en el mismo
  repositorio y se despliegan juntos.

---

## 5. Verificación

```text
☐ La CI corre `deptrac analyse` y falla si una dependencia entre paquetes no está declarada
☐ Existe un arch test que verifica que el paquete X no importa clases internas de Y
☐ `composer validate` pasa en todos los paquetes
☐ Un PR de ejemplo que viola la frontera se verificó que FALLA la CI
☐ `composer install` funciona en una máquina limpia
☐ La documentación de cada paquete describe su API pública (los contratos)
```

> [!important] La verificación que de verdad importa
> **Que un PR que viola la frontera falle la CI.** Si eso no está probado con un caso
> real, la frontera es teórica. Ese es el criterio de salida de F1.

---

## 6. Reversibilidad

| Aspecto | Detalle |
|---|---|
| **¿Se puede revertir?** | Sí, parcialmente |
| **Cómo** | Fusionar los paquetes en `app/` manteniendo los directorios. Los contratos se convierten en interfaces dentro del mismo namespace. |
| **Costo de revertir** | Medio. Se pierde el aislamiento del autoload; la verificación por CI pasa a depender de `arch tests` solamente. |
| **Señal de que hay que revertir** | Si la ceremonia de empaquetado (actualizar N `composer.json`) consume más tiempo que el beneficio del aislamiento. **Regla definida: no crear un paquete nuevo hasta que un módulo tenga ≥ 3 clases y un consumidor real.** |

---

## 7. Referencias

- [[02.02 Arquitectura Modular en Paquetes]]
- [[02.03 Reglas de Frontera entre Módulos]]
- [[02.04 Capas Internas de un Paquete]]
- [[08.03 F1 Andamiaje Técnico y Frontera Modular]]
- [[00.03 Stack, Versiones y Dependencias]]
