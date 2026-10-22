#!/usr/bin/env python3
"""
cai-log.py — Registro de cambios y bitácora de sesiones del proyecto CAI
===============================================================================

Escribe entradas **nuevas** en:

  sistema cai/12 - Registro de Cambios/12.02 Registro de Cambios.md
  sistema cai/12 - Registro de Cambios/12.03 Bitácora de Sesiones con IA.md

El script **solo agrega**. No edita ni borra entradas existentes: eso es lo que
hace que el registro sirva como histórico. Las correcciones se registran como
una entrada nueva.

Uso rápido
----------
    bin/cai-log.py cambio \
        --tipo edición --severidad N2 \
        --motivo "Corregir el wikilink roto del ADR-0006 en 03.05" \
        --archivos "sistema cai/03 - Modelo de Datos/03.05 Planes de Atención y Notas Clínicas.md" \
        --rastreo "ADR-0006" \
        --verificacion "bin/validate-vault.py -> 0 errores"

    bin/cai-log.py sesion \
        --operador "Cesar Benitez" \
        --modelo "opencode/big-pickle" --variante default \
        --agente build \
        --objetivo "Sanear los enlaces de 03 - Modelo de Datos" \
        --area "03 - Modelo de Datos" \
        --resultado completado

Orden de los argumentos largos: da igual. Los valores con espacios van entre
comillas.

El modelo se toma de `--modelo`, o de la variable de entorno `CAI_MODELO`
(formato `proveedor/modelo#variante`), o de `CAI_MODELO` + `CAI_VARIANTE`.
Sin modelo no hay atribución, y sin atribución la entrada no se escribe.

Referencia: AGENTS.md · 12.01 Política de Cambios y Trazabilidad
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from typing import NoReturn

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAULT = os.path.join(RAIZ, "sistema cai")
REGISTRO = os.path.join(VAULT, "12 - Registro de Cambios", "12.02 Registro de Cambios.md")
BITACORA = os.path.join(VAULT, "12 - Registro de Cambios", "12.03 Bitácora de Sesiones con IA.md")

TIPOS = {
    "creación",
    "edición",
    "renombre",
    "movimiento",
    "deprecación",
    "reversión",
    "decisión",
    "infraestructura",
    "proceso",
}
SEVERIDADES = {"N1", "N2", "N3", "N4"}
RESULTADOS = {"completado", "parcial", "fallido"}
ESTADOS = {"aplicado", "fallido", "revertido", "pendiente de revisión"}

SIN_DATO = "—"


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------


def fallar(mensaje: str) -> NoReturn:
    print(f"ERROR: {mensaje}", file=sys.stderr)
    sys.exit(1)


def leer(ruta: str) -> str:
    if not os.path.isfile(ruta):
        fallar(f"no existe el archivo: {ruta}")
    with open(ruta, encoding="utf-8") as manejador:
        return manejador.read()


def escribir(ruta: str, texto: str) -> None:
    with open(ruta, "w", encoding="utf-8", newline="\n") as manejador:
        manejador.write(texto)


def celda(valor: str) -> str:
    """Prepara un valor para una celda de tabla Markdown."""
    limpio = " ".join(str(valor).split())
    return limpio.replace("|", "\\|")


def ahora() -> str:
    """Fecha local en el formato del proyecto: 2026-10-22 12:05 (−03)."""
    momento = datetime.now().astimezone()
    desfase = momento.strftime("%z")
    signo = "−" if desfase.startswith("-") else "+"
    horas, minutos = desfase[1:3], desfase[3:5]
    zona = f"{signo}{horas}" if minutos == "00" else f"{signo}{horas}:{minutos}"
    return f"{momento.strftime('%Y-%m-%d %H:%M')} ({zona})"


def hoy() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d")


def resolver_modelo(modelo: str | None, variante: str | None) -> tuple[str, str, str]:
    """
    Devuelve (proveedor, modelo, variante) a partir de las opciones o del entorno.

    Acepta `opencode/big-pickle#default`, `opencode/big-pickle` o solo
    `big-pickle` (en ese caso se rechaza: sin proveedor la atribución es
    incompleta, ver 12.03 §3.1).
    """
    crudo = modelo or os.environ.get("CAI_MODELO", "")
    if not crudo:
        fallar(
            "falta el modelo de IA. Usá --modelo proveedor/modelo#variante "
            "o definí CAI_MODELO. Sin modelo no hay atribución (AGENTS.md §3)."
        )
    crudo = crudo.strip()
    if "#" in crudo:
        crudo, variante = crudo.split("#", 1)
    if "/" not in crudo:
        fallar(
            f"el modelo «{crudo}» no incluye el proveedor. "
            "La forma canónica es proveedor/modelo#variante (12.03 §3.1)."
        )
    proveedor, nombre = crudo.split("/", 1)
    return proveedor.strip(), nombre.strip(), (variante or "").strip()


def siguiente_id(texto: str, prefijo: str) -> str:
    """
    Calcula el próximo ID correlativo del año en curso.

    Solo mira los encabezados de entrada y las filas de índice: el texto de
    ejemplo del documento no debe consumir números.
    """
    anio = datetime.now().astimezone().year
    patron = re.compile(r"^\s*(?:##|\|)\s*" + re.escape(prefijo) + r"-" + str(anio) + r"-(\d{3})")
    numeros = [int(n) for n in patron.findall(texto)]
    siguiente = (max(numeros) + 1) if numeros else 1
    return f"{prefijo}-{anio}-{siguiente:03d}"


def insertar_entrada(texto: str, marcador: str, bloque: str) -> str:
    """Inserta el bloque justo después de `<!-- MARCADOR:START -->`."""
    inicio = f"<!-- {marcador}:START -->"
    if inicio not in texto:
        fallar(f"falta el marcador {inicio} en el documento")
    posicion = texto.index(inicio) + len(inicio)
    return texto[:posicion] + bloque + texto[posicion:]


def insertar_en_indice(texto: str, seccion: str, fila: str) -> str:
    """Agrega la fila arriba de todo en la tabla de la sección indicada."""
    if seccion not in texto:
        fallar(f"no se encontró la sección «{seccion}» para actualizar el índice")
    desde = texto.index(seccion)
    lineas = texto[desde:].split("\n")

    # La tabla empieza en la primera línea que empieza con «|».
    for posicion, linea in enumerate(lineas):
        if linea.strip().startswith("|"):
            # posicion     = encabezado
            # posicion + 1 = separador
            corte = desde + len("\n".join(lineas[: posicion + 2])) + 1
            return texto[:corte] + fila + "\n" + texto[corte:]
    fallar(f"la sección «{seccion}» no tiene tabla de índice")


def verificacion(valor: str) -> str:
    """Pone el comando entre acentos graves si el valor no los trae."""
    if not valor:
        return "pendiente"
    if "`" in valor:
        return valor
    for separador in (" -> ", " → "):
        if separador in valor:
            comando, _, resultado = valor.partition(separador)
            return f"`{comando.strip()}` → {resultado.strip()}"
    return valor


def actualizar_fecha(texto: str) -> str:
    return re.sub(r"(?m)^updated:.*$", f"updated: {hoy()}", texto, count=1)


# ---------------------------------------------------------------------------
# Subcomando: cambio
# ---------------------------------------------------------------------------


def comando_cambio(args: argparse.Namespace) -> int:
    if args.tipo not in TIPOS:
        fallar(f"tipo inválido «{args.tipo}». Válidos: {', '.join(sorted(TIPOS))}")
    if args.severidad not in SEVERIDADES:
        fallar(f"severidad inválida «{args.severidad}». Válidas: {', '.join(sorted(SEVERIDADES))}")
    if args.estado not in ESTADOS:
        fallar(f"estado inválido «{args.estado}». Válidos: {', '.join(sorted(ESTADOS))}")
    if len(args.motivo.split()) < 10:
        fallar(
            "el motivo tiene menos de 10 palabras: no explica nada. "
            "Escribí por qué se hizo el cambio, no qué se cambió (12.02 §4.1)."
        )
    if args.severidad in {"N3", "N4"} and not args.rastreo:
        fallar(
            f"un cambio {args.severidad} exige rastreo (ADR, RF, RN o P). "
            "Ver 12.01 §5 y AGENTS.md §4."
        )

    proveedor, nombre, variante = resolver_modelo(args.modelo, args.variante)
    autor = args.autor or os.environ.get("CAI_OPERADOR", "")
    if not autor:
        fallar("falta el autor. Usá --autor o definí CAI_OPERADOR.")

    texto = leer(REGISTRO)
    identificador = args.id or siguiente_id(texto, "REG")
    if re.search(rf"^##\s*{re.escape(identificador)}\b", texto, re.M):
        fallar(f"el ID {identificador} ya existe: el registro es de solo agregar")
    sesion = args.sesion or os.environ.get("CAI_SESION", "") or SIN_DATO
    if sesion != SIN_DATO and sesion not in leer(BITACORA):
        fallar(f"la sesión {sesion} no existe en 12.03. Registrala primero con `cai-log.py sesion`")

    modelo = f"`{proveedor}/{nombre}`" + (f" (variante `{variante}`)" if variante else "")
    archivos = ", ".join(f"`{a.strip()}`" for a in args.archivos.split(",") if a.strip())
    if not archivos:
        fallar("falta --archivos: declarar el alcance antes de empezar (AGENTS.md §2.1)")

    resumen = args.resumen or args.motivo.split(".")[0][:90]

    bloque = f"""
