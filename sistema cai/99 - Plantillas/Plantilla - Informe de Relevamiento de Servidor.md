---
title: Plantilla - Informe de Relevamiento de Servidor
type: plantilla
status: vigente
tags: [cai, plantilla, informe, relevamiento, servidor, direccion]
owner: Responsable técnico
updated: 2026-11-09
related:
  - "[[07.08 Relevamiento del Servidor del Centro]]"
  - "[[Plantilla - Solicitud de Autorización de Intervención en Servidor]]"
  - "[[Plantilla - Inventario de Servidor]]"
  - "[[09.01 Manual de Dirección]]"
---

# Plantilla - Informe de Relevamiento de Servidor

> [!info] Cómo usar esta plantilla
> Se completa **después** del relevamiento, con el inventario y la evidencia a la vista.
> El informe es para Dirección: debe poder leerse sin conocimientos técnicos y debe
> permitir decidir qué hacer con el servidor.
>
> **Regla:** el informe no lleva datos personales. Si una frase necesita el nombre, el
> documento o el diagnóstico de una persona para entenderse, se reescribe en términos
> de categoría y volumen.

---

## Portada

| Campo | Valor |
|---|---|
| **Centro** | [Nombre completo del centro] |
| **Título** | Informe de Relevamiento del Servidor |
| **N.º de informe** | [AAAA-MM-DD-NN] |
| **Solicitud de autorización** | [AAAAMMDD-NN] |
| **Equipo / etiqueta** | [Identificación] |
| **Ubicación** | [Sala / rack / oficina] |
| **Fecha de la intervención** | [AAAA-MM-DD] |
| **Fecha del informe** | [AAAA-MM-DD] |
| **Autor** | [Nombre y apellido] |
| **Revisó** | [Nombre y apellido] |
| **Clasificación** | Confidencial — uso interno del centro |
| **Versión** | [1.0] |

---

## Control documental

| Versión | Fecha | Cambio | Autor | Aprobó |
|---|---|---|---|---|
| 0.1 | [AAAA-MM-DD] | Borrador inicial | [Nombre] | — |
| 1.0 | [AAAA-MM-DD] | Versión para Dirección | [Nombre] | [Nombre] |

---

## Resumen ejecutivo

> [!important] Extensión máxima: una página
> Escribir en lenguaje llano: qué se encontró, qué riesgos hay y qué se recomienda.
> Sin jerga innecesaria y sin datos personales.

```text
[Redactar entre 150 y 300 palabras. Debe responder:
- Qué equipo se relevó y en qué estado general está.
- Si el hardware alcanza para el sistema CAI o si hay que reemplazarlo.
- Qué categorías de datos aloja y si están respaldadas.
- Cuáles son los tres riesgos principales.
- Qué decisión se pide a Dirección.]
```

---

## 1. Objetivo y alcance

### 1.1 Objetivo

[Describir en una frase qué se buscó con el relevamiento.]

### 1.2 Alcance

| Incluido | Excluido |
|---|---|
| [Hardware, software, red, cuentas, respaldos, mapa de datos] | [Reparación, instalación, migración, copia de datos] |

### 1.3 Documentos de referencia

| Documento | Uso |
|---|---|
| [Solicitud de autorización N.º …] | Habilitó la intervención |
| [Inventario de servidor] | Fuente de los datos |
| [[07.02 Requisitos de Hardware y Software]] | Criterio de comparación |

---

## 2. Metodología y limitaciones

### 2.1 Método

[Describir: intervención presencial, solo lectura, acompañamiento, comandos utilizados,
registro en bitácora, evidencia cifrada.]

### 2.2 Limitaciones

| Limitación | Impacto en las conclusiones |
|---|---|
| [Herramienta no disponible] | [Qué no se pudo verificar] |
| [Ficha incompleta] | [Qué conclusión queda condicionada] |
| [Equipo en producción] | [Qué no se pudo ejecutar] |

> [!warning] Declarar las limitaciones no debilita el informe
> Lo hace auditable. Un informe que dice "todo se verificó" cuando faltó la mitad de
> los datos es un informe que no se puede usar para decidir.

---

## 3. Hardware

### 3.1 Resumen

| Aspecto | Hallazgo | ¿Cumple el requisito? |
|---|---|---|
| CPU | [Modelo y núcleos] | Sí / No / Parcial |
| RAM | [GB] | Sí / No / Parcial |
| Disco | [Tipo y capacidad] | Sí / No / Parcial |
| Fuente | [Potencia] | Sí / No / Sin dato |
| UPS | [Sí / No / Sin dato] | Sí / No / Sin dato |
| Estado físico | [Bueno / Regular / Malo] | — |

