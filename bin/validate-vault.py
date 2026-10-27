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
from typing import Iterable, Literal

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

VAULT_POR_DEFECTO = "sistema cai"
CARPETAS_IGNORADAS = {".obsidian", ".git", ".cai", "node_modules", "vendor", ".trash"}

CAMPOS_OBLIGATORIOS = ["title", "type", "status", "tags", "owner", "updated"]
ESTADOS_VALIDOS = {"borrador", "vigente", "deprecated", "superseded"}
# Los ADR usan sus propios estados (ver 00.01 §4 y Plantilla - ADR).
ESTADOS_ADR = {"borrador", "aceptado", "revisado", "reemplazado", "descartado"}

# Valores que no constituyen una atribución (AGENTS.md §3): la sesión no se registra así.
CAMPOS_VACIOS_SESION = {
    "",
    "—",
    "-",
    "no declarado",
    "no declarada",
    "pendiente",
    "*(completar)*",
    "(completar)",
}

# Severidades y posición de los avisos que no dependen de una línea concreta.
Severidad = Literal["error", "aviso"]
ERROR: Severidad = "error"
AVISO: Severidad = "aviso"
PRIMERA_LINEA = 1

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
    severidad: Severidad = ERROR


@dataclass
class Resultado:
    documentos: int = 0
    wikilinks: int = 0
    problemas: list[Problema] = field(default_factory=list)

    def add(self, *args, **kwargs) -> None:
        self.problemas.append(Problema(*args, **kwargs))

    @property
    def errores(self) -> list[Problema]:
        return [p for p in self.problemas if p.severidad == ERROR]

    @property
    def avisos(self) -> list[Problema]:
        return [p for p in self.problemas if p.severidad == AVISO]


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


def leer_frontmatter(texto: str) -> dict[str, str]:
    """Devuelve los campos del frontmatter; vacío si no hay bloque válido."""
    if not texto.startswith("---"):
        return {}
    fin = texto.find("\n---", 3)
    if fin == -1:
        return {}
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
    return campos


# ---------------------------------------------------------------------------
# Comprobaciones
# ---------------------------------------------------------------------------


def comprobar_frontmatter(ruta: str, texto: str, res: Resultado) -> None:
    campos = leer_frontmatter(texto)
    nombre = os.path.splitext(os.path.basename(ruta))[0]

    if not campos:
        res.add(ruta, PRIMERA_LINEA, "frontmatter", "Falta el bloque de frontmatter (--- … ---)", ERROR)
        return

    for campo in CAMPOS_OBLIGATORIOS:
        if campo not in campos or not campos[campo]:
            res.add(ruta, PRIMERA_LINEA, "frontmatter", f"Falta el campo obligatorio `{campo}`", ERROR)

    titulo = campos.get("title", "").strip('"').strip("'")
    esperado = sin_prefijo(nombre)
    if titulo and normalizar(titulo) != normalizar(esperado):
        res.add(
            ruta,
            PRIMERA_LINEA,
            "frontmatter",
            f"`title` («{titulo}») no coincide con el nombre del archivo sin prefijo («{esperado}»)",
            ERROR,
        )

    estado = campos.get("status", "").strip().strip('"').strip("'")
    validos = ESTADOS_ADR if nombre.startswith("ADR-") else ESTADOS_VALIDOS
    if estado and estado not in validos:
        res.add(
            ruta,
            PRIMERA_LINEA,
            "frontmatter",
            f"`status` inválido («{estado}»). Válidos: {', '.join(sorted(validos))}",
            ERROR,
        )

    actualizado = campos.get("updated", "").strip()
    if actualizado and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", actualizado):
        res.add(
            ruta,
            PRIMERA_LINEA,
            "frontmatter",
            f"`updated` debe tener formato YYYY-MM-DD (valor «{actualizado}»)",
            ERROR,
        )


