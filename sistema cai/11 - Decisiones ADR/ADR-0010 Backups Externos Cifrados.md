---
title: ADR-0010 Backups Externos Cifrados
type: adr
status: aceptado
tags: [cai, adr, backup, descaro, cifrado, continuidad, retencion]
owner: Dirección
updated: 2026-10-22
related:
  - "[[06.07 Backups y Recuperación]]"
  - "[[10.04 Recuperación ante Desastres]]"
  - "[[07.01 Arquitectura del Servidor del Centro]]"
---

# ADR-0010 — Copias de seguridad externas, cifradas y con custodia de claves separada

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-10-22 |
| **Decide** | Dirección, con Administración Técnica |
| **Alcance** | Plan de respaldos del sistema, custodia de claves, continuidad operativa |

---

## 1. Contexto

El sistema guarda datos que **no se pueden recuperar** si se pierden: historial
clínico de menores, datos de facturación, y el registro académico.

El servidor es **propio del centro**, está en el **edificio**, y es el **único**
lugar donde vive la producción.

**Restricciones:**

- **D-4 (ransomware)** y **D-5 (pérdida total del servidor)** son escenarios
  reales, no teóricos. Un backup guardado en el mismo servidor **no protege**
  contra ninguno de los dos (ver [[10.04 Recuperación ante Desastres]]).
- **Los datos clínicos son sensibles**: la copia externa sale del perímetro
  físico del centro, así que **tiene que ir cifrada**.
- **No hay servicio de nube contratado** y el centro no quiere depender de
  internet: la copia se hace a un **destino físico fuera del centro** (P14).
- **El presupuesto es bajo** y la operación es mínima.
- **Nadie puede ser a la vez quien desarrolla el sistema y quien custodia sus
  claves**. Si el desarrollador tiene la clave y el backup, el cifrado no
  protege nada.
- La **retención de las notas clínicas** está pendiente de definición por
  Dirección (P4), y eso determina cuánto tiempo se guardan las copias.

**Qué sabemos:**

- La regla **3-2-1** es el estándar de facto: 3 copias, 2 medios distintos, 1
  copia fuera del sitio.
- Un backup **no verificado no es un backup**. La verificación tiene que ser
  periódica y **hecha por alguien que no lo hizo**.
- El cifrado **en reposo** del backup tiene sentido propio, aunque el disco de
  origen ya esté cifrado: la copia sale del centro.

**Qué no sabemos:**

- **Dónde** estará físicamente el destino externo (P14: un USB rotativo, el
  escritorio de la Dirección, la casa del Backup Custodian).
- **Quién** será el Backup Custodian (P19): tiene que ser una persona del
  centro, no el desarrollador.

---

## 2. Decisión

**Se adopta la regla 3-2-1: tres copias de los datos, en dos medios distintos,
una de ellas cifrada y custodiada fuera del centro. El cifrado del backup se
realiza con AES-256, y la clave de descifrado la custodia una persona del
centro distinta del desarrollador. El backup externo se genera diario y se
retira físicamente del centro una vez por semana; la verificación de
restauración se hace mensual y el ensayo completo, trimestral.**

En detalle:

### 2.1 Las tres copias

| Copia | Dónde | Frecuencia | Cifrado | Retención |
|---|---|---|---|---|
| **L0 · Local diaria** | `/var/backups/cai/` en el servidor | Diaria (02:00) | Sí (AES-256) | 7 días |
| **L1 · Local semanal** | `/var/backups/cai/weekly/` | Semanal (lunes) | Sí (AES-256) | 4 semanas |
| **L2 · Externa** | Destino físico fuera del centro | Diaria | Sí (AES-256) | 4 semanas + 1 copia mensual |

> [!danger] Por qué un backup en el mismo servidor no alcanza
> Un backup en el mismo disco **no protege** contra ransomware (que cifra el
> disco), ni contra incendio, robo, inundación, ni contra la pérdida total del
> equipo. Solo protege contra **errores de software**: un `DELETE` sin `WHERE`,
> una migración con error, un `DROP TABLE`. Por eso el nivel 2 de rollback
> (restaurar un `pg_dump`) vive en el servidor, y el nivel 3 (copia externa)
> vive fuera.

### 2.2 Los dumps separados por schema

```text
backup/
├── 2026-10-22/
│   ├── identity.sql.gz
│   ├── students.sql.gz
│   ├── scheduling.sql.gz
│   ├── care.sql.gz          ← contiene el contenido cifrado de las notas
│   ├── billing.sql.gz
│   ├── communications.sql.gz
│   ├── reporting.sql.gz
│   └── MANIFEST.txt         ← checksums, fecha, versión del esquema
```