### 3.2 Comparación con el requisito

[Comparar contra [[07.02 Requisitos de Hardware y Software]] y explicar la brecha. Si el
equipo no alcanza, decir qué falta y qué implica.]

---

## 4. Software

| Aspecto | Hallazgo | Observación |
|---|---|---|
| Sistema operativo | [Distribución y versión] | [Soporte vigente / vencido] |
| Última actualización | [Fecha] | [Riesgo de seguridad] |
| Servicios activos | [Cantidad y relevantes] | [Servicios innecesarios] |
| Software instalado | [Resumen] | [Licencias / obsolescencia] |
| Antivirus / EDR | [Producto y estado] | [Cobertura] |
| Acceso remoto | [SSH / RDP / otro] | [Riesgo] |

---

## 5. Almacenamiento

| Aspecto | Hallazgo | Riesgo |
|---|---|---|
| Capacidad total | [GB] | — |
| Uso actual | [%] | [Alto / Medio / Bajo] |
| Discos con errores | [Cantidad] | [Alto / Medio / Bajo] |
| Cifrado | [Sí / No / Parcial] | [Alto / Medio / Bajo] |
| Crecimiento estimado | [GB por mes] | [Tiempo hasta llenarse] |

---

## 6. Red

| Aspecto | Hallazgo | Observación |
|---|---|---|
| IP y direccionamiento | [IP / DHCP] | [Fija / dinámica] |
| Puertos abiertos | [Lista] | [Cuáles son necesarios] |
| Firewall | [Activo / inactivo] | [Reglas relevantes] |
| Salida a internet | [Sí / No / Restringida] | [Necesidad real] |
| VPN | [Sí / No] | [Riesgo] |
| Certificados | [Vigencia] | [Renovación] |

---

## 7. Cuentas y accesos

| Aspecto | Hallazgo | Riesgo |
|---|---|---|
| Usuarios activos | [Cantidad] | — |
| Usuarios privilegiados | [Cantidad] | [Alto / Medio / Bajo] |
| Login directo de `root` | [Sí / No] | [Alto / Medio / Bajo] |
| Autenticación por contraseña | [Sí / No] | [Alto / Medio / Bajo] |
| MFA | [Sí / No / Parcial] | [Alto / Medio / Bajo] |
| Credenciales en texto plano | [Sí / No / No verificable] | [Alto / Medio / Bajo] |
| Cuentas de exempleados | [Sí / No / No verificable] | [Alto / Medio / Bajo] |

> [!danger] No incluir usuarios ni contraseñas
> Se informa la cantidad y el riesgo. Si hace falta individualizar una cuenta para que
> Dirección actúe, se entrega en un anexo confidencial separado, no en el cuerpo del
> informe.

---

## 8. Respaldos

| Aspecto | Hallazgo | ¿Cumple la política? |
|---|---|---|
| ¿Hay respaldos? | [Sí / No] | Sí / No |
| Frecuencia | [Diaria / semanal / mensual] | Sí / No |
| Retención | [Días / semanas] | Sí / No |
| Cifrado | [Sí / No] | Sí / No |
| Última ejecución exitosa | [Fecha] | Sí / No |
| Última prueba de restauración | [Fecha / nunca] | Sí / No |
| Copia fuera del edificio | [Sí / No] | Sí / No |

[Explicar el riesgo si no hay respaldo probado. Ver [[06.07 Backups y Recuperación]].]

---

## 9. Mapa de datos

> [!danger] Solo agregados
> Esta sección no contiene nombres, documentos, diagnósticos ni importes. Solo
> categorías, cantidades y tamaños.

| Categoría | Dónde está | Volumen | Sensibilidad | Respaldo | Observación |
|---|---|---|---|---|---|
| Identificatorios | [Sistema / carpeta] | [N registros / GB] | Alta | Sí / No | [ ] |
| Clínicos | [ ] | [ ] | Muy alta | [ ] | [ ] |
| Financieros | [ ] | [ ] | Alta | [ ] | [ ] |
| Documentos | [ ] | [ ] | Alta | [ ] | [ ] |
| Credenciales | [ ] | [ ] | Muy alta | [ ] | [ ] |
| Otros | [ ] | [ ] | Media / Baja | [ ] | [ ] |

