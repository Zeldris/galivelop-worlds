"""RAG-2: interfaces Store y Embedder; un extra que falte falla con la orden que lo instala."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from gworld.chunks import Chunk
from gworld.rag import (EmbedError, Embedder, Hit, IndexMeta, IndexMismatchError, MissingExtraError, RagError, Store,
                        cosine, require_extra)
from tests.store_contract import StoreContract

ROOT = Path(__file__).resolve().parent.parent

M1 = IndexMeta("nomic-embed-text", "1")
M2 = IndexMeta("nomic-embed-text", "2")


def chunk(n: int) -> Chunk:
    return Chunk(id=f"chunk:{n}", fact_id="fact:x", n=n, text=f"t{n}")


class FakeEmbedder(Embedder):
    model, version = "nomic-embed-text", "1"

    def __init__(self, out=None):
        self.out = out

    def embed(self, texts):
        return self.out if self.out is not None else [(1.0, float(len(t))) for t in texts]


class MemStore(Store):
    def __init__(self):
        self._meta, self._dim, self.rows = None, None, {}

    def meta(self):
        return self._meta

    def dimension(self):
        return self._dim

    def add(self, meta, chunks, vectors):
        dim = self.check_add(meta, chunks, vectors)
        if dim is None:
            return
        self._meta, self._dim = meta, dim
        self.rows.update({c.id: (c, tuple(v)) for c, v in zip(chunks, vectors)})

    def search(self, meta, vector, k):
        self.check_search(meta, vector, k)
        hits = [Hit(c, cosine(vector, v)) for c, v in self.rows.values()]
        return sorted(hits, key=lambda h: (-h.score, h.chunk.id))[:k]

    def clear(self):
        self._meta, self._dim, self.rows = None, None, {}


class MemStoreContractTest(StoreContract, unittest.TestCase):
    def make_store(self):
        return MemStore()


class InterfaceTest(unittest.TestCase):
    def test_son_abstractas(self):
        with self.assertRaises(TypeError):
            Embedder()
        with self.assertRaises(TypeError):
            Store()

    def test_embedder_meta(self):
        self.assertEqual(FakeEmbedder().meta, M1)

    def test_embed_checked_devuelve_tuplas(self):
        self.assertEqual(FakeEmbedder([[1, 2], [3, 4]]).embed_checked(["a", "b"]), [(1.0, 2.0), (3.0, 4.0)])

    def test_embed_checked_rechaza_forma_mala(self):
        for out, msg in (([(1.0,)], "se pidieron 2"), ([(1.0,), (1.0, 2.0)], "misma longitud"),
                         ([(1.0,), (float("nan"),)], "no finitos"), ([(), ()], "llegó vacío"),
                         ([(1.0,), (None,)], "no numéricos"), ([(1.0,), ("x",)], "no numéricos"),
                         ([(1.0,), (10 ** 400,)], "no numéricos")):
            with self.subTest(msg=msg), self.assertRaises(EmbedError) as cm:
                FakeEmbedder(out).embed_checked(["a", "b"])
            self.assertIn(msg, str(cm.exception))

    def test_model_y_version_son_obligatorios(self):
        class SinNada(Embedder):
            def embed(self, texts):
                return []

        class SoloModelo(SinNada):
            model = "m"

        with self.assertRaises(TypeError) as cm:
            SinNada()
        self.assertIn("model", str(cm.exception))
        with self.assertRaises(TypeError) as cm:
            SoloModelo()
        self.assertIn("version", str(cm.exception))

    def test_indexmeta_rechaza_campos_vacios(self):
        for args in (("", "1"), ("m", ""), ("  ", "1"), ("m", None)):
            with self.subTest(args=args), self.assertRaises(RagError) as cm:
                IndexMeta(*args)
            self.assertIn("IndexMeta.", str(cm.exception))

    def test_cosine_no_desborda(self):
        self.assertAlmostEqual(cosine((1e200, 1e200), (1e200, 1e200)), 1.0)
        self.assertAlmostEqual(cosine((1e200, 0), (0, 1e200)), 0.0)
        with self.assertRaises(EmbedError) as cm:
            cosine((1e308, 1e308), (float("inf"), 1.0))
        self.assertIn("no finit", str(cm.exception))

    def test_cosine(self):
        self.assertAlmostEqual(cosine((1, 0), (1, 0)), 1.0)
        self.assertAlmostEqual(cosine((1, 0), (0, 1)), 0.0)
        for a, b, msg in (((1, 0), (1, 0, 0), "longitud distinta"), ((0, 0), (1, 0), "norma 0")):
            with self.subTest(msg=msg), self.assertRaises(EmbedError) as cm:
                cosine(a, b)
            self.assertIn(msg, str(cm.exception))


class StoreIndiceVacioTest(unittest.TestCase):
    def test_indice_vacio_acepta_cualquier_meta(self):
        MemStore().check_meta(M2)


class ExtraTest(unittest.TestCase):
    def test_extra_ausente_nombra_la_orden(self):
        with self.assertRaises(MissingExtraError) as cm:
            require_extra("gworld_no_existe_xyz", "pgvector")
        self.assertIn('pip install "gworld[pgvector]"', str(cm.exception))
        self.assertIn("gworld_no_existe_xyz", str(cm.exception))
        self.assertIsInstance(cm.exception, ImportError)

    def test_extra_presente(self):
        self.assertIs(require_extra("json", "x"), __import__("json"))

    def test_fallo_interno_no_se_disfraza_de_extra(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "gw_rota_mod.py"), "w") as f:
                f.write("import gw_otro_que_no_existe\n")
            sys.path.insert(0, d)
            try:
                with self.assertRaises(ImportError) as cm:
                    require_extra("gw_rota_mod", "x")
                self.assertNotIsInstance(cm.exception, MissingExtraError)
                self.assertEqual(cm.exception.name, "gw_otro_que_no_existe")
            finally:
                sys.path.remove(d)

    def test_submodulo_ausente_es_extra_ausente(self):
        with self.assertRaises(MissingExtraError) as cm:
            require_extra("json.gw_no_existe", "pgvector")
        self.assertIn('pip install "gworld[pgvector]"', str(cm.exception))
        self.assertIn("json.gw_no_existe", str(cm.exception))

    def test_importar_gworld_rag_no_trae_extras(self):
        code = "import sys, gworld.rag; assert not {'psycopg','psycopg2','pgvector','numpy','requests'} & set(sys.modules)"
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
