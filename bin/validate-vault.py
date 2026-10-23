#!/usr/bin/env python3
"""
validate-vault.py — Validador de la bóveda del proyecto CAI
===============================================================================
Comprueba que la documentación cumple las convenciones de
`sistema cai/00 - Inicio/00.01 Convenciones de la Vault.md`:

  1. Frontmatter completo y coherente (title/type/status/tags/owner/updated).
  2. Wikilinks que resuelven (no hay destinos rotos).
  3. Tablas Markdown bien formadas (mismo número de columnas en todas las filas).
  4. Sin caracteres CJK, cirílicos ni fragmentos de otro idioma.
  5. Aviso: documentos que no están referenciados desde ningún índice.

Uso:
    bin/validate-vault.py                 # valida "sistema cai/"
    bin/validate-vault.py --vault RUTA    # valida otra carpeta
    bin/validate-vault.py --quiet         # solo errores
    bin/validate-vault.py --json           # salida legible por máquina

Salida:
    0  todo bien (puede haber avisos)
    1  hay errores que impiden publicar
    2  error de uso del script

Referencia: AGENTS.md · 12.01 Política de Cambios y Trazabilidad
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from typing import Iterable

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

VAULT_POR_DEFECTO = "sistema cai"
CARPETAS_IGNORADAS = {".obsidian", ".git", ".cai", "node_modules", "vendor", ".trash"}

CAMPOS_OBLIGATORIOS = ["title", "type", "status", "tags", "owner", "updated"]
ESTADOS_VALIDOS = {"borrador", "vigente", "deprecated", "superseded"}
# Los ADR usan sus propios estados (ver 00.01 §4 y Plantilla - ADR).
ESTADOS_ADR = {"borrador", "aceptado", "revisado", "reemplazado", "descartado"}

# Rangos Unicode que no pertenecen al español ni a la notación técnica del proyecto.
RANGOS_PROHIBIDOS = [
    (0x0400, 0x04FF, "cirílico"),
    (0x0500, 0x052F, "cirílico suplementario"),
    (0x2DE0, 0x2DFF, "cirílico extendido"),
    (0x3040, 0x30FF, "japonés (kana)"),
    (0x3400, 0x4DBF, "CJK extendido A"),
    (0x4E00, 0x9FFF, "CJK unificado"),
    (0xAC00, 0xD7AF, "coreano (hangul)"),
    (0xF900, 0xFAFF, "CJK compatibilidad"),
    (0xFF00, 0xFFEF, "ancho completo"),
]

# Palabras inglesas que no deberían aparecer sueltas en la prosa en español.
# Solo se usan como aviso: el escáner de diccionarios hace el resto.
SOSPECHOSAS = re.compile(
    r"\b(?:the|this|that|with|from|which|there|their|would|should|could|"
    r"actually|another|reader|historical|failure|strangely|creates)\b",
    re.IGNORECASE,
)

# El texto entre comillas suele citar etiquetas de interfaz en inglés.
# Se excluye del escaneo de idioma para no dar falsos positivos.
CITAS = re.compile(r"\"[^\"\n]*\"|“[^”\n]*”|«[^»\n]*»")


# ---------------------------------------------------------------------------
# Modelo de resultado
# ---------------------------------------------------------------------------


@dataclass
class Problema:
    archivo: str
    linea: int
    regla: str
    mensaje: str
    severidad: str = "error"  # error | aviso


@dataclass
class Resultado:
    documentos: int = 0
    wikilinks: int = 0
    problemas: list[Problema] = field(default_factory=list)

    def add(self, *args, **kwargs) -> None:
        self.problemas.append(Problema(*args, **kwargs))

    @property
    def errores(self) -> list[Problema]:
        return [p for p in self.problemas if p.severidad == "error"]

    @property
    def avisos(self) -> list[Problema]:
        return [p for p in self.problemas if p.severidad == "aviso"]


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------


def normalizar(texto: str) -> str:
    """Minúsculas y sin acentos, para comparar nombres de archivo."""
    sin_acentos = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )
    return sin_acentos.lower().strip()


def sin_prefijo(nombre: str) -> str:
    """Quita el prefijo `NN.MM ` o `NN ` de un nombre de archivo."""
    return re.sub(r"^\d+(\.\d+)?\s*[-–]?\s*", "", nombre).strip()


def recorrer_markdown(raiz: str) -> Iterable[str]:
    for actual, carpetas, archivos in os.walk(raiz):
        carpetas[:] = [c for c in carpetas if c not in CARPETAS_IGNORADAS]
        if any(parte in CARPETAS_IGNORADAS for parte in actual.split(os.sep)):
            continue
        for archivo in sorted(archivos):
            if archivo.endswith(".md"):
                yield os.path.join(actual, archivo)


def quitar_bloques_de_codigo(texto: str) -> str:
    """Reemplaza bloques ``` y `código en línea` por espacios, conservando saltos."""
    texto = re.sub(r"```.*?```", lambda m: "\n" * m.group(0).count("\n"), texto, flags=re.S)
    texto = re.sub(r"`[^`\n]*`", "", texto)
    return texto


def destinos_wikilink(texto: str) -> Iterable[tuple[int, str]]:
    """Genera (línea, destino) por cada wikilink, sin alias ni ancla."""
    for numero, linea in enumerate(texto.split("\n"), start=1):
        for coincidencia in re.finditer(r"\[\[([^\]]+)\]\]", linea):
            destino = coincidencia.group(1).split("|")[0].split("#")[0].strip()
            if destino:
                yield numero, destino


def leer_frontmatter(texto: str) -> tuple[dict[str, str], int]:
    """Devuelve (campos, número de líneas del bloque)."""
    if not texto.startswith("---"):
        return {}, 0
    fin = texto.find("\n---", 3)
    if fin == -1:
        return {}, 0
    bloque = texto[3:fin]
    campos: dict[str, str] = {}
    clave_actual = None
    for linea in bloque.split("\n"):
        if not linea.strip():
            continue
        if re.match(r"^[A-Za-z_][\w-]*:", linea):
            clave, _, valor = linea.partition(":")
            clave_actual = clave.strip()
            campos[clave_actual] = valor.strip()
        elif linea.startswith((" ", "\t", "-")) and clave_actual:
            campos[clave_actual] = (campos[clave_actual] + " " + linea.strip()).strip()
    return campos, bloque.count("\n") + 2


# ---------------------------------------------------------------------------
# Comprobaciones
# ---------------------------------------------------------------------------


def comprobar_frontmatter(ruta: str, texto: str, res: Resultado) -> None:
    campos, _ = leer_frontmatter(texto)
    nombre = os.path.splitext(os.path.basename(ruta))[0]

    if not campos:
        res.add(ruta, 1, "frontmatter", "Falta el bloque de frontmatter (--- … ---)", "error")
        return

    for campo in CAMPOS_OBLIGATORIOS:
        if campo not in campos or not campos[campo]:
            res.add(ruta, 1, "frontmatter", f"Falta el campo obligatorio `{campo}`", "error")

    titulo = campos.get("title", "").strip('"').strip("'")
    esperado = sin_prefijo(nombre)
    if titulo and normalizar(titulo) != normalizar(esperado):
        res.add(
            ruta,
            1,
            "frontmatter",
            f"`title` («{titulo}») no coincide con el nombre del archivo sin prefijo («{esperado}»)",
            "error",
        )

    estado = campos.get("status", "").strip().strip('"').strip("'")
    validos = ESTADOS_ADR if nombre.startswith("ADR-") else ESTADOS_VALIDOS
    if estado and estado not in validos:
        res.add(
            ruta,
            1,
            "frontmatter",
            f"`status` inválido («{estado}»). Válidos: {', '.join(sorted(validos))}",
            "error",
        )

    actualizado = campos.get("updated", "").strip()
    if actualizado and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", actualizado):
        res.add(
            ruta,
            1,
            "frontmatter",
            f"`updated` debe tener formato YYYY-MM-DD (vale «{actualizado}»)",
            "error",
        )


def comprobar_wikilinks(ruta: str, limpio: str, indice: dict[str, str], res: Resultado) -> None:
    for numero, destino in destinos_wikilink(limpio):
        res.wikilinks += 1
        if normalizar(destino) in indice:
            continue
        res.add(ruta, numero, "wikilinks", f"Enlace roto: [[{destino}]]", "error")


def comprobar_tablas(ruta: str, limpio: str, res: Resultado) -> None:
    """Valida que todas las filas de una tabla tengan las mismas columnas."""
    lineas = limpio.split("\n")

    def celdas(linea: str) -> int:
        # Los pipes escapados (\|) no separan celdas.
        return len(re.split(r"(?<!\\)\|", linea.strip().strip("|")))

    bloque: list[tuple[int, str]] = []
    inicio = 0
    for numero, linea in enumerate(lineas, start=1):
        desnuda = linea.strip()
        if desnuda.startswith("|") and desnuda.count("|") >= 2:
            if not bloque:
                inicio = numero
            bloque.append((numero, desnuda))
            continue
        if bloque:
            _validar_bloque(ruta, bloque, inicio, celdas, res)
            bloque = []
    if bloque:
        _validar_bloque(ruta, bloque, inicio, celdas, res)


def _validar_bloque(ruta, bloque, inicio, celdas, res: Resultado) -> None:
    if len(bloque) < 2:
        return
    esperadas = celdas(bloque[0][1])
    separador = bloque[1][1]
    if not re.fullmatch(r"\|?[\s:|-]+\|?", separador):
        res.add(
            ruta,
            bloque[1][0],
            "tablas",
            "Falta la fila separadora `|---|` después del encabezado",
            "error",
        )
        return
    for numero, linea in bloque[2:]:
        obtenidas = celdas(linea)
        if obtenidas != esperadas:
            res.add(
                ruta,
                numero,
                "tablas",
                f"La fila tiene {obtenidas} celdas y el encabezado {esperadas}",
                "error",
            )


def comprobar_caracteres(ruta: str, texto: str, limpio: str, res: Resultado) -> None:
    for numero, linea in enumerate(texto.split("\n"), start=1):
        for caracter in linea:
            codigo = ord(caracter)
            for desde, hasta, nombre in RANGOS_PROHIBIDOS:
                if desde <= codigo <= hasta:
                    res.add(
                        ruta,
                        numero,
                        "caracteres",
                        f"Carácter {nombre} inesperado: «{caracter}» (U+{codigo:04X})",
                        "error",
                    )
                    break

    for numero, linea in enumerate(limpio.split("\n"), start=1):
        for coincidencia in SOSPECHOSAS.finditer(CITAS.sub(" ", linea)):
            res.add(
                ruta,
                numero,
                "idioma",
                f"Palabra en inglés sospechosa en la prosa: «{coincidencia.group(0)}»",
                "aviso",
            )


def comprobar_indices(rutas: list[str], textos: dict[str, str], res: Resultado) -> None:
    """Aviso si un documento no está enlazado desde ningún índice.

    `textos` ya viene sin bloques de código: los enlaces se cuentan una vez.
    """
    indices = {
        "inicio",
        "indice de adrs",
        "12.02 registro de cambios",
        "12.03 bitacora de sesiones con ia",
    }
    referenciados: set[str] = set()
    for limpio in textos.values():
        for _, destino in destinos_wikilink(limpio):
            referenciados.add(normalizar(destino))

    for ruta in rutas:
        nombre = os.path.splitext(os.path.basename(ruta))[0]
        clave = normalizar(nombre)
        if clave in indices:
            continue
        if clave not in referenciados:
            res.add(ruta, 1, "indices", "No está referenciado desde ningún índice", "aviso")


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Valida la bóveda de documentación del proyecto CAI."
    )
    parser.add_argument("--vault", default=VAULT_POR_DEFECTO, help="Carpeta de la bóveda")
    parser.add_argument("--quiet", action="store_true", help="Muestra solo errores")
    parser.add_argument("--json", action="store_true", help="Salida en JSON")
    args = parser.parse_args(argv)

    if not os.path.isdir(args.vault):
        print(f"ERROR: no existe la carpeta de la bóveda: {args.vault}", file=sys.stderr)
        return 2

    rutas = list(recorrer_markdown(args.vault))
    if not rutas:
        print(f"ERROR: no se encontraron documentos .md en {args.vault}", file=sys.stderr)
        return 2

    # Índice de nombres de documento → ruta, con alias sin prefijo numérico.
    indice: dict[str, str] = {}
    for ruta in rutas:
        nombre = os.path.splitext(os.path.basename(ruta))[0]
        indice.setdefault(normalizar(nombre), ruta)
        indice.setdefault(normalizar(sin_prefijo(nombre)), ruta)

    res = Resultado(documentos=len(rutas))
    limpios: dict[str, str] = {}

    for ruta in rutas:
        with open(ruta, encoding="utf-8", errors="replace") as manejador:
            texto = manejador.read()
        limpio = quitar_bloques_de_codigo(texto)
        limpios[ruta] = limpio
        comprobar_frontmatter(ruta, texto, res)
        comprobar_wikilinks(ruta, limpio, indice, res)
        comprobar_tablas(ruta, limpio, res)
        comprobar_caracteres(ruta, texto, limpio, res)

    comprobar_indices(rutas, limpios, res)

    if args.json:
        print(
            json.dumps(
                {
                    "documentos": res.documentos,
                    "wikilinks": res.wikilinks,
                    "errores": len(res.errores),
                    "avisos": len(res.avisos),
                    "problemas": [p.__dict__ for p in res.problemas],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        _imprimir_informe(res, args.quiet)

    return 1 if res.errores else 0


def _imprimir_informe(res: Resultado, quiet: bool) -> None:
    print("=" * 78)
    print(" VALIDACIÓN DE LA BÓVEDA — PROYECTO CAI")
    print("=" * 78)
    print(f" Documentos analizados : {res.documentos}")
    print(f" Wikilinks verificados : {res.wikilinks}")
    print(f" Errores               : {len(res.errores)}")
    print(f" Avisos                : {len(res.avisos)}")
    print("=" * 78)

    if res.errores:
        print("\nERRORES (impiden publicar)")
        print("-" * 78)
        for problema in res.errores:
            print(f"  {problema.archivo}:{problema.linea}")
            print(f"    [{problema.regla}] {problema.mensaje}")

    if not quiet and res.avisos:
        print("\nAVISOS (revisar, no bloquean)")
        print("-" * 78)
        for problema in res.avisos:
            print(f"  {problema.archivo}:{problema.linea}")
            print(f"    [{problema.regla}] {problema.mensaje}")

    print()
    if res.errores:
        print(f"RESULTADO: FALLÓ — {len(res.errores)} error(es). Corregí y volvé a ejecutar.")
    elif res.avisos:
        print(f"RESULTADO: OK con {len(res.avisos)} aviso(s).")
    else:
        print("RESULTADO: OK — la bóveda cumple las convenciones.")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