---

## {identificador} · {args.titulo or resumen}

| Campo | Valor |
|---|---|
| **Fecha** | {ahora()} |
| **Tipo** | {args.tipo} |
| **Severidad** | {args.severidad} |
| **Autor** | {celda(autor)} · IA {modelo} |
| **Sesión** | {sesion} |
| **Motivo** | {celda(args.motivo)} |
| **Archivos** | {archivos} |
| **Rastreo** | {celda(args.rastreo or SIN_DATO)} |
| **Verificación** | {celda(verificacion(args.verificacion))} |
| **Estado** | {args.estado} |
| **Pendiente** | {celda(args.pendiente or SIN_DATO)} |
"""

    fila = (
        f"| {identificador} | {hoy()} | {args.tipo} | {args.severidad} "
        f"| {celda(resumen)} | {sesion} |"
    )

    if args.seco:
        print(bloque)
        print(fila)
        return 0

    texto = insertar_entrada(texto, "REG-ENTRIES", bloque)
    texto = actualizar_fecha(texto)
    escribir(REGISTRO, texto)

    # El índice se actualiza en un segundo paso para que un fallo no deje
    # la entrada escrita sin su fila.
    texto = leer(REGISTRO)
    texto = insertar_en_indice(texto, "## 3. Índice de entradas", fila)
    escribir(REGISTRO, texto)

    print(f"OK  {identificador} registrado en 12.02")
    print(f"    modelo: {proveedor}/{nombre}" + (f"#{variante}" if variante else ""))
    print("    siguiente paso: verificá y commiteá con el ID en el mensaje")
    return 0


# ---------------------------------------------------------------------------
# Subcomando: sesion
# ---------------------------------------------------------------------------


def comando_sesion(args: argparse.Namespace) -> int:
    if args.resultado not in RESULTADOS:
        fallar(f"resultado inválido «{args.resultado}». Válidos: {', '.join(sorted(RESULTADOS))}")
    if not args.operador:
        fallar("falta --operador: la sesión se atribuye a una persona concreta")

    proveedor, nombre, variante = resolver_modelo(args.modelo, args.variante)

    texto = leer(BITACORA)
    identificador = args.id or siguiente_id(texto, "SES")
    if re.search(rf"^##\s*{re.escape(identificador)}\b", texto, re.M):
        fallar(f"el ID {identificador} ya existe: la bitácora es de solo agregar")

    fin = args.fin or ahora()
    archivos = ", ".join(f"`{a.strip()}`" for a in (args.archivos or "").split(",") if a.strip())

    bloque = f"""
