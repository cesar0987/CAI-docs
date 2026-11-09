---
title: Plantilla - Inventario de Servidor
type: plantilla
status: vigente
tags: [cai, plantilla, inventario, servidor, hardware, datos, evidencia]
owner: Responsable técnico
updated: 2026-11-09
related:
  - "[[07.08 Relevamiento del Servidor del Centro]]"
  - "[[Plantilla - Solicitud de Autorización de Intervención en Servidor]]"
  - "[[Plantilla - Informe de Relevamiento de Servidor]]"
  - "[[07.02 Requisitos de Hardware y Software]]"
---

# Plantilla - Inventario de Servidor

> [!info] Cómo usar esta plantilla
> Se completa **durante** la intervención, no después. Cada ficha se llena con lo que
> se observa o con la salida de un comando de solo lectura. Los campos que no se
> puedan obtener se marcan `No verificable` y se explican en la ficha 8.
>
> **Regla:** este inventario no lleva datos personales. Solo categorías, cantidades y
> tamaños. Si un dato no se puede anotar sin identificar a una persona, no se anota.

---

## Ficha 0 — Datos del relevamiento

| Campo | Valor |
|---|---|
| **Centro** | [Nombre] |
| **N.º de solicitud de autorización** | [AAAAMMDD-NN] |
| **Fecha de inicio** | [AAAA-MM-DD] |
| **Hora de inicio** | [HH:MM] |
| **Fecha de cierre** | [AAAA-MM-DD] |
| **Hora de cierre** | [HH:MM] |
| **Responsable técnico** | [Nombre] |
| **Acompañante designado** | [Nombre y cargo] |
| **Equipo / etiqueta** | [Identificación] |
| **Ubicación física** | [Sala / rack / oficina] |
| **Modalidad** | Presencial en el centro |
| **Medio de evidencia** | [Medio cifrado, identificador] |

---

## Ficha 1 — Hardware

| Componente | Detalle | Valor relevado | Evidencia | Observaciones |
|---|---|---|---|---|
| Tipo de equipo | Torre / rack / otro | [Valor] | [Foto / comando] | [ ] |
| Fabricante | Marca | [Valor] | [Etiqueta] | [ ] |
| Modelo | Modelo comercial | [Valor] | [Etiqueta] | [ ] |
| Número de serie | Serial | [Valor] | [Etiqueta] | [ ] |
| Etiqueta de inventario | Identificador del centro | [Valor] | [Foto] | [ ] |
| CPU | Modelo y arquitectura | [Valor] | `lscpu` | [ ] |
| Núcleos / hilos | Cantidad | [Valor] | `lscpu` | [ ] |
| Memoria RAM | Total instalada | [Valor] | `free -h` / `dmidecode` | [ ] |
| Módulos de memoria | Cantidad y capacidad | [Valor] | `dmidecode -t memory` | [ ] |
| Discos | Cantidad y tipo | [Valor] | `lsblk` | [ ] |
| Fuente de alimentación | Potencia y estado | [Valor] | Etiqueta / visual | [ ] |
| UPS | Marca, modelo, autonomía | [Valor] | Etiqueta / visual | [ ] |
| Rack | Medidas y ventilación | [Valor] | Visual | [ ] |
| Estado exterior | Limpieza, golpes, polvo | [Valor] | Foto | [ ] |
| Garantía | Vigente / vencida / sin dato | [Valor] | Documentación | [ ] |
| Antigüedad estimada | Años | [Valor] | Documentación | [ ] |

> [!note] Comparación con el requisito
> Al cerrar esta ficha, comparar CPU, RAM y disco con [[07.02 Requisitos de Hardware y Software]].
> El resultado va en la ficha 8 como hallazgo, no acá.

---

## Ficha 2 — Almacenamiento

### 2.1 Discos

