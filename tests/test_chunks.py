"""RAG-1: troceado del canon en Chunk con los ids de hecho."""

import dataclasses
import hashlib
import json
import re
import unittest
from pathlib import Path

from gworld.canon import Fact, read_facts
from gworld.chunks import Chunk, ChunkError, chunk_facts

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "examples" / "valle-brumas"


def fact(text: str, id: str = "fact:" + "a" * 32) -> Fact:
    return Fact(id=id, file="a.md", headings=(), text=text, sha256="sha256:x")


def words(n: int, start: int = 0) -> str:
    return " ".join(f"w{i}" for i in range(start, start + n))


def all_words(chunks) -> list[str]:
    return [w for c in chunks for w in c.text.split()]


class ChunkTest(unittest.TestCase):
    def test_inmutable_y_to_json(self):
        c = chunk_facts([fact("hola mundo")])[0]
        self.assertEqual(c.to_json(), {"id": c.id, "fact_id": "fact:" + "a" * 32, "n": 0, "text": "hola mundo"})
        with self.assertRaises(dataclasses.FrozenInstanceError):
            c.text = "otro"  # type: ignore[misc]

    def test_hecho_corto_es_un_chunk(self):
        cs = chunk_facts([fact("Un hecho corto.")])
        self.assertEqual([(c.n, c.text) for c in cs], [(0, "Un hecho corto.")])
        self.assertRegex(cs[0].id, r"^chunk:[0-9a-f]{32}$")

    def test_hecho_vacio_no_da_chunk(self):
        self.assertEqual(chunk_facts([fact(""), fact("  \n\n ")]), ())
        self.assertEqual(chunk_facts([]), ())

    def test_exactamente_max_words_es_un_chunk(self):
        self.assertEqual(len(chunk_facts([fact(words(5))], 5)), 1)

    def test_una_palabra_de_mas_son_dos(self):
        cs = chunk_facts([fact(words(6))], 5)
        self.assertEqual([len(c.text.split()) for c in cs], [5, 1])

    def test_parrafo_largo_se_parte_por_frases_y_palabras(self):
        text = "Uno dos tres. Cuatro cinco seis siete.\n\nOcho nueve diez once doce trece catorce."
        cs = chunk_facts([fact(text)], 3)
        self.assertEqual([c.text for c in cs],
                         ["Uno dos tres.", "Cuatro cinco seis", "siete.", "Ocho nueve diez", "once doce trece", "catorce."])
        cs = chunk_facts([fact(text)], 5)
        self.assertEqual([c.text for c in cs],
                         ["Uno dos tres.", "Cuatro cinco seis siete.", "Ocho nueve diez once doce", "trece catorce."])

    def test_se_agrupan_parrafos_con_su_separador(self):
        cs = chunk_facts([fact("a b\n\nc d\n\ne f g")], 4)
        self.assertEqual([c.text for c in cs], ["a b\n\nc d", "e f g"])

    def test_parrafo_mayor_que_el_tope_no_pasa_del_tope(self):
        text = words(10) + "\n\n" + words(25, 10) + ". Fin de la frase corta."
        for m in (1, 2, 7, 10):
            cs = chunk_facts([fact(text)], m)
            self.assertTrue(all(1 <= len(c.text.split()) <= m for c in cs), m)

    def test_fila_de_tabla_no_se_parte_si_cabe(self):
        cs = chunk_facts([fact("| a | b |\n| c | d |")], 6)
        self.assertEqual([c.text for c in cs], ["| a | b |", "| c | d |"])

    def test_linea_mayor_que_el_tope_se_parte_por_palabras(self):
        cs = chunk_facts([fact("| a | b | c | d |\n| e |")], 3)
        self.assertEqual([c.text for c in cs], ["| a |", "b | c", "| d |", "| e |"])

    def test_palabra_sin_espacios_larga(self):
        cs = chunk_facts([fact("x" * 5000)], 3)
        self.assertEqual([c.text for c in cs], ["x" * 5000])

    def test_unicode(self):
        text = "El dragón ¿vive? Sí… ñandú 龍 vive. Ça va très bien ¡ya!"
        cs = chunk_facts([fact(text)], 3)
        self.assertEqual(all_words(cs), text.split())
        self.assertTrue(all(len(c.text.split()) <= 3 for c in cs))

    def test_max_words_invalido(self):
        for bad in (0, -1, 1.5, "3", None, True):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ChunkError, r"max_words debe ser un entero mayor que 0"):
                    chunk_facts([fact("a b")], bad)  # type: ignore[arg-type]
        self.assertTrue(issubclass(ChunkError, ValueError))

    def test_ids_deterministas(self):
        facts = [fact(words(30), "fact:" + "1" * 32), fact(words(7), "fact:" + "2" * 32)]
        self.assertEqual(chunk_facts(facts, 8), chunk_facts(facts, 8))
        ids = [c.id for c in chunk_facts(facts, 8)]
        self.assertEqual(len(ids), len(set(ids)))

    def test_mismo_texto_en_dos_hechos_ids_distintos(self):
        a, b = chunk_facts([fact("igual", "fact:" + "1" * 32), fact("igual", "fact:" + "2" * 32)])
        self.assertNotEqual(a.id, b.id)

    def test_mismo_texto_en_dos_fragmentos_ids_distintos(self):
        a, b = chunk_facts([fact("x\n\nx")], 1)
        self.assertEqual(a.text, b.text)
        self.assertNotEqual(a.id, b.id)

    def test_id_fijo_con_texto_no_ascii(self):
        fid, text = "fact:" + "a" * 32, "dragón 龍"
        key = json.dumps([fid, 0, text], ensure_ascii=False)
        expected = "chunk:" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]
        self.assertEqual(chunk_facts([fact(text, fid)])[0].id, expected)
        self.assertEqual(expected, "chunk:" + hashlib.sha256(
            ('["fact:' + "a" * 32 + '", 0, "dragón 龍"]').encode("utf-8")).hexdigest()[:32])

    def test_editar_un_hecho_cambia_solo_sus_ids(self):
        a, b = fact(words(30), "fact:" + "1" * 32), fact(words(30, 100), "fact:" + "2" * 32)
        before = chunk_facts([a, b], 10)
        b2 = dataclasses.replace(b, text=b.text[:-1] + "X")
        after = chunk_facts([a, b2], 10)
        of = lambda cs, fid: [c.id for c in cs if c.fact_id == fid]
        self.assertEqual(of(before, a.id), of(after, a.id))
        self.assertEqual(len(of(before, b.id)), len(of(after, b.id)))
        self.assertNotEqual(of(before, b.id)[-1], of(after, b.id)[-1])
        self.assertEqual(of(before, b.id)[:-1], of(after, b.id)[:-1])

    def test_cubre_todo_el_texto_en_orden(self):
        text = "Uno dos. Tres cuatro cinco seis.\n\n" + words(40) + "! Siete.\n\nOcho  nueve\tdiez"
        for m in (1, 2, 3, 6, 50):
            cs = chunk_facts([fact(text)], m)
            self.assertEqual(all_words(cs), text.split(), m)
            self.assertEqual([c.n for c in cs], list(range(len(cs))))

    def test_canon_del_mundo_de_ejemplo(self):
        facts = read_facts(EXAMPLE / "canon")
        for m in (3, 200):
            cs = chunk_facts(facts, m)
            self.assertTrue(cs)
            self.assertTrue(all(len(c.text.split()) <= m for c in cs))
            for f in facts:
                mine = [c for c in cs if c.fact_id == f.id]
                self.assertEqual(all_words(mine), f.text.split())
            self.assertTrue(all(re.match(r"^chunk:[0-9a-f]{32}$", c.id) for c in cs))
        self.assertEqual(len(chunk_facts(facts)), len({c.fact_id for c in chunk_facts(facts)}) +
                         sum(1 for c in chunk_facts(facts) if c.n > 0))


if __name__ == "__main__":
    unittest.main()
