---
title: ADR-0006 Cifrado de Notas Clínicas
type: adr
status: aceptado
tags: [cai, adr, seguridad, clinico, cifrado, aead, datos-sensibles]
owner: Dirección
updated: 2026-10-22
related:
  - "[[04.04 Datos Clínicos: Cifrado y Acceso]]"
  - "[[03.05 Planes de Atención y Notas Clínicas]]"
  - "[[08.07 F5 Seguimiento Clínico]]"
---

# ADR-0006 — Cifrado en reposo del contenido de las notas clínicas

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-10-22 |
| **Decide** | Dirección, con el Responsable técnico |
| **Alcance** | Módulo `care`, almacenamiento, respaldos, plan de continuidad |

---

## 1. Contexto

El sistema registrará **notas clínicas de menores**: observaciones de sesiones,
evaluaciones, evolución e incidencias durante la atención.

Este es el **dato más sensible** que maneja el sistema. Su compromiso tiene
consecuencias:

- **Legales**: son datos de salud de menores, con consentimiento de los
  responsables y con deber de confidencialidad.
- **Éticas**: el equipo clínico asume un compromiso profesional con las familias.
- **Reputacionales**: una filtración de notas de menores es un hecho que marca al
  centro durante años.

**Restricciones:**

- El servidor es **propio del centro** y **no tiene alta disponibilidad**: no hay
  un segundo servidor donde replicar el cifrado en tránsito.
- El cifrado tiene que ser **transparente para el código de aplicación**: el
  profesional no puede tener que "cifrar antes de guardar".
- El acceso del personal es **diversificado**: muchos profesionales con roles distintos tienen que ver
  partes distintas de la misma información.
- El sistema tiene que poder **exportar** el historial clínico en algún momento
  (traslado de alumno, auditoría externa).

**Qué sabemos:**

- El cifrado simétrico (AES-256-GCM) es el adecuado para datos en reposo: rápido,
  estándar, auditado.
- El cifrado a nivel de **columna** protege el dato aunque alguien tenga acceso
  directo a la base de datos (un `psql` sin distinción, un dump sin distinción).
- El cifrado a nivel de **disco** (LUKS, dm-crypt) protege contra robo del
  servidor, pero no contra alguien con acceso a la base de datos.

**Qué no sabemos:**

- Si Dirección o una auditoría externa exigirá un formato concreto de exportación
  (esto se resuelve en F9, ver [[01.07 Preguntas Abiertas y Decisiones Pendientes]]).
- Si en el futuro hará falta un segundo servidor con réplica (hoy no).

---

## 2. Decisión

**El contenido narrativo de las notas clínicas se cifra en reposo con
AES-256-GCM (cast `encrypted` de Laravel) usando una clave distinta de la
`APP_KEY`. El cifrado es transparente: se cifra al escribir y se descifra al leer,
con la clave gestionada fuera de la base de datos. Los metadatos de la nota
permanecen en claro para poder filtrar, ordenar y auditar sin descifrar.**

En detalle:

### 2.1 Qué se cifra y qué no

| Dato | Ubicación | Cifrado |
|---|---|---|
| **Contenido de la nota** | `care.clinical_notes.content` | ✅ **AES-256-GCM** |
| Resumen legible (≤ 300 car.) | `care.clinical_notes.summary` | No (redactado sin datos sensibles) |
| Tipo, estado, fechas, autor | `care.clinical_notes` (resto) | No |
| Diagnóstico | `care.care_plans.diagnosis` | ⚠️ **Pendiente de P7** |
| Objetivos del plan | `care.care_goals` | ⚠️ **Pendiente de P7** |
| Archivos adjuntos clínicos | `storage/app/clinical` | ✅ Cifrados en disco (LUKS) |

> [!important] La línea roja
> **El contenido de una nota clínica nunca existe en claro en el almacenamiento.**
> Solo existe en claro en memoria, durante el tiempo que la pantalla del
> profesional la muestra.

### 2.2 La clave

