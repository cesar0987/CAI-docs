---
title: ADR-0005 Release por Symlink
type: adr
status: aceptado
tags: [cai, adr, despliegue, release, symlink, servidor, rollback]
owner: Responsable técnico
updated: 2026-10-22
related:
  - "[[06.05 Release y Deploy]]"
  - "[[06.06 Procedimiento de Rollback]]"
  - "[[07.03 Instalación del Sistema]]"
---

# ADR-0005 — Despliegue por symlink `current`

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-10-22 |
| **Decide** | Responsable técnico |
| **Alcance** | Procedimiento de despliegue en el servidor del centro |

---

## 1. Contexto

El sistema corre en **un solo servidor** del centro, sin alta disponibilidad y sin
intervenciones de internet (ver [[07.01 Arquitectura del Servidor del Centro]]).

Necesitamos un despliegue que:

- Sea **reversible en menos de un minuto** (es el nivel 2 de los 4 niveles de
  rollback definidos en [[06.06 Procedimiento de Rollback]]).
- **No deje el sistema sin responder** mientras se copia la versión nueva.
- Pueda hacerlo el **Administrador Técnico** sin ser un desarrollador.
- Sea **auditable**: hay que poder responder "qué versión está desplegada y desde
  cuándo".

**Restricciones:**
- Un solo servidor, con recursos modestos (el plan es de ~8 GB de RAM).
- El servidor es **local al centro**: si hay que resolverlo por internet, la
  operación se cae cuando no hay internet.
- El despliegue tiene que ser **scriptable**, no una secuencia de comandos que hay
  que recordar.
- El `storage/` y el `.env` **no** pueden cambiar con cada release: contienen
  archivos subidos, logs y la configuración con la `APP_KEY`.

**Qué sabemos:**
- El patrón *symlink + release* (`capistrano`-like) es el estándar para despliegues
  PHP desde hace más de una década.
- El rollback con symlink es **atómico**: cambiar el enlace y cambiar el código.
- Git en el servidor añade una dependencia de red si el repositorio es remoto.

---

## 2. Decisión

**Cada release se despliega en un directorio versionado bajo `releases/`, y el
directorio activo se señala con el symlink `current`. El rollback es cambiar el
symlink `current` a un release anterior. Un symlink `previous` apunta al release
anterior para que el rollback sea de un solo comando.**

En detalle:

### 2.1 La estructura en el servidor

```text
/srv/cai/
├── current → releases/2026-10-22-1200-abc1234    (symlink ACTIVO)
├── previous → releases/2026-10-15-0900-def5678   (symlink ANTERIOR)
├── releases/
│   ├── 2026-10-15-0900-def5678/
│   ├── 2026-10-20-1400-aaa1111/
│   └── 2026-10-22-1200-abc1234/
├── shared/                     ← NUNCA se toca en un deploy
│   ├── .env                    ← configuración (con APP_KEY)
│   ├── storage/
│   │   ├── app/                ← archivos subidos
│   │   ├── framework/
│   │   │   ├── cache/
│   │   │   ├── sessions/
│   │   │   └── views/
│   │   └── logs/
│   └── node_modules/
└── scripts/
    ├── release.sh              ← deploy y rollback
    ├── status.sh               ← qué versión está activa
    ├── healthcheck.sh          ← verificación
    ├── backup.sh
    └── prune-releases.sh
```

### 2.2 Las propiedades que hacen que esto funcione

| Propiedad | Cómo se logra |
|---|---|
| **Atomicidad** | Cambiar un symlink es una operación atómica del sistema de archivos. No hay un momento en que "el sistema está a medio deploy". |
| **Reversión instantánea** | `ln -sfn releases/XXX current` y un `php artisan queue:restart`. Segundos. |
| **Aislamiento del estado** | `storage/` y `.env` viven en `shared/` y se **enlazan** (symlink) en cada release. Sobreviven a los deploys. |
| **Reproducibilidad** | Cada release es un directorio inmutable. Se puede volver a él en cualquier momento. |
| **Auditoría** | El nombre del directorio tiene fecha y versión. `readlink current` responde "¿qué está desplegado?". |

### 2.3 El flujo de deploy