def comprobar_wikilinks(ruta: str, limpio: str, indice: dict[str, str], res: Resultado) -> None:
    for numero, destino in destinos_wikilink(limpio):
        res.wikilinks += 1
        if normalizar(destino) in indice:
            continue
        res.add(ruta, numero, "wikilinks", f"Enlace roto: [[{destino}]]", ERROR)


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
            ERROR,
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
                ERROR,
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
                        ERROR,
                    )
                    break

    for numero, linea in enumerate(limpio.split("\n"), start=1):
        for coincidencia in SOSPECHOSAS.finditer(CITAS.sub(" ", linea)):
            res.add(
                ruta,
                numero,
                "idioma",
                f"Palabra en inglés sospechosa en la prosa: «{coincidencia.group(0)}»",
                AVISO,
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
            res.add(ruta, PRIMERA_LINEA, "indices", "No está referenciado desde ningún índice", AVISO)


def comprobar_bitacora_sesiones(ruta: str, texto: str, res: Resultado) -> None:
    """Exige que cada sesión de la bitácora lleve su marcador de identificación."""
    nombre = os.path.basename(ruta).lower()
    if "bitacora" not in nombre and "12.03" not in nombre:
        return

    _comprobar_marcadores_por_prefijo(ruta, texto, res, "SES", "sesiones")
    comprobar_atribucion_de_sesiones(ruta, texto, res)


def comprobar_atribucion_de_sesiones(ruta: str, texto: str, res: Resultado) -> None:
    """Cada sesión del índice tiene entrada, y cada entrada tiene proveedor y modelo.

    Sin el identificador exacto la atribución se pierde para siempre (AGENTS.md §3), y una
    sesión que solo existe como fila de tabla no es auditable. Por eso ambas cosas se
    verifican aquí y no a ojo.
    """
    linea_de = lambda marca: next(
        (i for i, l in enumerate(texto.splitlines()) if l.strip() == marca), None
    )
    inicio_indice = linea_de("<!-- SES-INDEX:START -->")
    inicio_entradas = linea_de("<!-- SES-ENTRIES:START -->")
    fin_entradas = linea_de("<!-- SES-ENTRIES:END -->")
    if inicio_indice is None or inicio_entradas is None or fin_entradas is None:
        res.add(
            ruta,
            PRIMERA_LINEA,
            "atribución",
            "Faltan los anclajes `SES-INDEX:START`, `SES-ENTRIES:START` o `SES-ENTRIES:END`",
            ERROR,
        )
        return

    lineas = texto.splitlines()
    indice = re.findall(
        r"^\|\s*(SES-\d{4}-\d{3})\s*\|", "\n".join(lineas[inicio_indice:inicio_entradas]), re.M
    )
    cuerpo = "\n".join(lineas[inicio_entradas:fin_entradas])
    entradas = re.findall(r"^##\s+(SES-\d{4}-\d{3})\b", cuerpo, re.M)

    faltantes = [sid for sid in indice if sid not in entradas]
    if faltantes:
        res.add(
            ruta,
            PRIMERA_LINEA,
            "atribución",
            "Sesiones en el índice sin entrada en el cuerpo: " + ", ".join(faltantes),
            ERROR,
        )
    huerfanas = [sid for sid in entradas if sid not in indice]
    if huerfanas:
        res.add(
            ruta,
            PRIMERA_LINEA,
            "atribución",
            "Entradas de sesión sin fila en el índice: " + ", ".join(huerfanas),
            ERROR,
        )

    posiciones = [
        (numero, coincidencia.group(1))
        for numero, linea in enumerate(lineas, start=1)
        if (coincidencia := re.match(r"^##\s+(SES-\d{4}-\d{3})\b", linea))
    ]
    cortes = [numero for numero, _ in posiciones] + [len(lineas) + 1]
    for (numero, sid), fin in zip(posiciones, cortes[1:]):
        bloque = "\n".join(lineas[numero - 1 : fin])
        for campo in ("Proveedor", "Modelo"):
            coincidencia = re.search(rf"^\| \*\*{campo}\*\* \| (.*?) \|", bloque, re.M)
            valor = (coincidencia.group(1).strip().strip("`") if coincidencia else "")
            if not coincidencia:
                res.add(
                    ruta,
                    numero,
                    "atribución",
                    f"La sesión {sid} no tiene el campo **{campo}**",
                    ERROR,
                )
            elif valor in CAMPOS_VACIOS_SESION:
                res.add(
                    ruta,
                    numero,
                    "atribución",
                    f"La sesión {sid} tiene **{campo}** como `{valor or '—'}`: "
                    "el modelo se registra con `proveedor/modelo#variante` o se pregunta",
                    ERROR,
                )


def comprobar_registro_cambios(ruta: str, texto: str, res: Resultado) -> None:
    """Exige que cada entrada del registro lleve su marcador de identificación."""
    nombre = os.path.basename(ruta).lower()
    if "registro de cambios" not in nombre and "12.02" not in nombre:
        return

    _comprobar_marcadores_por_prefijo(ruta, texto, res, "REG", "identificadores")


def _comprobar_marcadores_por_prefijo(
    ruta: str, texto: str, res: Resultado, prefijo: str, regla: str
) -> None:
    inicio = f"<!-- {prefijo}-ENTRIES:START -->"
    fin = f"<!-- {prefijo}-ENTRIES:END -->"
    if inicio not in texto or fin not in texto:
        res.add(
            ruta,
            PRIMERA_LINEA,
            regla,
            f"Falta el rango de entradas entre `{inicio}` y `{fin}`",
            ERROR,
        )
        return

    lineas = texto.splitlines()
    for numero, linea in enumerate(lineas, start=1):
        coincidencia = re.match(rf"^##\s*({prefijo}-\d{{4}}-\d{{3}})\b", linea)
        if not coincidencia:
            continue
        entrada_id = coincidencia.group(1)
        marcador = f"<!-- {entrada_id} -->"
        ventana = "\n".join(lineas[max(0, numero - 25): numero])
        if marcador not in ventana:
            res.add(
                ruta,
                numero,
                regla,
                f"La entrada {entrada_id} no tiene su marcador `{marcador}` justo antes del encabezado",
                ERROR,
            )


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
        comprobar_bitacora_sesiones(ruta, texto, res)
        comprobar_registro_cambios(ruta, texto, res)

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
