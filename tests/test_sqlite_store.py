"""RAG-3: ``SqliteStore`` pasa el contrato, persiste y pide reindexar con otro modelo."""

import os
import sqlite3
import tempfile
import unittest

from gworld.rag import IndexMismatchError, StoreError
from gworld.sqlite_store import SqliteStore
from tests.store_contract import M1, M2, StoreContract, chunk


class SqliteStoreContractTest(StoreContract, unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.path = os.path.join(d.name, "rag.sqlite")

    def make_store(self):
        s = SqliteStore(self.path)
        self.addCleanup(s.close)
        return s


class SqlitePersistenceTest(unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.path = os.path.join(d.name, "rag.sqlite")

    def test_persiste_entre_aperturas_con_meta(self):
        with SqliteStore(self.path) as s:
            s.add(M1, [chunk("a", 3)], [(0.5, 0.25)])
        with SqliteStore(self.path) as s:
            self.assertEqual((s.meta(), s.dimension()), (M1, 2))
            (hit,) = s.search(M1, (0.5, 0.25), 1)
            self.assertEqual(hit.chunk, chunk("a", 3))
            with self.assertRaises(IndexMismatchError) as cm:
                s.search(M2, (0.5, 0.25), 1)
            self.assertIn("reindexa", str(cm.exception))

    def test_add_fallido_no_deja_meta_a_medias(self):
        with SqliteStore(self.path) as s:
            with self.assertRaises(StoreError):
                s.add(M1, [chunk("a")], [])
        with SqliteStore(self.path) as s:
            self.assertIsNone(s.meta())

    def test_fallo_a_mitad_de_add_revierte_todo(self):
        with SqliteStore(self.path) as s:
            bad = chunk("b")
            object.__setattr__(bad, "text", object())  # tipo que sqlite3 no sabe guardar: falla en la 2.ª fila
            with self.assertRaises(sqlite3.ProgrammingError) as cm:
                s.add(M1, [chunk("a"), bad], [(1.0, 0.0), (0.0, 1.0)])
            self.assertIn("not supported", str(cm.exception))
            self.assertIsNone(s.meta())
            self.assertEqual(s._db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