```text
1. Verificar que la CI está verde
2. Verificar que hay un backup de hoy
3. Crear releases/{fecha}-{hora}-{version}/
4. Copiar los archivos desde el tag (git clone --depth 1 --branch <tag>)
5. Enlazar shared/storage y shared/.env
6. composer install --no-dev --optimize-autoloader --no-scripts
7. php artisan migrate --force
8. php artisan config:cache && route:cache && view:cache
9. php artisan queue:restart
10. Cambiar current → el nuevo release
11. Cambiar previous → el release anterior
12. Ejecutar healthcheck
13. Si falla: rollback automático
```

> [!danger] El paso 12 no es opcional
> Un deploy sin verificación automática deja el sistema en un estado desconocido. El
> healthcheck final es lo que convierte "el deploy terminó" en "el deploy funcionó".
> Y si falla, el rollback automático lo hace sin intervención humana.

### 2.4 El rollback

```bash
# Ver el estado
sudo /srv/cai/scripts/status.sh

# Volver atrás
sudo /srv/cai/scripts/rollback.sh
```

```bash
# Lo que hace rollback.sh
previous=$(readlink -f /srv/cai/previous)
current=$(readlink -f /srv/cai/current)
ln -sfn "$previous" /srv/cai/current
cd /srv/cai/current
php artisan config:cache && php artisan route:cache && php artisan view:cache
php artisan queue:restart
/srv/cai/scripts/healthcheck.sh
```

> [!important] El rollback de código NO toca la base de datos
> Esa es la razón de existir del patrón expand–contract (ver
> [[ADR-0003 Expand-Contract y Feature Flags]]). Si el rollback no resuelve el
> problema, el siguiente nivel es restaurar el backup.

---

## 3. Alternativas consideradas

### 3.1 Desplegar directamente sobre el directorio activo

| Aspecto | Detalle |
|---|---|
| **Descripción** | `git pull` en `/srv/cai`, `composer install`, `artisan migrate`. Todo en el mismo directorio. |
| **Ventajas** | Cero estructura. Un solo directorio. Fácil de entender. |
| **Desventajas** | **No hay rollback instantáneo**: hay que volver al commit anterior y reinstalar. Durante el deploy, el sistema está en un estado mixto. Si el `composer install` falla a mitad, el sistema queda roto. |
| **Por qué se descartó** | Es exactamente el escenario que el nivel 2 de rollback tiene que cubrir, y no lo cubre. Un deploy que no se puede revertir en un minuto no es un deploy, es una apuesta. |

### 3.2 Capistrano / Deployer

| Aspecto | Detalle |
|---|---|
| **Descripción** | Usar una herramienta dedicada que ya implementa el patrón symlink. |
| **Ventajas** | Probado. Tiene muchas funciones. |
| **Desventajas** | Otra dependencia (PHP o Ruby) que hay que mantener. Otra configuración. Su comportamiento por defecto no es el que necesitamos exactamente. |
| **Por qué se descartó** | El patrón completo que necesitamos son **~150 líneas de shell**. Una dependencia que hay que entender, actualizar y auditar para escribir 150 líneas de shell es un mal intercambio en un proyecto con un solo dev. |

### 3.3 Contenedores (Docker)

| Aspecto | Detalle |
|---|---|
| **Descripción** | La aplicación vive en una imagen; el deploy es levantar un contenedor nuevo. |
| **Ventajas** | Reproducibilidad total del entorno. Rollback instantáneo con tags de imagen. |
| **Desventajas** | Requiere un **orquestador** o, en el mínimo, `docker compose`. El servidor del centro necesita la imagen Docker. Aumenta el consumo de memoria (el daemon + el contenedor). El `docker compose` v2 no está disponible en el entorno verificado. |
| **Por qué se descartó** | Es la mejor opción **si** hubiera un orquestador y un equipo capaz de operarlo. Con un servidor modesto y una persona part-time, Docker agrega una capa de operación que hay que aprender a diagnosticar (contenedor que no arranca, red que no resuelve, volumen que no monta). El symlink da el 90 % del beneficio de rollback con el 10 % del costo. **Queda registrado en el backlog como opción a reevaluar si el sistema crece.** |

### 3.4 Git pull en el servidor

