"""Pruebas de la política de trazabilidad.

Cubren los casos T-19, T-20 y T-21 de la matriz de
`sistema cai/05 - Proceso de Desarrollo/05.09 Herramientas de Gobernanza.md` §9.

Se ejecutan con la biblioteca estándar, sin dependencias:

    python3 -m unittest discover -s bin/tests -v
"""

from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any
from unittest import mock

RAIZ = Path(__file__).resolve().parents[2]
SCRIPT = RAIZ / "bin" / "cai-log.py"

REGISTRO_FICTICIO = """# Registro de prueba

## REG-2026-001 · Alta de la funcionalidad

| Campo | Valor |
|---|---|
| **Motivo** | Alta inicial del módulo de prueba |
| **Archivos** | `nota.txt` |

## REG-2026-002 · Retiro del módulo viejo

| Campo | Valor |
|---|---|
| **Motivo** | Se retira el módulo viejo y se marca como deprecated |
| **Archivos** | `viejo.txt` |
"""


def cargar_modulo():
    """Carga `bin/cai-log.py` como módulo sin ejecutar su `main`."""
    spec = importlib.util.spec_from_file_location("cai_log", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(modulo)
    return modulo


class VerificarMensaje(unittest.TestCase):
    modulo: Any

    @classmethod
    def setUpClass(cls):
        cls.modulo = cargar_modulo()

    def problemas(self, mensaje: str, eliminados: list[str] | None = None) -> list[str]:
        return self.modulo.verificar_mensaje(mensaje, REGISTRO_FICTICIO, eliminados or [])

    def test_mensaje_sin_registro(self):
        self.assertTrue(self.problemas("fix: algo sin trazabilidad"))

    def test_mensaje_con_registro_existente(self):
        self.assertEqual(self.problemas("docs: alta (REG-2026-001)"), [])

    def test_registro_inexistente(self):
        problemas = self.problemas("docs: algo (REG-2026-999)")
        self.assertEqual(len(problemas), 1)
        self.assertIn("REG-2026-999", problemas[0])

    def test_comentario_no_cuenta_como_cita(self):
        self.assertTrue(self.problemas("# REG-2026-001\nfix: sin registro"))
        self.assertEqual(self.modulo.citas("# REG-2026-001\nfix: sin registro"), [])

    def test_eliminacion_justificada(self):
        self.assertEqual(self.problemas("docs: retiro (REG-2026-002)", ["viejo.txt"]), [])

    def test_eliminacion_no_mencionada(self):
        problemas = self.problemas("docs: retiro (REG-2026-002)", ["otro.txt"])
        self.assertIn("otro.txt", problemas[0])

    def test_eliminacion_sin_justificacion(self):
        problemas = self.problemas("docs: alta (REG-2026-001)", ["nota.txt"])
        self.assertIn("no justifica", problemas[0])

    def test_merge_no_exige_registro(self):
        self.assertTrue(self.modulo.es_merge("Merge branch 'main' into feature"))
        self.assertFalse(self.modulo.es_merge("docs: algo (REG-2026-001)"))


class ComandoVerificar(unittest.TestCase):
    modulo: Any

    @classmethod
    def setUpClass(cls):
        cls.modulo = cargar_modulo()

    def ejecutar(self, mensaje: str, extra: list[str] | None = None):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta_mensaje = Path(carpeta) / "mensaje"
            ruta_mensaje.write_text(mensaje, encoding="utf-8")
            ruta_registro = Path(carpeta) / "12.02.md"
            ruta_registro.write_text(REGISTRO_FICTICIO, encoding="utf-8")
            salida, error = io.StringIO(), io.StringIO()
            with (
                mock.patch.object(self.modulo, "REGISTRO", str(ruta_registro)),
                mock.patch.object(self.modulo, "archivos_eliminados", return_value=[]),
                redirect_stdout(salida),
                redirect_stderr(error),
            ):
                codigo = self.modulo.main(
                    ["verificar", "--mensaje", str(ruta_mensaje), *(extra or [])]
                )
            return codigo, salida.getvalue(), error.getvalue()

    def test_codigo_cero_con_registro_valido(self):
        codigo, salida, _ = self.ejecutar("docs: alta (REG-2026-001)")
        self.assertEqual(codigo, 0)
        self.assertIn("REG-2026-001", salida)

    def test_codigo_uno_sin_registro(self):
        codigo, _, error = self.ejecutar("docs: sin trazabilidad")
        self.assertEqual(codigo, 1)
        self.assertIn("REG-AAAA-NNN", error)

    def test_codigo_uno_con_registro_inexistente(self):
        codigo, _, error = self.ejecutar("docs: algo (REG-2026-999)")
        self.assertEqual(codigo, 1)
        self.assertIn("REG-2026-999", error)

    def test_codigo_dos_si_falta_el_archivo(self):
        with redirect_stderr(io.StringIO()):
            codigo = self.modulo.main(["verificar", "--mensaje", "/no/existe/mensaje"])
        self.assertEqual(codigo, 2)

    def test_salida_json(self):
        codigo, salida, _ = self.ejecutar("docs: alta (REG-2026-001)", ["--json"])
        self.assertEqual(codigo, 0)
        datos = json.loads(salida)
        self.assertTrue(datos["ok"])
        self.assertEqual(datos["citados"], ["REG-2026-001"])


class InsercionSegura(unittest.TestCase):
    """T-21: una entrada nueva no puede tocar las anteriores."""

    modulo: Any

    @classmethod
    def setUpClass(cls):
        cls.modulo = cargar_modulo()

    TEXTO = (
        "---\n\n"
        "<!-- SES-ENTRIES:START -->\n"
        "---\n\n"
        "## SES-2026-001 · Uno\n\n"
        "| **Objetivo** | primera |\n\n"
        "---\n\n"
        "## SES-2026-002 · Dos\n\n"
        "| **Objetivo** | segunda |\n\n"
        "<!-- SES-ENTRIES:END -->\n"
    )

    def test_agrega_sin_modificar_lo_anterior(self):
        bloque = "\n---\n\n## SES-2026-003 · Tres\n\n| **Objetivo** | tercera |\n"
        nuevo = self.modulo.insertar_entrada(self.TEXTO, "SES-ENTRIES", bloque)
        self.assertIn("SES-2026-001", nuevo)
        self.assertIn("SES-2026-002", nuevo)
        self.assertIn("SES-2026-003", nuevo)
        self.assertEqual(nuevo.replace(bloque, "", 1), self.TEXTO)

    def test_falla_si_falta_el_marcador(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.modulo.insertar_entrada("sin marcadores", "SES-ENTRIES", "x")


if __name__ == "__main__":
    unittest.main()