| Aspecto | Decisión |
|---|---|
| **Algoritmo** | AES-256-GCM (AEAD) |
| **Longitud de clave** | 32 bytes (256 bits) |
| **Clave** | `CLINICAL_ENCRYPTION_KEY`, distinta de `APP_KEY` |
| **Generación** | `php artisan key:generate --show` → se guarda en el gestor de contraseñas |
| **Rotación** | Ver §2.5 |
| **IV / Nonce** | Generado aleatoriamente por el cifrado, **nunca reutilizado** |
| **AAD** | `clinical_note_id` — impide mover un texto cifrado de una fila a otra |
| **Almacenamiento** | **Nunca** en la base de datos, nunca en el repositorio, nunca en el backup del servidor |

```php
// packages/care/src/Models/ClinicalNote.php
use Illuminate\Database\Eloquent\Casts\AsEncryptedArray; // o el cast string equivalente

protected function casts(): array
{
    return [
        'content' => 'encrypted',
    ];
}
```

### 2.3 Por qué GCM y no CBC

| Propiedad | GCM | CBC |
|---|---|---|
| **Detecta manipulación** | ✅ Etiqueta de autenticación | ❌ No |
| **IV (nonce)** | ✅ Sin padding ni IV manual | ❌ IV aleatorio obligatorio, padding obligatorio |
| **Confidencialidad + integridad** | En un solo primitivo | Dos primitivos |

> [!danger] El riesgo que se evita con GCM
> Con un cifrado sin autenticación, alguien con acceso a la base de datos podría
> **modificar** una nota clínica sin tocarla —por ejemplo, cambiar un texto
> cifrado por otro— y el sistema no se enteraría. Con GCM, cualquier modificación
> hace que el descifrado **falle**, y el sistema registra el intento. La
> inalterabilidad de la nota no depende solo de las reglas de negocio: tiene una
> barrera criptográfica.

### 2.4 El descifrado y la auditoría

```text
Petición autenticada
  → Policy verifica permiso + alcance
    → Se lee la fila (contenido cifrado)
      → Se descifra en memoria
        → Se registra el acceso en security_events
          → Se muestra
```

> [!important] Descifrar **es** acceder
> La auditoría de lectura se dispara en el `retrieved` del observer, que ocurre
> **después** de que el descifrado tenga éxito. Es decir: si el descifrado falla,
> no hubo lectura y no hay nota que auditar. Si el descifrado tiene éxito, la
> lectura quedó registrada. No hay forma de leer una nota sin dejar rastro.

### 2.5 Rotación de la clave

| Escenario | Procedimiento |
|---|---|
| **Rotación ordinaria** | Se cifra con la clave nueva, se descifra con la antigua y se vuelve a cifrar, en un comando por lotes. |
| **Clave comprometida** | Se declara incidente, se rota, y **todas** las notas se re-cifran. |
| **Clave perdida** | **Pérdida total e irreversible** de las notas clínicas. De ahí la regla de respaldar las claves por separado. |

> [!danger] La `APP_KEY` y la clave clínica se respaldan **por separado**
> Si se pierde la `APP_KEY`, se pierden todas las notas clínicas cifradas (y
> cualquier otro dato cifrado de Laravel). Por eso ambas claves están en el
> gestor de contraseñas del centro, **nunca** en el mismo lugar que el backup del
> servidor. Ver [[07.05 Configuración de PostgreSQL]] y
> [[10.04 Recuperación ante Desastres]].

---

## 3. Alternativas consideradas

### 3.1 Sin cifrado (solo control de acceso por rol)

| Aspecto | Detalle |
|---|---|
| **Descripción** | Las notas se guardan en claro; la protección es el permiso de la aplicación y el cifrado de disco del servidor. |
| **Ventajas** | Cero complejidad. Búsqueda y reportes triviales. Exportación sin pasos extra. |
| **Desventajas** | Un `psql` sin distinción, un dump sin distinción o un acceso indebido al servidor expone **todo** el contenido. El cifrado de disco protege contra robo físico, no contra acceso lógico. |
| **Por qué se descartó** | El riesgo aceptable no es "alguien ve la base de datos de un centro de 300 alumnos". La consecuencia legal y ética de una filtración de notas clínicas de menores es desproporcionada frente al costo de cifrar una columna. |