| Aspecto | Detalle |
|---|---|
| **Descripción** | El servidor hace `git pull` desde el repositorio remoto. |
| **Ventajas** | Simple. El servidor siempre tiene el código. |
| **Desventajas** | Requiere **internet o red con GitHub** en el momento del deploy. Si el centro no tiene internet estable, el deploy falla. Además, `git pull` sobre un checkout vivo deja archivos en estado intermedio si falla. |
| **Por qué se descartó** | La independencia de internet es una decisión explícita del proyecto (ver [[07.01 Arquitectura del Servidor del Centro]]). Un deploy que depende de GitHub contradice esa decisión. La alternativa es clonar desde un **mirror local** del repositorio, que es lo que se hace. |

---

## 4. Consecuencias

### 4.1 Positivas

- **Rollback de código en menos de un minuto**, ejecutable por el Administrador
  Técnico con un solo comando.
- **El deploy no interrumpe el servicio**: el release nuevo se prepara por completo
  y el cambio es un `ln -sfn`.
- **El estado persistente sobrevive a los deploys** (`shared/`).
- **Se puede tener varias versiones en el servidor** para comparar o para depurar.
- **Es auditable**: `readlink current` responde qué está desplegado.
- **No depende de internet** en el momento del deploy (usa un mirror local o un
  paquete de release).

### 4.2 Negativas (lo que aceptamos)

- **Consumo de disco**: cada release ocupa espacio. Se resuelve con
  `prune-releases.sh --keep 5`.
- **Un `release.sh` que hay que mantener**: es código, y el código puede fallar.
- **El symlink hay que entenderlo**: si alguien hace `cp -r` en lugar de desplegar
  con el script, rompe el mecanismo.
- **Los permisos y el `owner` de los archivos** hay que fijarlos en el script (los
  releases nuevos los crea `root` si el deploy se hace con `sudo`).
- **El `storage/` enlazado no se versiona ni se respalda con el release**: hay que
  respaldarlo aparte (está en el backup de la base + el backup de `storage/`).
- **Un error en el `release.sh` puede dejar el symlink en un estado raro**: por eso
  el `status.sh` verifica y el `healthcheck` es el juez final.
- **El rollback de código y el de datos son dos cosas distintas**: puede pasar que
  el rollback de código no resuelva el problema porque el problema está en los datos.

### 4.3 Neutras

- El servidor **no** tiene un "directorio de la aplicación": tiene un symlink. Es
  un detalle que se explica una vez y no vuelve a molestar.
- El número de releases en el servidor es un parámetro del script (`--keep`).

---

## 5. Verificación

```text
☐ Un deploy completo tarda menos de 3 minutos
☐ Un rollback completo tarda menos de 1 minuto (cronometrado)
☐ El healthcheck se ejecuta al final del deploy y hace rollback automático si falla
☐ `status.sh` muestra la versión activa, la anterior, la fecha y el estado del healthcheck
☐ `shared/storage` y `shared/.env` no cambian entre releases (verificado con checksum)
☐ `prune-releases.sh --keep 5` conserva los 5 últimos y borra el resto
☐ El rollback se probó en el servidor real, con acta y cronómetro
☐ Un release se puede arrancar manualmente desde su directorio (para depurar)
```

> [!important] La verificación que de verdad importa
> **Que el rollback se haya probado con el cronómetro en marcha.** Un rollback que
> "debería funcionar" no es un rollback. El ensayo de F8 tiene que medir el tiempo
> real de principio a fin, con el healthcheck en verde.

---

## 6. Reversibilidad

| Aspecto | Detalle |
|---|---|
| **¿Se puede revertir?** | Sí |
| **Cómo** | Desplegar directamente sobre el directorio activo (`git pull` + `composer install`). Se pierde el rollback instantáneo. |
| **Costo de revertir** | Medio-bajo. Un día de trabajo, más la pérdida de la propiedad de rollback rápido. |
| **Señal de que hay que revertir** | Si el número de incidentes donde el rollback fue necesario supera ~2 al año, o si el `release.sh` se vuelve más simple de lo que parece. La señal más clara: si el script se modifica más de una vez por trimestre. |

---

## 7. Referencias

- [[06.05 Release y Deploy]]
- [[06.06 Procedimiento de Rollback]]
- [[06.03 Expand-Contract]]
- [[07.01 Arquitectura del Servidor del Centro]]
- [[07.03 Instalación del Sistema]]
- [[10.01 Runbook Operativo]]
