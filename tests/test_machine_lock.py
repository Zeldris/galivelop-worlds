"""RAG-3: candado de máquina ``grun.lock/1`` (stdlib)."""

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from gworld import machine_lock
from gworld.machine_lock import LockBusyError, LockUnavailableError, MachineLockError

ROOT = Path(__file__).resolve().parent.parent
CHILD = """
import sys, time
from gworld import machine_lock
with machine_lock.hold(5, app="hijo", entry=7):
    print("held", flush=True)
    sys.stdin.readline()
"""


class StateEnvMixin:
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.state = Path(d.name) / "estado"
        env = {k: v for k, v in os.environ.items() if k not in ("GALIVELOP_STATE_HOME", "XDG_STATE_HOME", "FLATPAK_ID")}
        env["GALIVELOP_STATE_HOME"] = str(self.state)
        p = mock.patch.dict(os.environ, env, clear=True)
        p.start()
        self.addCleanup(p.stop)


class PathTest(StateEnvMixin, unittest.TestCase):
    def test_orden_de_rutas(self):
        self.assertEqual(machine_lock.lock_path(), self.state / "gpu.lock")
        with mock.patch.dict(os.environ, {"GALIVELOP_STATE_HOME": "relativa", "XDG_STATE_HOME": "/x/st"}):
            self.assertEqual(machine_lock.lock_path(), Path("/x/st/galivelop/gpu.lock"))
        with mock.patch.dict(os.environ, {"GALIVELOP_STATE_HOME": "", "XDG_STATE_HOME": "rel", "HOME": "/h"}):
            self.assertEqual(machine_lock.lock_path(), Path("/h/.local/state/galivelop/gpu.lock"))

    def test_flatpak_ignora_el_sandbox(self):
        env = {"GALIVELOP_STATE_HOME": "", "XDG_STATE_HOME": "/h/.var/app/org.x/.local/state", "FLATPAK_ID": "org.x",
               "HOME": "/h"}
        with mock.patch.dict(os.environ, env):
            self.assertEqual(machine_lock.lock_path(), Path("/h/.local/state/galivelop/gpu.lock"))
        env.pop("FLATPAK_ID")
        with mock.patch.dict(os.environ, env):
            self.assertEqual(machine_lock.lock_path(), Path("/h/.var/app/org.x/.local/state/galivelop/gpu.lock"))


class HoldTest(StateEnvMixin, unittest.TestCase):
    def test_crea_carpeta_escribe_registro_y_trunca_sin_borrar(self):
        path = machine_lock.lock_path()
        with machine_lock.hold(1, entry="e1"):
            self.assertTrue(machine_lock.busy())
            raw = path.read_text()
            self.assertNotIn("\n", raw)
            rec = json.loads(raw)
            self.assertEqual((rec["schema"], rec["app"], rec["pid"], rec["entry"]), ("grun.lock/1", "gworld", os.getpid(), "e1"))
            self.assertRegex(rec["since"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
            self.assertEqual(machine_lock.holder()["pid"], os.getpid())
            inode = path.stat().st_ino
        self.assertTrue(path.exists())
        self.assertEqual(path.read_text(), "")
        self.assertFalse(machine_lock.busy())
        self.assertIsNone(machine_lock.holder())
        with machine_lock.hold(1):
            self.assertEqual(path.stat().st_ino, inode)

    def test_hijo_excluye_y_vence_con_lockbusy(self):
        child = subprocess.Popen([sys.executable, "-c", CHILD], cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 text=True)
        try:
            self.assertEqual(child.stdout.readline().strip(), "held")
            self.assertEqual(machine_lock.holder()["app"], "hijo")
            t0 = time.monotonic()
            with self.assertRaises(LockBusyError) as cm:
                with machine_lock.hold(0.3):
                    self.fail("no debía tomarlo")
            self.assertIn("sigue ocupado tras 0.3 s", str(cm.exception))
            self.assertGreaterEqual(time.monotonic() - t0, 0.3)
            child.stdin.write("\n")
            child.stdin.flush()
            child.wait(timeout=10)
            with machine_lock.hold(2):  # libre al morir el hijo
                pass
        finally:
            child.kill()
            child.wait()
            child.stdin.close()
            child.stdout.close()

    def test_no_se_puede_abrir_no_es_libre(self):
        self.state.parent.mkdir(parents=True, exist_ok=True)
        self.state.write_text("soy un archivo, no una carpeta")
        with self.assertRaises(LockUnavailableError) as cm:
            with machine_lock.hold(0.1):
                pass
        self.assertIn("no se puede abrir el candado", str(cm.exception))
        self.assertIsInstance(cm.exception, MachineLockError)

    def test_sin_fcntl_error_claro(self):
        with mock.patch.object(machine_lock, "fcntl", None):
            with self.assertRaises(MachineLockError) as cm:
                with machine_lock.hold(0.1):
                    pass
        self.assertIn("necesita fcntl", str(cm.exception))

    def test_importar_no_trae_fuera_de_stdlib(self):
        code = ("import sys, gworld.rag, gworld.sqlite_store, gworld.ollama, gworld.machine_lock;"
                "bad = [m for m in sys.modules if m.split('.')[0] in ('grun','requests','numpy','psycopg','psycopg2','pgvector')];"
                "assert not bad, bad")
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
