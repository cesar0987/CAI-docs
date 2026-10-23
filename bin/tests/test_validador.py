"""Pruebas del validador de la bóveda (T4 de 05.08).

Cubren los casos T-01 a T-10 de la matriz de
`sistema cai/05 - Proceso de Desarrollo/05.09 Herramientas de Gobernanza.md` §9.

    python3 -m unittest discover -s bin/tests -v
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parents[2]
SCRIPT = RAIZ / "bin" / "validate-vault.py"


def cargar_modulo() -> Any:
    spec = importlib.util.spec_from_file_location("validate_vault", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar {SCRIPT}")
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def documento(titulo: str, cuerpo: str = "", **campos: str) -> str:
    """Arma un documento mínimo con el frontmatter obligatorio."""
    valores = {
        "type": "proceso",
        "status": "vigente",
        "tags": "[cai]",
        "owner": "Responsable técnico",
        "updated": "2026-10-22",
    }
    valores.update(campos)
    lineas = ["---", f"title: {titulo}"]
    lineas += [f"{clave}: {valor}" for clave, valor in valores.items()]
    lineas += ["---", "", cuerpo]
    return "\n".join(lineas)


class Validador(unittest.TestCase):
    modulo: Any

    @classmethod
    def setUpClass(cls) -> None:
        cls.modulo = cargar_modulo()

    def crear(self, carpeta: str, nombre: str, contenido: str) -> Path:
        ruta = Path(carpeta) / nombre
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(contenido, encoding="utf-8")
        return ruta

    def ejecutar(self, *argumentos: str) -> tuple[int, str, str]:
        salida, error = io.StringIO(), io.StringIO()
        with redirect_stdout(salida), redirect_stderr(error):
            codigo = self.modulo.main(list(argumentos))
        return codigo, salida.getvalue(), error.getvalue()

    def validar(self, contenido: str, nombre: str = "Inicio.md") -> dict[str, Any]:
        with tempfile.TemporaryDirectory() as carpeta:
            self.crear(carpeta, nombre, contenido)
            codigo, salida, _ = self.ejecutar("--vault", carpeta, "--json")
        datos: dict[str, Any] = json.loads(salida)
        datos["codigo"] = codigo
        return datos

    def mensajes(self, datos: dict[str, Any], regla: str | None = None) -> list[str]:
        problemas = datos["problemas"]
        if regla is not None:
            problemas = [p for p in problemas if p["regla"] == regla]
        return [p["mensaje"] for p in problemas]

    # T-01
    def test_boveda_sana(self) -> None:
        datos = self.validar(documento("Inicio", "# Inicio\n\nTexto en español.\n"))
        self.assertEqual(datos["codigo"], 0)
        self.assertEqual(datos["errores"], 0)
        self.assertEqual(datos["avisos"], 0)
        self.assertEqual(datos["documentos"], 1)

    # T-02
    def test_documento_sin_frontmatter(self) -> None:
        datos = self.validar("# Sin frontmatter\n")
        self.assertEqual(datos["codigo"], 1)
        errores = [p for p in datos["problemas"] if p["severidad"] == "error"]
        self.assertEqual(len(errores), 1)
        self.assertEqual(errores[0]["linea"], 1)
        self.assertIn("frontmatter", errores[0]["mensaje"])

    # T-03
    def test_title_distinto_del_nombre(self) -> None:
        datos = self.validar(documento("Otro título"), nombre="Documento.md")
        self.assertIn("no coincide con el nombre del archivo", " ".join(self.mensajes(datos)))

    # T-04
    def test_status_fuera_del_catalogo(self) -> None:
        datos = self.validar(documento("Inicio", status="activo"))
        self.assertIn("`status` inválido", " ".join(self.mensajes(datos)))

    def test_adr_usa_su_propio_catalogo(self) -> None:
        datos = self.validar(
            documento("ADR-0001 Prueba", status="aceptado"),
            nombre="ADR-0001 Prueba.md",
        )
        self.assertNotIn("`status` inválido", " ".join(self.mensajes(datos)))

    # T-05
    def test_updated_mal_formado(self) -> None:
        datos = self.validar(documento("Inicio", updated="22-10-2026"))
        self.assertIn("formato YYYY-MM-DD", " ".join(self.mensajes(datos)))

    # T-06
    def test_enlaces_alias_ancla_y_codigo(self) -> None:
        cuerpo = (
            "[[Inicio]] [[Inicio|alias]] [[Inicio#Sección]]\n\n"
            "`[[No se cuenta]]`\n\n"
            "```\n[[Tampoco se cuenta]]\n```\n\n"
            "[[Fantasma]]\n"
        )
        datos = self.validar(documento("Inicio", cuerpo))
        rotos = [m for m in self.mensajes(datos, "wikilinks") if "Enlace roto" in m]
        self.assertEqual(rotos, ["Enlace roto: [[Fantasma]]"])
        self.assertEqual(datos["wikilinks"], 4)

    # T-07
    def test_tabla_sin_separador(self) -> None:
        datos = self.validar(documento("Inicio", "| a | b |\n| 1 | 2 |\n"))
        self.assertIn("Falta la fila separadora", " ".join(self.mensajes(datos, "tablas")))

    def test_fila_con_celdas_distintas(self) -> None:
        datos = self.validar(
            documento("Inicio", "| a | b |\n|---|---|\n| 1 | 2 | 3 |\n")
        )
        self.assertIn("3 celdas y el encabezado 2", " ".join(self.mensajes(datos, "tablas")))

    def test_pipe_escapado_no_separa_celdas(self) -> None:
        datos = self.validar(
            documento("Inicio", "| a | b |\n|---|---|\n| x \\| y | z |\n")
        )
        self.assertEqual(self.mensajes(datos, "tablas"), [])

    # T-08
    def test_caracter_cjk(self) -> None:
        datos = self.validar(documento("Inicio", "Texto con carácter 漢 inesperado.\n"))
        self.assertIn("CJK", " ".join(self.mensajes(datos, "caracteres")))

    def test_palabra_inglesa_fuera_y_dentro_de_comillas(self) -> None:
        fuera = self.validar(documento("Inicio", "Esta frase tiene the palabra.\n"))
        self.assertIn("the", " ".join(self.mensajes(fuera, "idioma")))

        dentro = self.validar(documento("Inicio", "El botón «the» no se escanea.\n"))
        self.assertEqual(self.mensajes(dentro, "idioma"), [])

    # T-09
    def test_salida_json(self) -> None:
        datos = self.validar(documento("Inicio", "[[Fantasma]]\n"))
        self.assertEqual(
            set(datos) - {"codigo"},
            {"documentos", "wikilinks", "errores", "avisos", "problemas"},
        )
        self.assertEqual(datos["documentos"], 1)
        self.assertEqual(datos["wikilinks"], 1)
        self.assertEqual(datos["errores"], 1)
        self.assertEqual(datos["avisos"], 0)
        self.assertEqual(
            set(datos["problemas"][0]),
            {"archivo", "linea", "regla", "mensaje", "severidad"},
        )

    # T-10
    def test_vault_inexistente(self) -> None:
        codigo, _, error = self.ejecutar("--vault", "/ruta/que/no/existe")
        self.assertEqual(codigo, 2)
        self.assertIn("no existe la carpeta", error)


if __name__ == "__main__":
    unittest.main()