---

## {identificador} · {args.titulo or args.objetivo[:80]}

| Campo | Valor |
|---|---|
| **Inicio** | {args.inicio or ahora()} |
| **Fin** | {fin} |
| **Operador** | {celda(args.operador)} |
| **Herramienta** | {celda(args.herramienta)} · agente `{args.agente}` |
| **Proveedor** | `{proveedor}` |
| **Modelo** | `{nombre}` |
| **Variante** | {(f'`{variante}`' if variante else SIN_DATO)} |
| **Objetivo** | {celda(args.objetivo)} |
| **Área** | {celda(args.area)} |
| **Archivos tocados** | {archivos or SIN_DATO} |
| **Verificación** | {celda(verificacion(args.verificacion))} |
| **Resultado** | {args.resultado} |
| **Entradas de registro** | {celda(args.entradas or "— todavía ninguna")} |
| **Pendiente** | {celda(args.pendiente or SIN_DATO)} |
"""

    modelo_completo = f"{proveedor}/{nombre}" + (f"#{variante}" if variante else "")
    fila = (
        f"| {identificador} | {hoy()} | {celda(args.operador)} | {celda(args.herramienta)} "
        f"| `{modelo_completo}` | {args.resultado} | {celda(args.entradas or SIN_DATO)} |"
    )

    if args.seco:
        print(bloque)
        print(fila)
        return 0

    texto = insertar_entrada(texto, "SES-ENTRIES", bloque)
    texto = actualizar_fecha(texto)
    escribir(BITACORA, texto)

    texto = leer(BITACORA)
    texto = insertar_en_indice(texto, "## 4. Índice de sesiones", fila)
    escribir(BITACORA, texto)

    print(f"OK  {identificador} registrada en 12.03")
    print(f"    modelo: {proveedor}/{nombre}" + (f"#{variante}" if variante else ""))
    print(f"    exportá CAI_SESION={identificador} para que los cambios se enlacen solos")
    return 0


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cai-log.py",
        description="Registra un cambio (12.02) o una sesión de IA (12.03).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ejemplos:\n"
            "  bin/cai-log.py cambio --tipo edición --severidad N1 \\\n"
            '      --motivo "Corregir tres enlaces rotos de 02 - Arquitectura" \\\n'
            '      --archivos "sistema cai/02 - Arquitectura/02.01 Arquitectura General.md"\n'
            "\n"
            "  bin/cai-log.py sesion --operador 'Cesar Benitez' \\\n"
            "      --modelo opencode/big-pickle#default --resultado completado\n"
        ),
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    cambio = sub.add_parser("cambio", help="Agrega una entrada a 12.02 (Registro de Cambios)")
    cambio.add_argument("--tipo", required=True, help=" | ".join(sorted(TIPOS)))
    cambio.add_argument("--severidad", required=True, help=" | ".join(sorted(SEVERIDADES)))
    cambio.add_argument("--motivo", required=True, help="Por qué se hizo, en una o dos frases")
    cambio.add_argument("--archivos", required=True, help="Rutas separadas por coma")
    cambio.add_argument("--rastreo", default="", help="ADR, RF, RN o P que originan el cambio")
    cambio.add_argument("--verificacion", default="", help="Comando y resultado")
    cambio.add_argument("--autor", default="", help="Persona responsable")
    cambio.add_argument("--sesion", default="", help="SES-AAAA-NNN (por defecto CAI_SESION)")
    cambio.add_argument("--titulo", default="", help="Título corto de la entrada")
    cambio.add_argument("--resumen", default="", help="Resumen para la tabla de índice")
    cambio.add_argument("--estado", default="aplicado", help=" | ".join(sorted(ESTADOS)))
    cambio.add_argument("--pendiente", default="", help="Qué queda abierto")
    cambio.add_argument("--modelo", default="", help="proveedor/modelo#variante")
    cambio.add_argument("--variante", default="", help="Variante del modelo")
    cambio.add_argument("--id", default="", help="ID explícito (solo para recuperar un hueco)")
    cambio.add_argument("--seco", action="store_true", help="Muestra la entrada sin escribirla")
    cambio.set_defaults(func=comando_cambio)

    sesion = sub.add_parser("sesion", help="Agrega una entrada a 12.03 (Bitácora de IA)")
    sesion.add_argument("--operador", required=True)
    sesion.add_argument("--objetivo", required=True)
    sesion.add_argument("--area", required=True)
    sesion.add_argument("--modelo", default="", help="proveedor/modelo#variante")
    sesion.add_argument("--variante", default="", help="Variante del modelo")
    sesion.add_argument("--agente", default="build", help="Modo del agente (build, plan, …)")
    sesion.add_argument(
        "--herramienta", default=os.environ.get("CAI_HERRAMIENTA", "OpenCode"), help="Harness y versión"
    )
    sesion.add_argument("--resultado", default="completado", help=" | ".join(sorted(RESULTADOS)))
    sesion.add_argument("--archivos", default="", help="Rutas separadas por coma")
    sesion.add_argument("--verificacion", default="", help="Comando y resultado")
    sesion.add_argument("--entradas", default="", help="IDs REG generados")
    sesion.add_argument("--inicio", default="", help="YYYY-MM-DD HH:MM (±ZZ)")
    sesion.add_argument("--fin", default="", help="YYYY-MM-DD HH:MM (±ZZ)")
    sesion.add_argument("--titulo", default="", help="Título corto de la entrada")
    sesion.add_argument("--pendiente", default="", help="Qué queda abierto")
    sesion.add_argument("--id", default="", help="ID explícito")
    sesion.add_argument("--seco", action="store_true", help="Muestra la entrada sin escribirla")
    sesion.set_defaults(func=comando_sesion)

    return parser


def main(argv: list[str]) -> int:
    args = construir_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