| Regla | Detalle |
|---|---|
| **Un dump por schema** | Permite restaurar un módulo sin tocar los demás, y reduce el radio de impacto de una fuga. |
| **El dump clínico se separa** | Va cifrado con una clave distinta de la del resto, y con permisos de lectura más restrictivos. |
| **Checksums** | `SHA256SUM` de cada archivo, en el manifiesto. Un archivo corrupto se detecta antes de restaurar. |
| **El esquema va aparte** | `pg_dump --schema-only` en cada respaldo: permite reconstruir la base sin los datos, para un entorno de pruebas. |

> [!important] Por qué separar por schema y no un solo `pg_dump` sin `-n`
> Un `pg_dump` completo **mezcla** en el mismo archivo datos clínicos y datos
> financieros. Para restaurarlo hay que tener acceso a todo, y para
> compartirlo o transportarlo hay que cifrarlo entero, incluido lo que no
> necesita cifrado. Separado, cada módulo tiene su dump, su clave y su
> audiencia.

### 2.3 El cifrado

| Aspecto | Decisión |
|---|---|
| **Algoritmo** | AES-256 (a través de `openssl enc -aes-256-cbc -pbkdf2`, o `age`) |
| **Clave** | Frase de paso fuerte, custodiada por el Backup Custodian |
| **Herramienta** | `openssl` (disponible en el servidor) o `age` (más simple, recomendado) |
| **Destino de la clave** | **Gestor de contraseñas**, con la `APP_KEY` y la clave clínica **en entradas separadas** |
| **Integridad** | Checksum SHA-256 antes de cifrar, verificado después de descifrar |
| **Transporte** | El archivo cifrado se copia al destino. Si hay red, `rsync` sobre SSH. |

```bash
# Cifrar un dump
openssl enc -aes-256-cbc -pbkdf2 -iter 600000 -salt \
  -in backup.sql.gz \
  -out backup.sql.gz.enc \
  -pass file:/run/secrets/backup_key

# Verificar integridad y descifrar
sha256sum -c backup.sha256
openssl enc -d -aes-256-cbc -pbkdf2 -iter 600000 \
  -in backup.sql.gz.enc \
  -out backup.sql.gz \
  -pass file:/run/secrets/backup_key
```

> [!danger] La regla que no se negocia
> **El backup cifrado y su clave nunca están en el mismo sitio.** Si están
> juntos, el cifrado no aporta nada: cualquiera que robe el disco se lleva
> también los datos. Por eso:
> - La clave está en el gestor de contraseñas, **no** en el servidor.
> - El servidor tiene un **derivado** de la clave en un archivo con permisos
>   `600`, propiedad del usuario del servicio, que **no** se respalda con los
>   dumps.
> - El Backup Custodian **no** es el desarrollador (P19).

### 2.4 La custodia

| Rol | Qué custodia | Qué hace |
|---|---|---|
| **Administración Técnica** | El script y el servidor | Genera el backup, lo cifra, lo deja listo para retirar. **No tiene la clave maestra.** |
| **Backup Custodian** | La frase de paso del backup (en el gestor de contraseñas) | Retira el medio, lo guarda fuera del centro, lo devuelve, verifica. |
| **Responsable técnico (dev)** | Nada de las claves | Recibe el aviso de "el backup está listo", verifica el checksum. **No tiene la clave.** |
| **Dirección** | La política | Aprueba la retención y los cambios de esta decisión. |

> [!important] Por qué el desarrollador no puede ser el custodio
> El escenario que hay que cubrir es el **error humano** y el **abuso de
> privilegio**: una persona con acceso a los datos y a las claves, en un
> sistema con datos de menores. Separar los roles es barato (es una decisión
> de organización, no de tecnología) y reduce la superficie.

### 2.5 La verificación

| Verificación | Frecuencia | Quién | Qué demuestra |
|---|---|---|---|
| **El backup existe y tiene el tamaño esperado** | Diaria | Admin Técnico | Que el script corrió |
| **El checksum coincide** | Diaria | Admin Técnico | Que el archivo no se corrompió en el traslado |
| **Se puede descifrar** | Semanal | Admin Técnico + Custodian | Que la clave funciona |
| **Se puede restaurar en una base de prueba** | Mensual | Admin Técnico + Custodian | Que el backup sirve de algo |
| **Ensayo completo de recuperación** | Trimestral | Custodian + Dirección | Que el procedimiento está escrito y se puede seguir |

> [!danger] Un backup que no se ha restaurado no es un backup
> Un archivo corrupto, un esquema que cambió, una tabla renombrada, una
> versión de PostgreSQL incompatible: todo eso **solo se detecta restaurando**.
> El ensayo trimestral es el que convierte "tenemos backups" en "podemos
> recuperar".

---