### 9.1 Qué implica este mapa

[Explicar qué categorías son críticas, cuáles están duplicadas, cuáles no tienen
respaldo y cuáles requieren una decisión de Dirección antes de migrar.]

---

## 10. Hallazgos y riesgos

### 10.1 Matriz de riesgo

| Probabilidad \ Impacto | Bajo | Medio | Alto |
|---|---|---|---|
| **Alta** | Medio | Alto | Alto |
| **Media** | Bajo | Medio | Alto |
| **Baja** | Bajo | Bajo | Medio |

### 10.2 Hallazgos

| ID | Hallazgo | Evidencia | Probabilidad | Impacto | Riesgo | Prioridad |
|---|---|---|---|---|---|---|
| H-01 | [Descripción] | [Ficha / comando] | Alta / Media / Baja | Alto / Medio / Bajo | Alto / Medio / Bajo | 1 |
| H-02 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| H-03 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| H-04 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

### 10.3 Los tres riesgos principales

1. **[Riesgo 1]:** [qué puede pasar, a quién afecta y por qué es prioritario].
2. **[Riesgo 2]:** [ ].
3. **[Riesgo 3]:** [ ].

---

## 11. Recomendaciones

| ID | Recomendación | Prioridad | Esfuerzo | Responsable | Plazo | Criterio de cierre |
|---|---|---|---|---|---|---|
| R-01 | [Acción concreta] | Inmediata / 30 días / 90 días | Bajo / Medio / Alto | [Rol] | [Fecha] | [Cómo se verifica] |
| R-02 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| R-03 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| R-04 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

### 11.1 Criterio de prioridad

| Prioridad | Cuándo aplica |
|---|---|
| **Inmediata** | Riesgo alto para datos sensibles, disponibilidad o integridad; se actúa antes de migrar |
| **30 días** | Degrada el servicio o incumple una buena práctica; se corrige en el corto plazo |
| **90 días** | Mejora recomendable; se planifica sin urgencia |

---

## 12. Conclusiones y siguiente paso

### 12.1 Conclusión general

[Responder: ¿el servidor sirve para el CAI? ¿Hay que reemplazarlo? ¿Se puede migrar
con las correcciones indicadas?]

### 12.2 Decisión que se solicita a Dirección

| Opción | Descripción | Consecuencia |
|---|---|---|
| A | [Aprobar el informe y ejecutar las recomendaciones inmediatas] | [ ] |
| B | [Solicitar una segunda intervención acotada] | [ ] |
| C | [Iniciar el reemplazo del equipo] | [ ] |

### 12.3 Siguiente paso propuesto

[Una sola acción concreta, con responsable y fecha.]

---

## 13. Anexos

| Anexo | Contenido | Ubicación |
|---|---|---|
| A | Inventario completo | [[Plantilla - Inventario de Servidor]] completado |
| B | Bitácora de acciones | Ficha de bitácora |
| C | Acta de inicio y cierre | Fichas de actas |
| D | Manifiesto de hashes | `hashes.sha256` |
| E | Evidencia fotográfica | Medio cifrado |
| F | Detalle confidencial de cuentas | Anexo separado, solo Dirección |

---

## Declaración de ausencia de datos personales

```text
Declaro que este informe no contiene nombres, documentos, domicilios, teléfonos,
correos, diagnósticos, contenidos clínicos, importes individuales ni credenciales
de alumnos, familias o profesionales. La información se presenta en forma
agregada, por categoría y volumen, conforme al procedimiento 07.08 y a la
política de manejo de datos del centro.

[Nombre y apellido]
[Cargo]
[Fecha]
```

---

## Aprobación

| Rol | Nombre | Firma | Fecha |
|---|---|---|---|
| **Autor** | [Nombre] | | [AAAA-MM-DD] |
| **Revisó** | [Nombre] | | [AAAA-MM-DD] |
| **Dirección** | [Nombre] | | [AAAA-MM-DD] |

---

## Documentos relacionados

- [[07.08 Relevamiento del Servidor del Centro]] — el procedimiento que originó este informe
- [[Plantilla - Solicitud de Autorización de Intervención en Servidor]] — la autorización
- [[Plantilla - Inventario de Servidor]] — la fuente de los datos
- [[07.02 Requisitos de Hardware y Software]] — el criterio de comparación
- [[06.07 Backups y Recuperación]] — la política de respaldos
- [[09.01 Manual de Dirección]] — el destinatario del informe
