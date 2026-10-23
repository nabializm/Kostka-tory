#!/usr/bin/env python3
"""Warstwa 2: współrzędne liter w kostce. Wymaga data/ z build_corpus.py.
Uruchomienie:  python build_cube.py
Wynik: data/torah_cube.csv.gz  (idx, litera, księga, rozdział, wers, x, y, z, shell, skok)
x,y,z = 0..68; środek kostki = (34,34,34) = litera nr 1.
"""
import gzip, csv, math, sys

def corners(k): return [(-k,-k),(-k,k),(k,-k),(k,k)]

def snake(k, start):
    """Wąż po ścianie (2k+1)^2 od narożnika start; kończy w przeciwległym narożniku."""
    sx, sz = start
    dx = 1 if sx < 0 else -1
    dz0 = 1 if sz < 0 else -1
    out, dz = [], dz0
    for i in range(2*k+1):
        x = sx + dx*i
        zs = range(-k, k+1) if dz > 0 else range(k, -k-1, -1)
        out += [(x, z) for z in zs]
        dz = -dz
    return out

def ring(k):
    """Obwód ramki jako cykl pól (x,z)."""
    r = [(-k, z) for z in range(-k, k+1)]
    r += [(x, k) for x in range(-k+1, k+1)]
    r += [(k, z) for z in range(k-1, -k-1, -1)]
    r += [(x, -k) for x in range(k-1, -k, -1)]
    return r

def dist(a, b): return sum(abs(p-q) for p, q in zip(a, b))

def build(total):
    path = [(0, 0, 0)]
    k = 1
    while len(path) < total:
        top_first = (k % 2 == 1)                    # powłoki na przemian: z góry / z dołu
        ys = list(range(k, -k-1, -1)) if top_first else list(range(-k, k+1))
        prev = path[-1]
        # twarz startowa: najbliższy narożnik
        c = min(corners(k), key=lambda q: dist(prev, (q[0], ys[0], q[1])))
        cells = [(x, ys[0], z) for x, z in snake(k, c)]
        r = ring(k); n = len(r)
        pos = r.index((cells[-1][0], cells[-1][2]))
        for y in ys[1:-1]:
            cells += [(r[(pos+i) % n][0], y, r[(pos+i) % n][1]) for i in range(n)]
            pos = (pos + n - 1) % n                 # koniec = poprzednik startu w cyklu
        last = cells[-1]
        c = min(corners(k), key=lambda q: dist(last, (q[0], ys[-1], q[1])))
        cells += [(x, ys[-1], z) for x, z in snake(k, c)]
        path += cells
        k += 1
    return path[:total]

def main():
    rows = list(csv.reader(gzip.open("data/torah_letters.csv.gz", "rt", encoding="utf-8")))
    hdr, data = rows[0], rows[1:]
    total = len(data)
    path = build(total)
    assert len(set(path)) == total, "powtórzone pola!"
    jumps = 0
    out = gzip.open("data/torah_cube.csv.gz", "wt", encoding="utf-8", newline="")
    w = csv.writer(out)
    w.writerow(["idx", "letter", "book", "chapter", "verse", "x", "y", "z", "shell", "jump"])
    for i, (r, p) in enumerate(zip(data, path)):
        j = 0 if i == 0 else int(dist(p, path[i-1]) != 1)
        jumps += j
        w.writerow([r[0], r[7], r[2], r[3], r[4], p[0]+34, p[1]+34, p[2]+34, max(map(abs, p)), j])
    out.close()
    print(f"liter: {total}, unikalnych pól: {len(set(path))}, skoków: {jumps}, powłok: {max(max(map(abs,p)) for p in path)}")

if __name__ == "__main__":
    main()