## 3. Alternativas consideradas

### 3.1 Copia de seguridad en la nube (S3, Backblaze, Wasabi)

| Aspecto | Detalle |
|---|---|
| **Descripción** | El backup se sube a un almacenamiento de objetos en la nube. |
| **Ventajas** | Automático, sin medios físicos. Copias fuera del sitio por definición. Alta durabilidad. |
| **Desventajas** | **Requiere internet estable** en el servidor (contradice D0). Costo mensual recurrente. **El backup sale del control del centro**: la clave y los datos están en un tercero. |
| **Por qué se descartó** | El requisito de independencia de internet y de no depender de terceros es explícito en este proyecto. Un backup que depende de la nube es un backup que deja de existir cuando se cae el enlace. **Queda como opción a reevaluar** si el centro contrata internet estable y un almacenamiento. |

### 3.2 Segunda máquina en el centro (NAS o servidor espejo)

| Aspecto | Detalle |
|---|---|
| **Descripción** | Un segundo equipo en el mismo edificio, con replicación de la base de datos. |
| **Ventajas** | Copia automática, sin intervención humana. Restauración rápida. |
| **Desventajas** | Costo del equipo y de su mantenimiento. **No protege contra incendio, robo o inundación** si está en el mismo edificio. Además, es una persona más que administrar. |
| **Por qué se descartó** | Replicar en el mismo edificio protege contra ransomware y contra error de software, que es lo que ya cubre el backup local + externo. El escenario D-5 (pérdida total del servidor) seguiría sin cobertura, y el costo sube. |

### 3.3 Backup sin cifrar

| Aspecto | Detalle |
|---|---|
| **Descripción** | Los dumps se guardan tal cual, confiando en el cifrado del disco del servidor. |
| **Ventajas** | Restauración más simple. Sin gestión de claves. |
| **Desventajas** | La copia **sale del centro** (destino externo). Un medio extraíble perdido o robado expone notas clínicas de menores. Sin cifrado, la copia tiene el mismo nivel de protección que los datos originales. |
| **Por qué se descartó** | El medio externo es el punto más débil de la cadena: se transporta, se guarda en un escritorio, se puede perder. El cifrado es barato y es la única defensa en ese punto. |

### 3.4 Cifrar con una clave guardada en el mismo servidor

| Aspecto | Detalle |
|---|---|
| **Descripción** | La clave del backup está en un archivo del servidor, protegida por permisos. |
| **Ventajas** | Automático: nunca hay que intervenir. |
| **Desventajas** | **Si alguien compromete el servidor, tiene los datos y la clave.** Con ransomware, el atacante obtiene lo mismo. La clave junto al backup no protege nada. |
| **Por qué se descartó** | Es exactamente el error que este ADR evita. La clave tiene que estar en un **lugar distinto** y en manos de una **persona distinta**. |

### 3.5 Solo backups locales (sin copia externa)

| Aspecto | Detalle |
|---|---|
| **Descripción** | Únicamente los dumps en el servidor, con rotación de 7 días. |
| **Ventajas** | Cero costo. Cero proceso. Restauración inmediata. |
| **Desventajas** | **No cubre D-4 ni D-5.** El escenario más grave del plan de continuidad queda sin cobertura. |
| **Por qué se descartó** | Los backups locales son un **complemento**, no el plan. La decisión de tener una copia externa es la que hace que el plan de continuidad sea creíble. |

### 3.6 Copia externa encriptada con la `APP_KEY`

| Aspecto | Detalle |
|---|---|
| **Descripción** | Se usa la misma clave de la aplicación para cifrar el backup. Una sola clave que recordar. |
| **Ventajas** | Una sola clave que gestionar. |
| **Desventajas** | Si se compromete la `APP_KEY`, se compromete todo: la aplicación **y** los backups. No hay separación de dominios. La `APP_KEY` la usa la aplicación todos los días; el backup se descifra una vez cada tres meses. Son justamente las claves que deberían estar separadas. |
| **Por qué se descartó** | La regla general de este proyecto es **separación de claves**: la `APP_KEY` y la clave clínica ya están separadas (ver [[ADR-0006 Cifrado de Notas Clínicas]]). La clave del backup es la tercera, y también va aparte. |

---

## 4. Consecuencias

### 4.1 Positivas

- **Los escenarios D-4 y D-5 tienen cobertura real**, que es lo que hacía falta.
- **Los datos clínicos no salen del centro en claro**: la copia viaja cifrada.
- **El cifrado y la clave están separados**, de modo que el cifrado aporta
  protección real y no es teatro.
- **Los dumps por schema** permiten restauraciones parciales y reducen el radio
  de impacto de una fuga o de un error.
