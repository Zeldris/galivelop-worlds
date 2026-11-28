"""RAG-2: interfaces Store y Embedder; un extra que falte falla con la orden que lo instala."""

import subprocess
import sys
import unittest

from gworld.chunks import Chunk
from gworld.rag import (EmbedError, Embedder, Hit, IndexMeta, IndexMismatchError, MissingExtraError, Store,
                        cosine, require_extra)

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
        self._meta, self.rows = None, {}

    def meta(self):
        return self._meta

    def add(self, meta, chunks, vectors):
        self.check_meta(meta)
        self._meta = meta
        self.rows.update({c.id: (c, v) for c, v in zip(chunks, vectors)})

    def search(self, meta, vector, k):
        self.check_meta(meta)
        hits = [Hit(c, cosine(vector, v)) for c, v in self.rows.values()]
        return sorted(hits, key=lambda h: -h.score)[:k]

    def clear(self):
        self._meta, self.rows = None, {}


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
                         ([(1.0,), (float("nan"),)], "no finitos")):
            with self.subTest(msg=msg), self.assertRaises(EmbedError) as cm:
                FakeEmbedder(out).embed_checked(["a", "b"])
            self.assertIn(msg, str(cm.exception))

    def test_cosine(self):
        self.assertAlmostEqual(cosine((1, 0), (1, 0)), 1.0)
        self.assertAlmostEqual(cosine((1, 0), (0, 1)), 0.0)
        for a, b, msg in (((1, 0), (1, 0, 0), "longitud distinta"), ((0, 0), (1, 0), "norma 0")):
            with self.subTest(msg=msg), self.assertRaises(EmbedError) as cm:
                cosine(a, b)
            self.assertIn(msg, str(cm.exception))


class StoreContractTest(unittest.TestCase):
    def test_consultar_con_otro_modelo_pide_reindexar(self):
        s = MemStore()
        s.add(M1, [chunk(0)], [(1.0, 0.0)])
        for call in (lambda: s.search(M2, (1.0, 0.0), 1), lambda: s.add(M2, [chunk(1)], [(0.0, 1.0)])):
            with self.assertRaises(IndexMismatchError) as cm:
                call()
            self.assertIn("reindexa", str(cm.exception))
            self.assertIn("nomic-embed-text 1", str(cm.exception))

    def test_clear_permite_otro_modelo(self):
        s = MemStore()
        s.add(M1, [chunk(0)], [(1.0, 0.0)])
        s.clear()
        self.assertIsNone(s.meta())
        s.add(M2, [chunk(0)], [(1.0, 0.0)])
        self.assertEqual(s.meta(), M2)

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
        import os, tempfile
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "gw_rota_mod.py"), "w") as f:
                f.write("import gw_otro_que_no_existe\n")
            sys.path.insert(0, d)
            try:
                with self.assertRaises(ImportError) as cm:
                    require_extra("gw_rota_mod", "x")
                self.assertNotIsInstance(cm.exception, MissingExtraError)
            finally:
                sys.path.remove(d)

    def test_importar_gworld_rag_no_trae_extras(self):
        code = "import sys, gworld.rag; assert not {'psycopg','psycopg2','pgvector','numpy','requests'} & set(sys.modules)"
        subprocess.run([sys.executable, "-c", code], check=True)


if __name__ == "__main__":
    unittest.main()
