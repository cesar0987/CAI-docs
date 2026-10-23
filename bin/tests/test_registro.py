"""Pruebas del registro de cambios y de la bitácora (T2 de 05.08).

Cubren los casos T-11, T-18 y T-23 de la matriz de
`sistema cai/05 - Proceso de Desarrollo/05.09 Herramientas de Gobernanza.md` §9:
escritura única y atómica, rechazo sin tocar el archivo y correlativo correcto.

    python3 -m unittest discover -s bin/tests -v
"""

from __future__ import annotations

import importlib.util
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest import mock

RAIZ = Path(__file__).resolve().parents[2]
SCRIPT = RAIZ / "bin" / "cai-log.py"
ANIO = datetime.now().astimezone().year

REGISTRO_FICTICIO = f"""---
title: Registro de Cambios
updated: 2026-10-01
---

# Registro de prueba

<!-- REG-ENTRIES:START -->

## REG-{ANIO}-001 · Uno

| Campo | Valor |
|---|---|
| **Motivo** | primero |

## REG-{ANIO}-002 · Dos

| Campo | Valor |
|---|---|
| **Motivo** | segundo |

<!-- REG-ENTRIES:END -->

## 3. Índice de entradas

<!-- REG-INDEX:START -->

| ID | Fecha | Tipo | Severidad | Resumen | Sesión |
|---|---|---|---|---|---|
| REG-{ANIO}-002 | 2026-10-01 | edición | N1 | segundo | — |
| REG-{ANIO}-001 | 2026-10-01 | edición | N1 | primero | — |
"""


