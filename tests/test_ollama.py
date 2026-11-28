"""RAG-3: ``OllamaEmbedder`` contra un servidor HTTP falso local, con el candado en un estado temporal."""

import fcntl
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

from gworld import machine_lock
from gworld.ollama import OllamaEmbedder
from gworld.rag import EmbedError, IndexMeta

DIGEST = "sha256:abc123"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, raw=False):
        data = body if raw else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self.server.calls.append(("GET", self.path, None))
        self._send(200, {"models": self.server.models})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        # ¿tiene alguien el candado mientras llega la llamada? (otra descripción de archivo en este proceso)
        fd = os.open(str(machine_lock.lock_path()), os.O_RDWR)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
                locked = False
            except BlockingIOError:
                locked = True
        finally:
            os.close(fd)
        self.server.calls.append(("POST", self.path, body, locked))
        mode = self.server.mode
        if mode == "http500":
            self._send(500, {"error": "modelo roto"})
        elif mode == "badjson":
            self._send(200, b"no es json", raw=True)
        elif mode == "noembeddings":
            self._send(200, {"otra": 1})
        else:
            self._send(200, {"embeddings": [[float(len(t)), 1.0] for t in body["input"]]})


class OllamaTest(unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        p = mock.patch.dict(os.environ, {"GALIVELOP_STATE_HOME": str(Path(d.name) / "estado")})
        p.start()
        self.addCleanup(p.stop)
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.srv.calls, self.srv.mode = [], "ok"
        self.srv.models = [{"name": "otro:latest", "digest": "sha256:zzz"}, {"name": "bge-m3:latest", "digest": DIGEST}]
        t = threading.Thread(target=self.srv.serve_forever, daemon=True)
        t.start()
        self.addCleanup(t.join)
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)
        self.url = f"http://127.0.0.1:{self.srv.server_port}"
        self.emb = OllamaEmbedder(base_url=self.url, timeout=5, lock_timeout=1)

    def test_defecto_y_variable_de_entorno(self):
        with mock.patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://h:1/"}):
            e = OllamaEmbedder()
        self.assertEqual((e.model, e.base_url), ("bge-m3", "http://h:1"))
        with mock.patch.dict(os.environ):
            os.environ.pop("OLLAMA_BASE_URL", None)
            self.assertEqual(OllamaEmbedder().base_url, "http://localhost:11434")

    def test_version_es_el_digest_y_meta(self):
        self.assertEqual(self.emb.version, DIGEST)
        self.assertEqual(self.emb.meta, IndexMeta("bge-m3", DIGEST))

    def test_modelo_ausente_dice_ollama_pull(self):
        with self.assertRaises(EmbedError) as cm:
            _ = OllamaEmbedder("nomic-embed-text", self.url).version
        self.assertIn("ollama pull nomic-embed-text", str(cm.exception))

    def test_embed_da_vectores_y_toma_el_candado(self):
        out = self.emb.embed_checked(["ab", "cde"])
        self.assertEqual(out, [(2.0, 1.0), (3.0, 1.0)])
        (call,) = [c for c in self.srv.calls if c[0] == "POST"]
        self.assertEqual(call[1:3], ("/api/embed", {"model": "bge-m3", "input": ["ab", "cde"]}))
        self.assertTrue(call[3], "la llamada a /api/embed debía hacerse con el candado tomado")
        self.assertFalse(machine_lock.busy(), "el candado se suelta al acabar")

    def test_candado_ocupado_vence(self):
        import subprocess, sys
        code = "import sys\nfrom gworld import machine_lock\nwith machine_lock.hold(5):\n print('h',flush=True); sys.stdin.readline()"
        root = Path(__file__).resolve().parent.parent
        child = subprocess.Popen([sys.executable, "-c", code], cwd=root, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        self.addCleanup(child.stdout.close)
        self.addCleanup(child.stdin.close)
        self.addCleanup(child.wait)
        self.addCleanup(child.kill)
        child.stdout.readline()
        with self.assertRaises(machine_lock.LockBusyError):
            OllamaEmbedder(base_url=self.url, lock_timeout=0.2).embed(["x"])
        self.assertEqual([c for c in self.srv.calls if c[0] == "POST"], [])

    def test_errores_dan_embed_error_con_motivo(self):
        for mode, msg in (("http500", "HTTP 500"), ("badjson", "JSON inválido"), ("noembeddings", "sin lista 'embeddings'")):
            with self.subTest(mode=mode):
                self.srv.mode = mode
                with self.assertRaises(EmbedError) as cm:
                    self.emb.embed(["x"])
                self.assertIn(msg, str(cm.exception))
        self.srv.mode = "http500"
        with self.assertRaises(EmbedError) as cm:
            self.emb.embed(["x"])
        self.assertIn("modelo roto", str(cm.exception))

    def test_servidor_caido(self):
        url = self.url
        self.srv.shutdown()
        self.srv.server_close()
        with self.assertRaises(EmbedError) as cm:
            OllamaEmbedder(base_url=url, timeout=2, lock_timeout=1).embed(["x"])
        self.assertIn("no se pudo hablar con Ollama", str(cm.exception))

    def test_sin_textos_no_llama(self):
        self.assertEqual(self.emb.embed([]), [])
        self.assertEqual(self.srv.calls, [])


if __name__ == "__main__":
    unittest.main()
