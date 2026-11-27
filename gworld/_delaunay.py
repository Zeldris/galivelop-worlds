"""Triangulacion de Delaunay con el mismo orden de triangulos que Delaunator 5 (mapbox, licencia ISC).

FMG rehace las celdas de su mapa con Delaunator al cargar y los arrays por celda del archivo siguen ese orden;
por eso aqui no vale cualquier triangulacion: el orden de ordenacion, el hash del casco y la legalizacion de
aristas son los de esa biblioteca. ``triangulate(points)`` devuelve ``(triangles, halfedges)``: el triangulo ``t``
son las aristas ``3t``, ``3t+1`` y ``3t+2``; ``halfedges[e]`` es la arista opuesta o -1 en el casco.
"""

import math

EPS = 2.0**-52


def _d2(ax, ay, bx, by):
    return (ax - bx) ** 2 + (ay - by) ** 2


def _orient(ax, ay, bx, by, cx, cy):
    return (ay - cy) * (bx - cx) - (ax - cx) * (by - cy)


def _in_circle(ax, ay, bx, by, cx, cy, px, py):
    dx, dy, ex, ey, fx, fy = ax - px, ay - py, bx - px, by - py, cx - px, cy - py
    ap, bp, cp = dx * dx + dy * dy, ex * ex + ey * ey, fx * fx + fy * fy
    return dx * (ey * cp - bp * fy) - dy * (ex * cp - bp * fx) + ap * (ex * fy - ey * fx) < 0


def _circum(ax, ay, bx, by, cx, cy):
    dx, dy, ex, ey = bx - ax, by - ay, cx - ax, cy - ay
    bl, cl = dx * dx + dy * dy, ex * ex + ey * ey
    den = dx * ey - dy * ex
    if den == 0:
        return math.inf, None
    d = 0.5 / den
    x, y = (ey * bl - dy * cl) * d, (dx * cl - ex * bl) * d
    return x * x + y * y, (ax + x, ay + y)


def _angle(dx, dy):
    p = dx / (abs(dx) + abs(dy))
    return (3 - p if dy > 0 else 1 + p) / 4


def _sort(ids, dist, lo, hi):
    stack = [(lo, hi)]
    while stack:
        lo, hi = stack.pop()
        if hi - lo <= 20:
            for i in range(lo + 1, hi + 1):
                cur = ids[i]
                j = i - 1
                while j >= lo and dist[ids[j]] > dist[cur]:
                    ids[j + 1] = ids[j]
                    j -= 1
                ids[j + 1] = cur
            continue
        mid = (lo + hi) >> 1
        i, j = lo + 1, hi
        ids[mid], ids[i] = ids[i], ids[mid]
        if dist[ids[lo]] > dist[ids[hi]]:
            ids[lo], ids[hi] = ids[hi], ids[lo]
        if dist[ids[i]] > dist[ids[hi]]:
            ids[i], ids[hi] = ids[hi], ids[i]
        if dist[ids[lo]] > dist[ids[i]]:
            ids[lo], ids[i] = ids[i], ids[lo]
        pivot = ids[i]
        pd = dist[pivot]
        while True:
            i += 1
            while dist[ids[i]] < pd:
                i += 1
            j -= 1
            while dist[ids[j]] > pd:
                j -= 1
            if j < i:
                break
            ids[i], ids[j] = ids[j], ids[i]
        ids[lo + 1] = ids[j]
        ids[j] = pivot
        if hi - i + 1 >= j - lo:
            stack += [(lo, j - 1), (i, hi)]
        else:
            stack += [(i, hi), (lo, j - 1)]