def cargar_modulo():
    """Carga `bin/cai-log.py` como módulo sin ejecutar su `main`."""
    spec = importlib.util.spec_from_file_location("cai_log", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(modulo)
    return modulo


class Correlativo(unittest.TestCase):
    modulo: Any

    @classmethod
    def setUpClass(cls):
        cls.modulo = cargar_modulo()

    def test_cuenta_encabezados_y_filas(self):
        texto = f"## REG-{ANIO}-001 · a\n\n| REG-{ANIO}-007 | 2026-10-01 | edición | N1 | x | — |\n"
        self.assertEqual(self.modulo.siguiente_id(texto, "REG"), f"REG-{ANIO}-008")

    def test_ignora_menciones_en_la_prosa(self):
        texto = f"El ejemplo REG-{ANIO}-099 no consume números.\n"
        self.assertEqual(self.modulo.siguiente_id(texto, "REG"), f"REG-{ANIO}-001")

    def test_sin_entradas_empieza_en_uno(self):
        self.assertEqual(self.modulo.siguiente_id("# vacío\n", "SES"), f"SES-{ANIO}-001")

    def test_id_pedido_duplicado_se_rechaza(self):
        with self.assertRaises(self.modulo.CaiError):
            self.modulo.preparar_id(REGISTRO_FICTICIO, "REG", f"REG-{ANIO}-001")

    def test_id_pedido_nuevo_se_respeta(self):
        pedido = f"REG-{ANIO}-050"
        self.assertEqual(self.modulo.preparar_id(REGISTRO_FICTICIO, "REG", pedido), pedido)

    def test_id_mal_formado_se_rechaza(self):
        for pedido in ("REG-26-1", "SES-2026-001", f"REG-{ANIO}-0012", "REG-2026-1"):
            with self.subTest(pedido=pedido):
                with self.assertRaises(self.modulo.CaiError):
                    self.modulo.preparar_id(REGISTRO_FICTICIO, "REG", pedido)

    def test_id_de_otro_anio_se_rechaza(self):
        with self.assertRaises(self.modulo.CaiError):
            self.modulo.preparar_id(REGISTRO_FICTICIO, "REG", "REG-2020-001")


class Modelo(unittest.TestCase):
    modulo: Any

    @classmethod
    def setUpClass(cls):
        cls.modulo = cargar_modulo()

    def test_variante_dentro_del_modelo(self):
        self.assertEqual(
            self.modulo.resolver_modelo("opencode/big-pickle#default", None),
            ("opencode", "big-pickle", "default"),
        )

    def test_variante_separada(self):
        self.assertEqual(
            self.modulo.resolver_modelo("opencode/big-pickle", "eval"),
            ("opencode", "big-pickle", "eval"),
        )

    def test_variantes_que_discrepan_se_rechazan(self):
        with self.assertRaises(self.modulo.CaiError):
            self.modulo.resolver_modelo("opencode/big-pickle#default", "otra")

    def test_variante_del_entorno(self):
        with mock.patch.dict(os.environ, {"CAI_VARIANTE": "entorno"}, clear=False):
            self.assertEqual(
                self.modulo.resolver_modelo("opencode/big-pickle", None),
                ("opencode", "big-pickle", "entorno"),
            )


class EscrituraAtomica(unittest.TestCase):
    modulo: Any

    @classmethod
    def setUpClass(cls):
        cls.modulo = cargar_modulo()

    def test_si_el_reemplazo_falla_el_original_queda_intacto(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "doc.md"
            ruta.write_text("original\n", encoding="utf-8")
            with mock.patch.object(self.modulo.os, "replace", side_effect=OSError("sin espacio")):
                with self.assertRaises(OSError):
                    self.modulo.escribir(str(ruta), "nuevo\n")
            self.assertEqual(ruta.read_text(encoding="utf-8"), "original\n")
            self.assertEqual(os.listdir(carpeta), ["doc.md"])

    def test_registrar_escribe_una_sola_vez(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "registro.md"
            ruta.write_text(REGISTRO_FICTICIO, encoding="utf-8")
            llamadas: list[str] = []
            real = self.modulo.escribir

            def espia(destino: str, contenido: str) -> None:
                llamadas.append(destino)
                real(destino, contenido)

            with mock.patch.object(self.modulo, "escribir", side_effect=espia):
                escrito = self.modulo._registrar(
                    str(ruta),
                    REGISTRO_FICTICIO,
                    "REG",
                    "\n## REG-NUEVO · prueba\n",
                    "| REG-NUEVO | 2026-10-22 | edición | N2 | prueba | — |\n",
                    False,
                )

            self.assertTrue(escrito)
            self.assertEqual(len(llamadas), 1)
            resultado = ruta.read_text(encoding="utf-8")
            self.assertIn(f"## REG-{ANIO}-001 · Uno", resultado)
            self.assertIn(f"## REG-{ANIO}-002 · Dos", resultado)
            self.assertIn("## REG-NUEVO · prueba", resultado)
            self.assertIn("| REG-NUEVO | 2026-10-22 |", resultado)

    def test_modo_seco_no_escribe(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "registro.md"
            ruta.write_text(REGISTRO_FICTICIO, encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                escrito = self.modulo._registrar(
                    str(ruta),
                    REGISTRO_FICTICIO,
                    "REG",
                    "\n## REG-NUEVO · prueba\n",
                    "| REG-NUEVO | fila |\n",
                    True,
                )
            self.assertFalse(escrito)
            self.assertEqual(ruta.read_text(encoding="utf-8"), REGISTRO_FICTICIO)

    def test_modo_seco_rechaza_si_falta_el_marcador_del_indice(self):
        sin_indice = REGISTRO_FICTICIO.replace("<!-- REG-INDEX:START -->", "")
        with self.assertRaises(self.modulo.CaiError):
            self.modulo._registrar(
                "registro.md",
                sin_indice,
                "REG",
                "\n## REG-NUEVO · prueba\n",
                "| REG-NUEVO | fila |\n",
                True,
            )

    def test_la_fila_nueva_va_arriba_de_las_existentes(self):
        fila = f"| REG-{ANIO}-099 | 2026-10-22 | edición | N1 | nueva | — |"
        nuevo = self.modulo.insertar_en_indice(
            REGISTRO_FICTICIO, "<!-- REG-INDEX:START -->", fila
        )
        self.assertLess(nuevo.index(fila), nuevo.index(f"| REG-{ANIO}-002 |"))
        self.assertLess(nuevo.index("| ID | Fecha |"), nuevo.index(fila))


class ComandoCambio(unittest.TestCase):
    modulo: Any

    @classmethod
    def setUpClass(cls):
        cls.modulo = cargar_modulo()

    def argumentos(self) -> list[str]:
        return [
            "cambio",
            "--tipo",
            "edición",
            "--severidad",
            "N2",
            "--motivo",
            "Se unifica el flujo de registro para escribir una sola vez y sin estados parciales",
            "--archivos",
            "bin/cai-log.py,bin/validate-vault.py",
            "--autor",
            "Prueba",
            "--modelo",
            "opencode/big-pickle#default",
            "--verificacion",
            "unittest -> OK",
        ]

    def test_registra_entrada_y_fila_en_una_sola_escritura(self):
        with tempfile.TemporaryDirectory() as carpeta:
            registro = Path(carpeta) / "12.02 Registro de Cambios.md"
            bitacora = Path(carpeta) / "12.03 Bitácora de Sesiones con IA.md"
            registro.write_text(REGISTRO_FICTICIO, encoding="utf-8")
            bitacora.write_text("# Bitácora\n", encoding="utf-8")

            llamadas: list[str] = []
            real = self.modulo.escribir

            def espia(destino: str, contenido: str) -> None:
                llamadas.append(destino)
                real(destino, contenido)

            with (
                mock.patch.object(self.modulo, "REGISTRO", str(registro)),
                mock.patch.object(self.modulo, "BITACORA", str(bitacora)),
                mock.patch.object(self.modulo, "escribir", side_effect=espia),
                mock.patch.dict(os.environ, {"CAI_SESION": ""}, clear=False),
                redirect_stdout(io.StringIO()) as salida,
            ):
                codigo = self.modulo.main(self.argumentos())

            esperado = f"REG-{ANIO}-003"
            self.assertEqual(codigo, 0)
            self.assertEqual(len(llamadas), 1)
            self.assertIn(esperado, salida.getvalue())

            resultado = registro.read_text(encoding="utf-8")
            self.assertIn(f"## {esperado}", resultado)
            self.assertIn(f"| {esperado} |", resultado)
            self.assertIn(f"updated: {self.modulo.hoy()}", resultado)

    def test_sesion_inexistente_no_escribe_nada(self):
        with tempfile.TemporaryDirectory() as carpeta:
            registro = Path(carpeta) / "12.02 Registro de Cambios.md"
            bitacora = Path(carpeta) / "12.03 Bitácora de Sesiones con IA.md"
            registro.write_text(REGISTRO_FICTICIO, encoding="utf-8")
            bitacora.write_text("# Bitácora\n", encoding="utf-8")

            with (
                mock.patch.object(self.modulo, "REGISTRO", str(registro)),
                mock.patch.object(self.modulo, "BITACORA", str(bitacora)),
                redirect_stderr(io.StringIO()),
            ):
                codigo = self.modulo.main(
                    self.argumentos() + ["--sesion", "SES-2026-999"]
                )

            self.assertEqual(codigo, 1)
            self.assertEqual(registro.read_text(encoding="utf-8"), REGISTRO_FICTICIO)


class ErroresDePolitica(unittest.TestCase):
    modulo: Any

    @classmethod
    def setUpClass(cls):
        cls.modulo = cargar_modulo()

    def test_devuelve_codigo_uno_en_vez_de_terminar(self):
        with redirect_stderr(io.StringIO()) as error:
            codigo = self.modulo.main(
                [
                    "cambio",
                    "--tipo",
                    "edición",
                    "--severidad",
                    "N3",
                    "--motivo",
                    "Un cambio de decisión que no declara su origen ni su trazabilidad completa",
                    "--archivos",
                    "bin/cai-log.py",
                    "--autor",
                    "Prueba",
                    "--modelo",
                    "opencode/big-pickle",
                ]
            )
        self.assertEqual(codigo, 1)
        self.assertIn("ERROR:", error.getvalue())


if __name__ == "__main__":
    unittest.main()