### 3.2 Cifrado de disco completo (LUKS / dm-crypt)

| Aspecto | Detalle |
|---|---|
| **Descripción** | Cifrar el volumen o la partición del servidor. |
| **Ventajas** | Protege **todo** el disco, no solo las notas. Cubre también logs, `storage/` y archivos adjuntos. |
| **Desventajas** | No protege contra acceso lógico a la base de datos. El backup tiene que verse descifrado en el momento de la copia. Si el sistema se reinicia sin clave, no arranca. |
| **Por qué se descartó** | **No es una alternativa, es un complemento.** Se conserva como una medida adicional, pero no resuelve el caso principal: alguien con permisos de PostgreSQL. |

### 3.3 Cifrado con clave pública (RSA / ECIES)

| Aspecto | Detalle |
|---|---|
| **Descripción** | Cada usuario con acceso legítimo recibe la clave cifrada con su clave pública. |
| **Ventajas** | Control de acceso fino por destinatario. |
| **Desventajas** | La operación de descifrado (RSA) es **mucho** más lenta y no admite consultas. Reescribir la nota exige recifrar. La gestión de claves públicas por usuario es una fuente de problemas de soporte. |
| **Por qué se descartó** | El modelo de acceso real del sistema es **por rol y alcance**, no por identidad con clave propia. Un profesional asignado a 20 alumnos no puede tener 20 claves. |

### 3.4 Cifrado determinista (para poder buscar)

| Aspecto | Detalle |
|---|---|
| **Descripción** | Cifrar con un IV derivado del contenido para que dos textos iguales generen el mismo texto cifrado y se pueda buscar con `LIKE`. |
| **Ventajas** | Búsqueda en contenido cifrado. |
| **Desventajas** | **Rompe la confidencialidad**: el atacante ve qué textos son iguales. El IV determinista es público, así que se puede montar un diccionario de textos comunes contra el campo cifrado. |
| **Por qué se descartó** | Se resuelve con un **resumen no sensible en claro** (`summary`, ≤ 300 caracteres) y con el hecho de que **no se busca dentro del contenido clínico**. La búsqueda global de Filament excluye el módulo `care` (ver §5 de [[04.04 Datos Clínicos: Cifrado y Acceso]]). |

### 3.5 Cifrado en la capa de aplicación (servicio externo, HSM)

| Aspecto | Detalle |
|---|---|
| **Descripción** | Un servicio dedicado (KMS/HSM) hace el cifrado. |
| **Ventajas** | La clave nunca existe en la aplicación. Rotación gestionada. Auditoría de uso de clave. |
| **Desventajas** | Un componente más que operar en un centro sin equipo de seguridad. Si el servicio no está disponible, **el sistema no puede leer una sola nota**. Punto único de fallo crítico. |
| **Por qué se descartar** | Es la opción correcta para una organización con equipo de seguridad y disponibilidad 24/7. Aquí no existe ese equipo. El coste operativo supera con creces el beneficio. **Queda anotado como opción a reevaluar si el centro crece o si aparece una exigencia legal.** |

---

## 4. Consecuencias

### 4.1 Positivas

- **Una filtración de la base de datos no expone notas clínicas.** Es la
  consecuencia principal que justifica todo el resto.
- **La inalterabilidad tiene barrera criptográfica**: el cifrado autenticado
  detecta cualquier manipulación del texto cifrado.
- **El cifrado es transparente**: el código de aplicación no cambia; el cast hace
  todo. No hay que aprender una API nueva.
- **El acceso se audita**: leer una nota es un evento registrado con usuario,
  hora, nota y alumno.
- **El respaldo se puede hacer por schema**: los dumps clínicos van cifrados
  aparte de los administrativos (ver [[10.04 Recuperación ante Desastres]]).
- **La clave se puede rotar** sin reescribir la aplicación.

### 4.2 Negativas (lo que aceptamos)