| Dispositivo | Tipo | Capacidad | Uso | Sistema de archivos | Cifrado | SMART | Estado |
|---|---|---|---|---|---|---|---|
| [/dev/sdX] | SSD / HDD | [GB] | [%] | [ext4 / xfs / ntfs] | Sí / No / Sin dato | OK / Fallo / Sin dato | [Bueno / Regular / Malo] |
| [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

### 2.2 Volúmenes y particiones

| Punto de montaje | Tamaño | Usado | Disponible | Uso % | Observaciones |
|---|---|---|---|---|---|
| [/] | [GB] | [GB] | [GB] | [%] | [ ] |
| [/srv] | [GB] | [GB] | [GB] | [%] | [ ] |
| [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

### 2.3 Estado general

| Pregunta | Respuesta |
|---|---|
| ¿Hay algún disco con errores SMART? | [Sí / No / Sin dato] |
| ¿Hay poco espacio libre? | [Sí / No] |
| ¿El disco está cifrado? | [Sí / No / Parcial] |
| ¿Hay swap activo? | [Sí / No] |
| ¿Se detectaron sectores reasignados? | [Sí / No / Sin dato] |

---

## Ficha 3 — Software

| Componente | Detalle | Valor relevado | Evidencia |
|---|---|---|---|
| Sistema operativo | Distribución y edición | [Valor] | `cat /etc/os-release` / `Get-ComputerInfo` |
| Versión | Número exacto | [Valor] | [Comando] |
| Kernel | Versión | [Valor] | `uname -a` |
| Arquitectura | x86_64 / ARM | [Valor] | `uname -m` |
| Última actualización | Fecha | [Valor] | Registro del sistema |
| Servicios activos | Lista | [Valor] | `systemctl` / `Get-Service` |
| Software instalado | Paquetes o programas | [Resumen] | `dpkg -l` / Registro |
| Licencias | Software propietario | [Valor] | Documentación |
| Antivirus / EDR | Producto y estado | [Valor] | Consola |
| Acceso remoto | SSH / RDP / otro | [Valor] | Configuración |
| Lenguajes / runtimes | PHP, Node, otros | [Valor] | `php -v`, etc. |
| Base de datos | Motor y versión | [Valor] | `psql --version` |
| Servidor web | Producto y versión | [Valor] | `nginx -v` |

> [!warning] No pegar claves de licencia
> Si aparece una licencia, se registra el producto y el estado, nunca la clave.

---

## Ficha 4 — Red

| Aspecto | Valor relevado | Evidencia |
|---|---|---|
| Nombre del equipo | [Valor] | `hostnamectl` |
| Interfaces | [Lista] | `ip -brief address` |
| Dirección IP | [IP / DHCP] | `ip address` |
| Máscara | [Valor] | `ip address` |
| Puerta de enlace | [Valor] | `ip route` |
| DNS | [Valor] | `resolvectl status` |
| Puertos en escucha | [Lista] | `ss -ltnp` |
| Firewall | Activo / inactivo | `ufw status` |
| Reglas relevantes | [Resumen] | `ufw status verbose` |
| Switch / router | Marca y modelo | Etiqueta |
| Salida a internet | Sí / No / Restringida | Prueba controlada |
| VPN | Sí / No | Configuración |
| Certificados | Vigencia | `openssl x509` |

> [!danger] No probar conectividad a internet desde el servidor
> La salida a internet se determina por configuración y por lo que reporte el centro.
> No se abre un navegador ni se descarga nada.

---

## Ficha 5 — Cuentas y accesos

| Usuario | Rol / propósito | Shell | Acceso SSH | MFA | Última sesión | Observaciones |
|---|---|---|---|---|---|---|
| [usuario] | [Administración / servicio] | [bash / nologin] | Sí / No | Sí / No / Sin dato | [Fecha] | [ ] |
| [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

### 5.1 Controles de acceso

| Pregunta | Respuesta |
|---|---|
| ¿Hay login directo de `root`? | [Sí / No / Sin dato] |
| ¿Se permite autenticación por contraseña? | [Sí / No / Sin dato] |
| ¿Hay cuentas sin contraseña o con contraseña débil? | [Sí / No / No verificable] |
| ¿Hay credenciales en texto plano? | [Sí / No / No verificable] |
| ¿Dónde están las credenciales? | [Ubicación, sin copiar el valor] |
| ¿Hay claves SSH sin passphrase? | [Sí / No / Sin dato] |
| ¿Hay cuentas de exempleados activas? | [Sí / No / No verificable] |

> [!danger] Credenciales: existencia sí, valor no
> Si se encuentra una contraseña, token o clave en un archivo, se anota **la ruta y el
> tipo de credencial**. El valor no se transcribe, no se fotografía y no se copia.

---

## Ficha 6 — Respaldos

| Aspecto | Valor relevado | Evidencia |
|---|---|---|
| ¿Hay respaldos? | Sí / No | Documentación / carpetas |
| Destino | [Disco local / NAS / externo] | Configuración |
| Frecuencia | [Diaria / semanal / mensual] | Cron / tarea |
| Hora de ejecución | [HH:MM] | Cron / tarea |
| Retención | [Días / semanas] | Configuración |
| Cifrado | Sí / No | Configuración |
| Última ejecución exitosa | [Fecha y hora] | Log |
| Última prueba de restauración | [Fecha / nunca] | Registro |
| Responsable | [Nombre / rol] | Documentación |
| ¿El respaldo sale del centro? | Sí / No | Documentación |
| ¿Hay copia fuera del edificio? | Sí / No | Documentación |
| Observaciones | [ ] | [ ] |

> [!important] Un respaldo que no se restauró no es un respaldo
> Si nunca se probó la restauración, se registra como `nunca` y se convierte en un
> hallazgo de prioridad alta. Ver [[06.07 Backups y Recuperación]] y
> [[06.08 Verificacion de Restauracion]].

---

## Ficha 7 — Mapa de datos

> [!danger] Esta ficha se completa con agregados, nunca con contenido
> Se registra **qué sistema o carpeta** contiene los datos, **qué categoría** son,
> **cuántos** registros o archivos hay y **cuánto** ocupan. No se transcribe ningún
> nombre, documento, diagnóstico ni importe.

| ID | Sistema o ubicación | Categoría | Descripción funcional | Volumen | Sensibilidad | Responsable | Respaldo | Observaciones |
|---|---|---|---|---|---|---|---|---|
| D-01 | [Base / carpeta / aplicación] | Identificatorios | [Para qué se usa] | [N registros / X GB] | Alta | [Rol] | Sí / No | [ ] |
| D-02 | [ ] | Clínicos | [ ] | [ ] | Muy alta | [ ] | [ ] | [ ] |
| D-03 | [ ] | Financieros | [ ] | [ ] | Alta | [ ] | [ ] | [ ] |
| D-04 | [ ] | Documentos | [ ] | [ ] | Alta | [ ] | [ ] | [ ] |
| D-05 | [ ] | Credenciales | [ ] | [ ] | Muy alta | [ ] | [ ] | [ ] |
| D-06 | [ ] | Otros | [ ] | [ ] | Media / Baja | [ ] | [ ] | [ ] |

### 7.1 Cómo se cuenta sin leer

| Dato | Comando o método | Qué se registra |
|---|---|---|
| Cantidad de filas | `SELECT COUNT(*) FROM <tabla>;` | Solo el número |
| Tamaño de base | `SELECT pg_size_pretty(pg_database_size('<base>'));` | Solo el tamaño |
| Cantidad de archivos | `find <ruta> -type f \| wc -l` | Solo el número |
| Tamaño de carpeta | `du -sh <ruta>` | Solo el tamaño |
| Extensiones | `find <ruta> -type f -printf '%f\n' \| sed 's/.*\.//' \| sort \| uniq -c` | Solo el conteo por extensión |

> [!tip] Si el número es pequeño, no se detalla
> Un conteo de 3 registros en una categoría sensible puede identificar a las personas.
> En ese caso se informa `menos de 10` y no el número exacto.

---

## Ficha 8 — Hallazgos

| ID | Hallazgo | Ficha de origen | Evidencia | Riesgo | Severidad | Recomendación |
|---|---|---|---|---|---|---|
| H-01 | [Descripción breve] | [Ficha] | [Comando / foto] | [Qué puede pasar] | Alta / Media / Baja | [Acción sugerida] |
| H-02 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| H-03 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| H-04 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

### 8.1 Criterio de severidad

| Severidad | Criterio |
|---|---|
| **Alta** | Afecta la disponibilidad, la integridad o la confidencialidad de datos sensibles; requiere acción antes de migrar |
| **Media** | Degrada el servicio o incumple una buena práctica; se corrige en el corto plazo |
| **Baja** | Mejora recomendable, sin impacto inmediato |

---

## Bitácora de acciones

| # | Fecha | Hora | Acción o comando | Resultado | Ejecutó | Verificó |
|---|---|---|---|---|---|---|
| 1 | [AAAA-MM-DD] | [HH:MM] | [Comando exacto] | [OK / error / limitación] | [Nombre] | [Nombre] |
| 2 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 3 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 4 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

> [!note] Por qué se registra el comando exacto
> La bitácora permite reproducir el relevamiento sin adivinar qué se hizo. Si un
> hallazgo se cuestiona, la fila dice qué comando lo produjo y quién lo verificó.

---

## Acta de inicio

```text
En [ciudad], a los [día] días del mes de [mes] de [año], a las [HH:MM], se
inicia el relevamiento técnico del servidor identificado como [equipo /
etiqueta], en [ubicación], con la presencia de:

- Responsable técnico: [nombre y apellido], [documento]
- Acompañante designado: [nombre y apellido], [cargo]

Se deja constancia de que:

1. La solicitud de autorización N.º [AAAAMMDD-NN] está firmada por Dirección.
2. El alcance autorizado es el de la solicitud y el procedimiento 07.08.
3. La intervención será de solo lectura y no modificará el equipo.
4. Se informó al acompañante el alcance, los límites y los criterios de aborto.

Firmas:

______________________________          ______________________________
Responsable técnico                      Acompañante designado
[Nombre]                                 [Nombre]
```

---

## Acta de cierre

```text
En [ciudad], a los [día] días del mes de [mes] de [año], a las [HH:MM], se
cierra el relevamiento técnico del servidor identificado como [equipo /
etiqueta].

Se deja constancia de que:

1. Se completaron las fichas [indicar cuáles] y quedaron sin completar [indicar
   cuáles y por qué].
2. No se instaló software, no se modificó configuración y no se copiaron datos
   personales.
3. Se detectaron [N] hallazgos, detallados en la ficha 8.
4. La evidencia quedó en [medio cifrado], con [N] archivos y manifiesto de
   hashes.
5. El equipo queda en el mismo estado en que se encontró, salvo [indicar
   cualquier diferencia].

Firmas:

______________________________          ______________________________
Responsable técnico                      Acompañante designado
[Nombre]                                 [Nombre]
```

---

## Control de evidencia

| Archivo | Tipo | Hash SHA-256 | Custodio | Fecha |
|---|---|---|---|---|
| [acta-inicio.pdf] | Acta | [Hash] | [Nombre] | [AAAA-MM-DD] |
| [comandos/hardware.txt] | Salida | [Hash] | [Nombre] | [AAAA-MM-DD] |
| [fotos/equipo-etiqueta.jpg] | Foto | [Hash] | [Nombre] | [AAAA-MM-DD] |
| [ ] | [ ] | [ ] | [ ] | [ ] |

> [!warning] El manifiesto se firma al cerrar
> Si un archivo se agrega después, se recalcula su hash y se registra en una fila
> nueva. No se reescribe una fila anterior.

---

## Checklist final antes de cerrar

```text
☐ La solicitud de autorización está firmada por Dirección
☐ El acompañante estuvo presente durante toda la intervención
☐ Las fichas 0 a 8 están completas o justificadas como "No verificable"
☐ No se copió ningún dato personal, clínico ni financiero
☐ No se instaló ni se modificó nada en el servidor
☐ Las fotos no muestran pantallas con datos
☐ La evidencia está cifrada y tiene manifiesto de hashes
☐ El acta de inicio y el acta de cierre están firmadas
☐ Los hallazgos tienen severidad y recomendación
☐ El equipo quedó en el mismo estado en que se encontró
```

---

## Documentos relacionados

- [[07.08 Relevamiento del Servidor del Centro]] — el procedimiento
- [[Plantilla - Solicitud de Autorización de Intervención en Servidor]] — la autorización
- [[Plantilla - Informe de Relevamiento de Servidor]] — el informe que se redacta con estos datos
- [[07.02 Requisitos de Hardware y Software]] — el requisito contra el que se compara
- [[06.07 Backups y Recuperación]] — qué se espera de un respaldo