- **Los checksums detectan la corrupción** antes de intentar restaurar, en lugar
  de descubrirla a mitad de una recuperación.
- **El plan de continuidad es verificable**: hay ensayos con fecha, responsable
  y resultado.
- **El costo es bajo**: un medio extraíble rotativo y una frase de paso.

### 4.2 Negativas (lo que aceptamos)

- **Hay un proceso manual**: alguien tiene que rotar el medio, llevárselo y
  devolverlo. Si esa persona falta una semana, el backup externo se atrasa.
- **La verificación de restauración consume tiempo**: una hora al mes, una
  mañana al trimestre. Es tiempo real que hay que sacar de la agenda.
- **Retención limitada**: 4 semanas de diarios + 1 copia mensual. Si Dirección
  exigiera conservar más (o si P4 determinara una retención legal de años),
  hay que **ampliar el almacenamiento externo**, y eso tiene un costo.
- **El backup externo requiere internet o transporte físico**: si hay internet
  estable en el centro, `rsync` por SSH automatiza el envío; si no, el
  transporte es manual.
- **La clave hay que recordarla y reponerla**: si el Backup Custodian cambia,
  hay que re-cifrar con la nueva clave o volver a descifrar y re-cifrar todo el
  histórico.
- **Un solo destino externo** es un punto de falla: si el medio se pierde y el
  último backup externo verificado es de hace un mes, la recuperación usa datos
  de hace un mes.
- **La retención de notas clínicas (P4) sigue abierta** y puede obligar a
  revisar la política de retención de los backups: si una nota debe conservarse
  15 años, los backups de 4 semanas no la cubren, y la copia externa de largo
  plazo tiene un costo distinto.

### 4.3 Neutras

- El backup externo **no sustituye** al local: uno protege de errores de
  software, el otro de la pérdida del equipo. Ambos se necesitan.
- La separación de roles (custodio ≠ desarrollador) es una decisión de
  **organización**, no de tecnología. Es la más barata de todo este ADR y la
  que más se olvida.

---

## 5. Verificación

```text
☐ El backup local diario existe y su tamaño es el esperado
☐ El checksum SHA-256 de cada dump coincide con el manifiesto
☐ Los dumps están separados por schema (un archivo por módulo)
☐ El dump clínico usa una clave distinta de la del resto
☐ El backup externo llega al destino fuera del centro
☐ El backup externo se puede descifrar con la clave del custodio
☐ Se puede restaurar un schema individual en una base de prueba
☐ Se puede restaurar el dump clínico y las notas se leen correctamente (requiere la APP_KEY y la clave clínica)
☐ La verificación mensual de restauración tiene acta con fecha y resultado
☐ El ensayo trimestral completo se realizó con la persona que tiene la clave
☐ La clave del backup NO está en el servidor, ni en el repositorio, ni en el backup
☐ La APP_KEY, la clave clínica y la clave del backup están en entradas SEPARADAS del gestor de contraseñas
☐ El backup externo más reciente no tiene más de 7 días
☐ El procedimiento de rotación de medios está escrito y es conocida por el Administrador Técnico
```

> [!important] El ensayo que de verdad prueba el plan
> **El ensayo trimestral, hecho por el custodio, no por el desarrollador.** Si el
> único que sabe descifrar y restaurar es la persona que construyó el sistema,
> el plan de continuidad no existe para el resto del centro: en el momento en
> que el desarrollador no esté disponible, nadie sabe qué hacer. Ese ensayo es
> el que mide la capacidad real de recuperación del centro.

---

## 6. Reversibilidad

| Aspecto | Detalle |
|---|---|
| **¿Se puede revertir?** | Sí, pero se pierde cobertura |
| **Cómo** | Dejar de copiar al exterior y quedarse con los backups locales. |
| **Costo de revertir** | Bajo en lo técnico, **alto en lo que acepta el centro**: D-4 y D-5 vuelven a estar sin cobertura. |
| **Mitigación** | Los backups ya hechos siguen siendo válidos: se pueden seguir restaurando. Lo que se pierde es la **generación automática** de nuevas copias externas. |
| **Señal de que hay que revertir** | Si el proceso manual de rotación se vuelve inviable (la persona responsable se va y nadie la reemplaza) y nadie encuentra un sustituto, el sistema queda con la cobertura local solamente. Es una señal organizacional, y hay que tratarla como una **incidencia**, no como un detalle de infraestructura. |

---

## 7. Referencias

- [[06.07 Backups y Recuperación]]
- [[10.04 Recuperación ante Desastres]]
- [[10.01 Runbook Operativo]]
- [[10.02 Calendario de Checklists]]
- [[07.01 Arquitectura del Servidor del Centro]]
- [[ADR-0006 Cifrado de Notas Clínicas]]
