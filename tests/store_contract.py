"""Suite de contrato de ``Store`` (RAG-3): mixin reutilizable, no es un ``TestCase`` y no se descubre sola.

Uso: ``class MiTest(StoreContract, unittest.TestCase)`` con ``make_store(self)`` que devuelve un almacén vacío.
"""

from gworld.chunks import Chunk
from gworld.rag import IndexMeta, IndexMismatchError, StoreError

M1 = IndexMeta("bge-m3", "sha:1")
M2 = IndexMeta("bge-m3", "sha:2")


def chunk(i: str, n: int = 0) -> Chunk:
    return Chunk(id=f"chunk:{i}", fact_id="fact:x", n=n, text=f"texto {i}")


class StoreContract:
    def make_store(self):
        raise NotImplementedError

    def test_vacio_no_tiene_meta(self):
        s = self.make_store()
        self.assertIsNone(s.meta())
        self.assertIsNone(s.dimension())
        self.assertEqual(s.search(M1, (1.0, 0.0), 3), [])

    def test_primer_add_fija_meta_y_dimension(self):
        s = self.make_store()
        s.add(M1, [chunk("a")], [(1.0, 0.0, 0.0)])
        self.assertEqual(s.meta(), M1)
        self.assertEqual(s.dimension(), 3)

    def test_add_vacio_no_fija_meta(self):
        s = self.make_store()
        s.add(M1, [], [])
        self.assertIsNone(s.meta())
        s.add(M2, [chunk("a")], [(1.0, 0.0)])
        self.assertEqual(s.meta(), M2)

    def test_longitudes_distintas_fallan_sin_guardar(self):
        s = self.make_store()
        with self.assertRaises(StoreError) as cm:
            s.add(M1, [chunk("a"), chunk("b")], [(1.0, 0.0)])
        self.assertIn("2 fragmentos y 1 vectores", str(cm.exception))
        self.assertIsNone(s.meta())
        self.assertEqual(s.search(M1, (1.0, 0.0), 5), [])

    def test_dimension_distinta_falla_sin_guardar(self):
        s = self.make_store()
        s.add(M1, [chunk("a")], [(1.0, 0.0)])
        with self.assertRaises(StoreError) as cm:
            s.add(M1, [chunk("b")], [(1.0, 0.0, 0.0)])
        self.assertIn("dimensión 3 y el índice 2", str(cm.exception))
        self.assertEqual([h.chunk.id for h in s.search(M1, (1.0, 0.0), 5)], ["chunk:a"])

    def test_vectores_de_distinta_longitud_entre_si_fallan(self):
        s = self.make_store()
        with self.assertRaises(StoreError) as cm:
            s.add(M1, [chunk("a"), chunk("b")], [(1.0, 0.0), (1.0,)])
        self.assertIn("misma longitud", str(cm.exception))
        self.assertIsNone(s.meta())

    def test_k_no_positivo_falla(self):
        s = self.make_store()
        s.add(M1, [chunk("a")], [(1.0, 0.0)])
        for k in (0, -1):
            with self.subTest(k=k), self.assertRaises(StoreError) as cm:
                s.search(M1, (1.0, 0.0), k)
            self.assertIn("mayor que 0", str(cm.exception))

    def test_consulta_de_otra_dimension_falla(self):
        s = self.make_store()
        s.add(M1, [chunk("a")], [(1.0, 0.0)])
        with self.assertRaises(StoreError) as cm:
            s.search(M1, (1.0, 0.0, 0.0), 1)
        self.assertIn("dimensión 3 y el índice 2", str(cm.exception))

    def test_otro_modelo_pide_reindexar(self):
        s = self.make_store()
        s.add(M1, [chunk("a")], [(1.0, 0.0)])
        for call in (lambda: s.search(M2, (1.0, 0.0), 1), lambda: s.add(M2, [chunk("b")], [(0.0, 1.0)])):
            with self.assertRaises(IndexMismatchError) as cm:
                call()
            self.assertIn("reindexa", str(cm.exception))
            self.assertIn("bge-m3 sha:1", str(cm.exception))

    def test_clear_permite_otro_modelo_y_otra_dimension(self):
        s = self.make_store()
        s.add(M1, [chunk("a")], [(1.0, 0.0)])
        s.clear()
        self.assertIsNone(s.meta())
        self.assertIsNone(s.dimension())
        s.add(M2, [chunk("a")], [(1.0, 0.0, 0.0)])
        self.assertEqual((s.meta(), s.dimension()), (M2, 3))

    def test_mismo_id_sustituye(self):
        s = self.make_store()
        s.add(M1, [chunk("a")], [(1.0, 0.0)])
        s.add(M1, [Chunk(id="chunk:a", fact_id="fact:y", n=7, text="nuevo")], [(0.0, 1.0)])
        hits = s.search(M1, (0.0, 1.0), 5)
        self.assertEqual(len(hits), 1)
        self.assertEqual((hits[0].chunk.fact_id, hits[0].chunk.n, hits[0].chunk.text), ("fact:y", 7, "nuevo"))
        self.assertAlmostEqual(hits[0].score, 1.0)

    def test_orden_por_score_y_luego_por_id_y_tope_k(self):
        s = self.make_store()
        s.add(M1, [chunk("c"), chunk("b"), chunk("a"), chunk("far")],
              [(1.0, 0.0), (1.0, 0.0), (1.0, 0.0), (0.0, 1.0)])
        self.assertEqual([h.chunk.id for h in s.search(M1, (1.0, 0.0), 10)],
                         ["chunk:a", "chunk:b", "chunk:c", "chunk:far"])
        self.assertEqual([h.chunk.id for h in s.search(M1, (1.0, 0.0), 2)], ["chunk:a", "chunk:b"])
        scores = [h.score for h in s.search(M1, (1.0, 0.2), 10)]
        self.assertEqual(scores, sorted(scores, reverse=True))
