# DESIGN.md

Este archivo es la dirección del proyecto para cualquier IA que toque esta base.
No reemplaza `AGENTS.md`; lo complementa y da contexto operativo para que la IA no genere "slop" genérico.

## Propósito del proyecto

Este repositorio no es un producto de marketing ni una demo. Es una bóveda documental de gobernanza, arquitectura, requisitos y trazabilidad para el Sistema Integral de Gestión del Centro de Atención Inclusiva (CAI).

La IA debe actuar como apoyo técnico y documental, no como autora creativa sin evidencia.

## Principios de diseño

1. Honestidad antes que brillo
   - No inventar cifras, métricas, resultados, fechas, versiones o estado del proyecto si no hay evidencia.
   - Si no hay fuente, decirlo claramente o dejarlo sin afirmar.

2. Dirección real, no belleza vacía
   - La IA debe producir contenido útil, claro y alineado con el dominio del proyecto.
   - No agregar “AI polish” ni adornos que no sirvan para entender el sistema.

3. Mantener el tono del dominio
   - Documentación técnica, no copy de lanzamiento ni “hero section”.
   - Terminología del centro, la arquitectura y la gobernanza del proyecto.

4. Ojo a la frontera del alcance
   - No tocar módulos ajenos a la tarea.
   - No expandir el problema por gusto.
   - Si algo no está en el alcance, se anota y se deja fuera.

5. Trazabilidad por defecto
   - El trabajo debe poder responder: qué se hizo, por qué, con qué modelo, qué validación se ejecutó.
   - Si falta evidencia, el trabajo no se cierra como completado.

6. No hay “código de relleno”
   - No comments genéricos, no banners, no “sección de ejemplo” que no aporta nada.
   - Si un bloque no añade valor funcional o documental, no existe.

7. Verificación antes de cierre
   - La salida debe pasar los checks del proyecto antes de considerarse finalizada.
   - Si la validación no se ejecuta, la sesión queda parcial o fallida.

## Restricciones de salida

La IA debe evitar:

- nombres o modelos inventados
- métricas fake o “ROI” artificial
- textos tipo marketing, hype o buzzwords sin base
- comentarios redundantes en código o documentación
- reescrituras grandes sin necesidad
- cambios de estilo que no correspondan al alcance
- duplicar reglas ya establecidas
- cambiar arquitectura o decisiones sin trazabilidad y rastreo

## Evidencia requerida

Todo cambio debe incluir, al menos:

- objetivo real
- alcance exacto
- archivos tocados
- validación ejecutada
- modelo usado
- resultado observado

## Revisión de calidad del proyecto

Antes de cerrar una sesión, hay que comprobar:

- que el alcance siguió siendo el pedido
- que no hubo inventos ni slop
- que la validación se ejecutó
- que la bitácora y el registro reflejan la verdad
- que queda claro qué falta si el trabajo está incompleto

## Thermos-style review (para más adelante)

Más adelante conviene un “review en segunda pasada” que inspeccione:

- correctness
- seguridad
- scope
- mantenibilidad
- inventos del agente
- deuda añadida
- cambios fuera del alcance

Esto puede hacerse como una revisión automática o simulada por subagentes, pero no reemplaza la gobernanza documental actual.

## Checklist pre-vuelo antes de tocar el proyecto

Antes de empezar cualquier sesión, la IA debe verificar estas 7 cosas:

1. Leer `AGENTS.md` y confirmar el alcance real de la tarea.
2. Declarar el objetivo en una frase verificable: qué se va a hacer y qué no.
3. Identificar exactamente los archivos que se van a tocar y/o los documentos que se leen como fuente.
4. Comprobar si hay ADR, requisito o decisión relevante que afecte la salida.
5. Registrarse explícitamente con el proveedor y el modelo usado, sin abreviaturas ambiguas.
6. Decidir qué validación corresponde a esa sesión antes de ejecutarla.
7. Dejar la sesión abierta a revisión: si hay algo no comprobado, se anota como pendiente y no como completado.

Si alguna de estas 7 no se puede afirmar con evidencia, la sesión no empieza de forma limpia.

## Revisión en segunda pasada (Thermos-style)

Toda salida de IA que modifique documentación o código debe pasar una revisión de cierre con estas preguntas:

- ¿Qué se hizo exactamente y qué quedó fuera del alcance?
- ¿Hay evidencia de que esto es verdad y no un invento?
- ¿Se usaron nombres, modelos o fechas reales y verificables?
- ¿La validación se ejecutó y el resultado es el que se dice?
- ¿Se añadió slop, adornos, marketing o lenguaje genérico sin valor?
- ¿Se tocó una frontera o módulo ajeno al problema planteado?
- ¿La sesión, el registro y la bitácora coinciden entre sí?
- ¿Hay deuda técnica o documentación que debería quedar anotada como pendiente?

La idea no es “hacer más revisión por estética”, sino evitar que la IA convierta un trabajo concreto en una salida difusa, imprecisa o demasiado amplia. En otras palabras: la segunda pasada vigila la verdad, el alcance y la disciplina.

## Regla operativa de cierre de sesión

Una sesión solo se considera cerrada si:

- el objetivo se cumplió o se declaró explícitamente como incompleto
- quedó claro qué archivos se tocaron
- el resultado de la validación se registró
- la bitácora y el registro reflejan la verdad del trabajo
- no quedaron afirmaciones sin base
- se dejó pendiente lo que no se pudo verificar

## Señales de anti-slop

La IA debe evitar automáticamente:

- cifras sin fuente
- resultados que no se midieron
- modelos ambiguos o inventados
- texto “bonito” que no aporta conocimiento
- repetir reglas ya existentes sin aportar criterio nuevo
- ampliar la solución para “hacerla más completa” sin pedido
- cerrar trabajo sin prueba o validación

Cuando aparezcan estas señales, el correcto es recortar, aclarar y volver a la evidencia.

## Qué se cumple con este documento

Este archivo no reemplaza `AGENTS.md`; complementa la política para que la IA tenga un criterio operativo claro. En práctica, se usa como una guía de trabajo para que cualquier agente:

- empiece con un objetivo acotado
- no invente hechos ni autoría
- registre la evidencia antes de cerrar
- haga una segunda revisión de corrección y alcance
- deje la salida útil, verificable y no decorativa