class _Tri:
    def __init__(self, pts):
        n = len(pts)
        self.n = n
        self.c = [float(v) for p in pts for v in p[:2]]
        size = max(2 * n - 5, 0) * 3
        self.tri = [0] * size
        self.half = [0] * size
        self.count = 0
        self.hsize = math.ceil(math.sqrt(n))
        self.prev = [0] * n
        self.next = [0] * n
        self.htri = [0] * n
        self.hash = [-1] * self.hsize
        self.stack = [0] * 512
        self._build()

    def _key(self, x, y):
        return math.floor(_angle(x - self.cx, y - self.cy) * self.hsize) % self.hsize

    def _link(self, a, b):
        self.half[a] = b
        if b != -1:
            self.half[b] = a

    def _add(self, a, b, c, ha, hb, hc):
        t = self.count
        self.tri[t:t + 3] = [a, b, c]
        self._link(t, ha)
        self._link(t + 1, hb)
        self._link(t + 2, hc)
        self.count += 3
        return t

    def _build(self):
        n, c = self.n, self.c
        xs, ys = c[0::2], c[1::2]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        i0 = min(range(n), key=lambda i: (_d2(cx, cy, xs[i], ys[i]), i))
        best = math.inf
        i1 = None
        for i in range(n):
            d = _d2(xs[i0], ys[i0], xs[i], ys[i])
            if i != i0 and 0 < d < best:
                i1, best = i, d
        best, i2 = math.inf, None
        for i in range(n):
            if i in (i0, i1):
                continue
            r, _ = _circum(xs[i0], ys[i0], xs[i1], ys[i1], xs[i], ys[i])
            if r < best:
                i2, best = i, r
        if i2 is None:
            raise ValueError("puntos colineales: no hay triangulacion")
        if _orient(xs[i0], ys[i0], xs[i1], ys[i1], xs[i2], ys[i2]) < 0:
            i1, i2 = i2, i1
        _, (self.cx, self.cy) = _circum(xs[i0], ys[i0], xs[i1], ys[i1], xs[i2], ys[i2])
        dist = [_d2(xs[i], ys[i], self.cx, self.cy) for i in range(n)]
        ids = list(range(n))
        _sort(ids, dist, 0, n - 1)
        prev, nxt, htri, hh = self.prev, self.next, self.htri, self.hash
        self.start = i0
        nxt[i0] = prev[i2] = i1
        nxt[i1] = prev[i0] = i2
        nxt[i2] = prev[i1] = i0
        htri[i0], htri[i1], htri[i2] = 0, 1, 2
        for i in (i0, i1, i2):
            hh[self._key(xs[i], ys[i])] = i
        self._add(i0, i1, i2, -1, -1, -1)
        xp = yp = None
        for k, i in enumerate(ids):
            x, y = xs[i], ys[i]
            if k > 0 and abs(x - xp) <= EPS and abs(y - yp) <= EPS:
                continue
            xp, yp = x, y
            if i in (i0, i1, i2):
                continue
            key = self._key(x, y)
            start = 0
            for j in range(self.hsize):
                start = hh[(key + j) % self.hsize]
                if start != -1 and start != nxt[start]:
                    break
            start = prev[start]
            e = start
            while True:
                q = nxt[e]
                if not _orient(x, y, xs[e], ys[e], xs[q], ys[q]) >= 0:
                    break
                e = q
                if e == start:
                    e = -1
                    break
            if e == -1:
                continue
            t = self._add(e, i, nxt[e], -1, -1, htri[e])
            htri[i] = self._legalize(t + 2)
            htri[e] = t
            m = nxt[e]
            while True:
                q = nxt[m]
                if not _orient(x, y, xs[m], ys[m], xs[q], ys[q]) < 0:
                    break
                t = self._add(m, i, q, htri[i], -1, htri[m])
                htri[i] = self._legalize(t + 2)
                nxt[m] = m
                m = q
            if e == start:
                while True:
                    q = prev[e]
                    if not _orient(x, y, xs[q], ys[q], xs[e], ys[e]) < 0:
                        break
                    t = self._add(q, i, e, -1, htri[e], htri[q])
                    self._legalize(t + 2)
                    htri[q] = t
                    nxt[e] = e
                    e = q
            self.start = prev[i] = e
            nxt[e] = prev[m] = i
            nxt[i] = m
            hh[self._key(x, y)] = i
            hh[self._key(xs[e], ys[e])] = e

    def _legalize(self, a):
        tri, half, c, stack = self.tri, self.half, self.c, self.stack
        depth = 0
        while True:
            b = half[a]
            a0 = a - a % 3
            ar = a0 + (a + 2) % 3
            if b == -1:
                if depth == 0:
                    break
                depth -= 1
                a = stack[depth]
                continue
            b0 = b - b % 3
            al = a0 + (a + 1) % 3
            bl = b0 + (b + 2) % 3
            p0, pr, pl, p1 = tri[ar], tri[a], tri[al], tri[bl]
            if _in_circle(c[2 * p0], c[2 * p0 + 1], c[2 * pr], c[2 * pr + 1],
                          c[2 * pl], c[2 * pl + 1], c[2 * p1], c[2 * p1 + 1]):
                tri[a], tri[b] = p1, p0
                hbl = half[bl]
                if hbl == -1:
                    e = self.start
                    while True:
                        if self.htri[e] == bl:
                            self.htri[e] = a
                            break
                        e = self.prev[e]
                        if e == self.start:
                            break
                self._link(a, hbl)
                self._link(b, half[ar])
                self._link(ar, bl)
                if depth < len(stack):
                    stack[depth] = b0 + (b + 1) % 3
                    depth += 1
            else:
                if depth == 0:
                    break
                depth -= 1
                a = stack[depth]
        return ar


def triangulate(points):
    """(triangles, halfedges) de la triangulacion de Delaunay de ``points`` ([x, y], al menos 3 no colineales)."""
    t = _Tri(points)
    return t.tri[:t.count], t.half[:t.count]