- **No se puede buscar dentro del contenido.** Hay que buscar por alumno, tipo,
  fecha y profesional. Es una limitación real y permanente.
- **No se pueden hacer reportes SQL sobre el texto.** Cualquier agregación
  tiene que hacerse en la capa de aplicación o sobre el `summary`.
- **La base de datos es más grande**: el cifrado añade ~60 % de tamaño (base64
  del binario + IV + etiqueta) al campo `content`.
- **Cada lectura descifra.** Es una operación de CPU, aunque despreciable para
  el volumen esperado (unas pocas notas por alumno al mes).
- **Se pierde la clave, se pierden las notas.** No hay recuperación posible. Es
  la contrapartida de la seguridad, y por eso el respaldo de claves es un
  requisito, no una buena práctica.
- **El respaldo de la clave es un punto de fallo humano.** Alguien tiene que
  tener acceso al gestor de contraseñas y acordarse de actualizarlo tras cada
  rotación.
- **La exportación a un tercero requiere descifrar**, lo que obliga a abrir el
  caso con cuidado (quién, qué, cuándo, con qué autorización).
- **No hay que subestimar la rotación.** Re-cifrar todas las notas es una
  operación de mantenimiento con downtime parcial si no se hace por lotes.

### 4.3 Neutras

- El módulo `care` es el único que depende de la clave clínica. Los demás
  módulos no la conocen, y por la regla de fronteras ([[02.03 Reglas de Frontera entre Módulos]]) no pueden ni leerla.
- La clave clínica **no** es la `APP_KEY`. Son dos secretos distintos, con dos
  respaldos distintos y dos rotaciones distintas.

---

## 5. Verificación

```text
☐ El contenido de una nota NO aparece en claro en un dump de la base de datos
☐ `grep` sobre el dump con una frase de una nota real no devuelve nada
☐ El dump con `pg_dump` (sin `-n`) NO contiene el texto cifrado legible de notas
☐ La nota se lee correctamente en la interfaz del profesional asignado
☐ Un profesional NO asignado NO puede leer la nota (Policy + alcance)
☐ La lectura de una nota genera un registro en security_events
☐ Cambiar un byte del texto cifrado hace fallar el descifrado (GCM lo detecta)
☐ La clave clínica NO está en el repositorio, ni en el .env del repo, ni en el backup del servidor
☐ La `APP_KEY` y la clave clínica están respaldadas en lugares separados
☐ La rotación de clave re-cifra las notas y todas siguen legibles
☐ La exportación de historial clínico abre un caso con registro de quién pidió qué y con qué autorización
```

> [!important] El test que no se puede omitir
> **Hacer un `pg_dump` de la base en producción y buscar una frase de una nota
> real.** Si la frase aparece, el cifrado no está funcionando, por mucho que las
> policies y los roles estén bien. Este test va en la checklist de F5
> (ver [[08.07 F5 Seguimiento Clínico]]).

---

## 6. Reversibilidad

| Aspecto | Detalle |
|---|---|
| **¿Se puede revertir?** | Parcialmente |
| **Cómo** | Se puede **dejar de cifrar** (quitar el cast y reescribir los datos en claro). Eso es una reversión técnica, y es una **regresión de seguridad**, no una mejora. |
| **Lo que no se puede deshacer** | Si la clave se pierde, las notas **no** se recuperan. No hay cifrado de clave, no hay backup de la clave en el sistema, por diseño. |
| **Costo de revertir** | Alto en el sentido de que es una pérdida de protección. Bajo en lo técnico. |
| **Señal de que hay que revertir** | Ninguna foreseeable. Si el requisito legal de retención (P4) resultara incompatible con el cifrado, la alternativa no es dejar de cifrar, sino redefinir el proceso de exportación. |

---

## 7. Referencias

- [[04.04 Datos Clínicos: Cifrado y Acceso]]
- [[03.05 Planes de Atención y Notas Clínicas]]
- [[04.01 Modelo de Seguridad]]
- [[10.04 Recuperación ante Desastres]]
- [[07.05 Configuración de PostgreSQL]]
- [[ADR-0010 Backups Externos Cifrados]]
