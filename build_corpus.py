#!/usr/bin/env python3
"""Warstwa 1: oczyszczona baza liter Pięcioksięgu (WLC / OSHB, domena publiczna).
Uruchomienie (Colab lub lokalnie):  python build_corpus.py
Wynik w folderze data/: torah_letters.csv.gz, torah_words.csv, torah_verses.csv, stats.txt
"""
import os, re, csv, gzip, urllib.request, xml.etree.ElementTree as ET

BASE = "https://raw.githubusercontent.com/openscriptures/morphhb/master/wlc/"
BOOKS = [("Gen", "genesis"), ("Exod", "exodus"), ("Lev", "leviticus"),
         ("Num", "numbers"), ("Deut", "deuteronomy")]
NS = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"
LETTERS = re.compile(r"[\u05D0-\u05EA]")          # tylko spółgłoski, bez nikkud i akcentów
SOFIT = set("ךםןףץ")
OUT = "data"; os.makedirs(OUT, exist_ok=True); os.makedirs("raw", exist_ok=True)

def fetch(code):
    path = f"raw/{code}.xml"
    if not os.path.exists(path):
        urllib.request.urlretrieve(BASE + code + ".xml", path)
    return path

def parse_verse(verse):
    """Słowa bezpośrednio w wersie. Pomijamy <note> (m.in. qere w <rdg>), zostaje ketiv."""
    words = []
    for el in verse:
        if el.tag == NS + "w":
            raw = "".join(el.itertext())
            letters = "".join(LETTERS.findall(raw))
            if letters:
                words.append((el.get("id"), letters))
    return words

g = 0
wl, ww, wv = [], [], []
stats = []
for bi, (code, slug) in enumerate(BOOKS, 1):
    root = ET.parse(fetch(code)).getroot()
    book_letters = 0
    for verse in root.iter(NS + "verse"):
        _, ch, vs = verse.get("osisID").split(".")
        ch, vs = int(ch), int(vs)
        words = parse_verse(verse)
        v_start = g + 1
        for wi, (wid, w) in enumerate(words, 1):
            w_start = g + 1
            for li, c in enumerate(w, 1):
                g += 1
                wl.append((g, bi, slug, ch, vs, wi, li, c, int(c in SOFIT), wid))
            ww.append((len(ww) + 1, bi, slug, ch, vs, wi, w, w_start, g, wid))
        if g >= v_start:
            wv.append((bi, slug, ch, vs, v_start, g))
        book_letters += g - v_start + 1 if g >= v_start else 0
    stats.append((slug, sum(1 for r in wl if r[1] == bi)))

with gzip.open(f"{OUT}/torah_letters.csv.gz", "wt", encoding="utf-8", newline="") as f:
    w = csv.writer(f); w.writerow("idx,book_no,book,chapter,verse,word_in_verse,letter_in_word,letter,is_sofit,word_id".split(","))
    w.writerows(wl)
with open(f"{OUT}/torah_words.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f); w.writerow("word_no,book_no,book,chapter,verse,word_in_verse,word,first_idx,last_idx,word_id".split(","))
    w.writerows(ww)
with open(f"{OUT}/torah_verses.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f); w.writerow("book_no,book,chapter,verse,first_idx,last_idx".split(","))
    w.writerows(wv)

lines = [f"{s}: {n} liter" for s, n in stats] + [f"RAZEM: {g} liter, {len(ww)} słów, {len(wv)} wersów"]
open(f"{OUT}/stats.txt", "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines))
