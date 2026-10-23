"""Pruebas de integración de los hooks de Git (T-19 y T-20 de 05.09 §9).

Crean un repositorio temporal, instalan los hooks reales y commitean de verdad.
También incluyen una guarda estática del plugin (T-22): no debe interpretar
comandos de commit ni escribir en la bóveda.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
HOOKS = RAIZ / "bin" / "hooks"
PLUGIN = RAIZ / ".opencode" / "plugins" / "cai-log.ts"


class HooksDeGit(unittest.TestCase):
    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()
        self.repo = Path(self.carpeta.name)

        (self.repo / "bin").mkdir()
        shutil.copy2(RAIZ / "bin" / "cai-log.py", self.repo / "bin" / "cai-log.py")

        self.git("init", "-q")

        destino = self.repo / ".git" / "hooks"
        for hook in HOOKS.iterdir():
            if hook.is_file():
                shutil.copy2(hook, destino / hook.name)

        self.registro = (
            self.repo
            / "sistema cai"
            / "12 - Registro de Cambios"
            / "12.02 Registro de Cambios.md"
        )
        self.registro.parent.mkdir(parents=True)
        self.escribir_registro(
            "## REG-2026-001 · Alta\n\n"
            "| Campo | Valor |\n|---|---|\n"
            "| **Motivo** | Alta inicial del módulo |\n"
            "| **Archivos** | `otro.txt` |\n"
        )

        (self.repo / "nota.txt").write_text("hola\n", encoding="utf-8")
        self.git("add", "nota.txt")

    def tearDown(self):
        self.carpeta.cleanup()

    def escribir_registro(self, texto: str) -> None:
        self.registro.write_text(f"# Registro de prueba\n\n{texto}", encoding="utf-8")

    def git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        entorno = dict(
            os.environ,
            GIT_AUTHOR_NAME="Prueba",
            GIT_AUTHOR_EMAIL="prueba@example.com",
            GIT_COMMITTER_NAME="Prueba",
            GIT_COMMITTER_EMAIL="prueba@example.com",
            GIT_CONFIG_NOSYSTEM="1",
        )
        return subprocess.run(
            [
                "git",
                "-c",
                "commit.gpgsign=false",
                "-c",
                "user.name=Prueba",
                "-c",
                "user.email=prueba@example.com",
                *args,
            ],
            cwd=self.repo,
            env=entorno,
            capture_output=True,
            text=True,
            check=check,
        )

    def commit(self, mensaje: str) -> subprocess.CompletedProcess[str]:
        return self.git("commit", "-m", mensaje, check=False)

    def test_commit_sin_registro_se_bloquea(self):
        resultado = self.commit("docs: cambio sin trazabilidad")
        self.assertNotEqual(resultado.returncode, 0)
        self.assertIn("REG-AAAA-NNN", resultado.stderr + resultado.stdout)
        self.assertIn("BLOQUEO", resultado.stderr + resultado.stdout)

    def test_commit_con_registro_inexistente_se_bloquea(self):
        resultado = self.commit("docs: cambio (REG-2026-999)")
        self.assertNotEqual(resultado.returncode, 0)
        self.assertIn("REG-2026-999", resultado.stderr + resultado.stdout)

    def test_commit_con_registro_valido_pasa(self):
        resultado = self.commit("docs: alta del módulo (REG-2026-001)")
        self.assertEqual(resultado.returncode, 0, resultado.stderr + resultado.stdout)

    def test_borrado_sin_justificar_se_bloquea(self):
        self.commit("docs: alta del módulo (REG-2026-001)")
        (self.repo / "nota.txt").unlink()
        self.git("add", "-u")

        resultado = self.commit("docs: retiro (REG-2026-001)")
        self.assertNotEqual(resultado.returncode, 0)
        self.assertIn("nota.txt", resultado.stderr + resultado.stdout)

        self.escribir_registro(
            "## REG-2026-001 · Retiro del módulo\n\n"
            "| Campo | Valor |\n|---|---|\n"
            "| **Motivo** | Se retira `nota.txt`, que queda deprecated |\n"
            "| **Archivos** | `nota.txt` |\n"
        )
        resultado = self.commit("docs: retiro (REG-2026-001)")
        self.assertEqual(resultado.returncode, 0, resultado.stderr + resultado.stdout)


class PluginSinPoderSobreLaBoveda(unittest.TestCase):
    """T-22: el plugin no interpreta commits ni escribe en el registro."""

    def test_no_interpreta_commits(self):
        fuente = PLUGIN.read_text(encoding="utf-8")
        self.assertNotIn("git\\s+commit", fuente)
        self.assertNotIn("--no-verify", fuente)

    def test_no_escribe_en_la_boveda(self):
        fuente = PLUGIN.read_text(encoding="utf-8")
        self.assertNotIn("BITACORA", fuente)
        self.assertNotIn("SES-ENTRIES", fuente)


if __name__ == "__main__":
    unittest.main()
