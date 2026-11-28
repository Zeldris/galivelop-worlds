"""``Embedder`` de Ollama (RAG-3; ADR 0006, invariantes 12 y 13): solo ``urllib``.

``version`` es el digest del modelo en ``GET /api/tags``; ``embed`` toma el candado de máquina
(``gworld.machine_lock``) y hace ``POST /api/embed``. Todo fallo de red, HTTP o JSON es ``EmbedError`` con el motivo.
"""

import json
import os
import urllib.error
import urllib.request
from typing import Sequence

from gworld import machine_lock
from gworld.rag import EmbedError, Embedder, Vector

DEFAULT_MODEL = "bge-m3"
DEFAULT_URL = "http://localhost:11434"


class OllamaEmbedder(Embedder):
    def __init__(self, model: str = DEFAULT_MODEL, base_url: "str | None" = None, *,
                 timeout: float = 120.0, lock_timeout: float = machine_lock.DEFAULT_TIMEOUT_S):
        self._model = model
        self.base_url = (base_url or os.environ.get("OLLAMA_BASE_URL") or DEFAULT_URL).rstrip("/")
        self.timeout = timeout
        self.lock_timeout = lock_timeout

    @property
    def model(self) -> str:
        return self._model

    @property
    def version(self) -> str:
        """Digest del modelo según ``/api/tags``; si no está descargado, ``EmbedError`` con ``ollama pull``."""
        tags = self._request("/api/tags", None)
        models = tags.get("models") if isinstance(tags, dict) else None
        if not isinstance(models, list):
            raise EmbedError("respuesta de /api/tags sin lista 'models'")
        names = {self._model, self._model + ":latest"} if ":" not in self._model else {self._model}
        for m in models:
            if isinstance(m, dict) and (m.get("name") in names or m.get("model") in names):
                digest = m.get("digest")
                if isinstance(digest, str) and digest:
                    return digest
                raise EmbedError(f"Ollama no da el digest del modelo {self._model}")
        raise EmbedError(f"el modelo {self._model} no está en Ollama ({self.base_url}): ollama pull {self._model}")

    def embed(self, texts: Sequence[str]) -> list[Vector]:
        if not texts:
            return []
        with machine_lock.hold(self.lock_timeout):
            data = self._request("/api/embed", {"model": self._model, "input": list(texts)})
        embeddings = data.get("embeddings") if isinstance(data, dict) else None
        if not isinstance(embeddings, list):
            raise EmbedError("respuesta de /api/embed sin lista 'embeddings'")
        return embeddings

    def _request(self, path: str, payload):
        url = self.base_url + path
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="GET" if body is None else "POST",
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read(300).decode("utf-8", "replace").strip()
            finally:
                exc.close()
            raise EmbedError(f"Ollama respondió HTTP {exc.code} en {url}: {detail}") from exc
        except (urllib.error.URLError, OSError) as exc:
            raise EmbedError(f"no se pudo hablar con Ollama en {url}: {getattr(exc, 'reason', exc)}") from exc
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, RecursionError) as exc:
            raise EmbedError(f"Ollama devolvió JSON inválido en {url}: {exc}") from exc
