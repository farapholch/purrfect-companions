"""Minimal läsare/skrivare för Bedrocks NBT (little-endian, okomprimerad).

Bedrock lagrar level.dat som 8 byte huvud (int32 version, int32 längd) följt
av en namnlös rotcompound. .mcstructure är samma NBT utan huvud. Ingen
tredjepartsmodul finns på maskinen — därav egen implementation. Endast de
taggtyper Bedrock faktiskt använder.
"""
import struct

TAG_END, TAG_BYTE, TAG_SHORT, TAG_INT, TAG_LONG = 0, 1, 2, 3, 4
TAG_FLOAT, TAG_DOUBLE, TAG_BYTES, TAG_STRING, TAG_LIST, TAG_COMPOUND = 5, 6, 7, 8, 9, 10
TAG_INT_ARRAY = 11


class Val:
    """Värde med explicit taggtyp — Python-typer räcker inte (byte vs int vs long)."""
    __slots__ = ("tag", "v")

    def __init__(self, tag, v):
        self.tag, self.v = tag, v

    def __repr__(self):
        return f"Val({self.tag},{self.v!r})"


def _rstr(d, o):
    n = struct.unpack_from("<H", d, o)[0]
    return d[o + 2:o + 2 + n].decode("utf8"), o + 2 + n


def _read(d, o, tag):
    if tag == TAG_BYTE: return Val(tag, d[o]), o + 1
    if tag == TAG_SHORT: return Val(tag, struct.unpack_from("<h", d, o)[0]), o + 2
    if tag == TAG_INT: return Val(tag, struct.unpack_from("<i", d, o)[0]), o + 4
    if tag == TAG_LONG: return Val(tag, struct.unpack_from("<q", d, o)[0]), o + 8
    if tag == TAG_FLOAT: return Val(tag, struct.unpack_from("<f", d, o)[0]), o + 4
    if tag == TAG_DOUBLE: return Val(tag, struct.unpack_from("<d", d, o)[0]), o + 8
    if tag == TAG_STRING:
        s, o = _rstr(d, o)
        return Val(tag, s), o
    if tag == TAG_LIST:
        et = d[o]; n = struct.unpack_from("<i", d, o + 1)[0]; o += 5
        out = []
        for _ in range(n):
            v, o = _read(d, o, et)
            out.append(v)
        return Val(tag, (et, out)), o
    if tag == TAG_COMPOUND:
        out = {}
        while True:
            t = d[o]; o += 1
            if t == TAG_END: break
            name, o = _rstr(d, o)
            v, o = _read(d, o, t)
            out[name] = v
        return Val(tag, out), o
    if tag == TAG_BYTES:
        n = struct.unpack_from("<i", d, o)[0]
        return Val(tag, d[o + 4:o + 4 + n]), o + 4 + n
    if tag == TAG_INT_ARRAY:
        n = struct.unpack_from("<i", d, o)[0]
        return Val(tag, list(struct.unpack_from(f"<{n}i", d, o + 4))), o + 4 + 4 * n
    raise ValueError(f"okänd tagg {tag} vid offset {o}")


def _wstr(s):
    b = s.encode("utf8")
    return struct.pack("<H", len(b)) + b


def _write(val):
    t, v = val.tag, val.v
    if t == TAG_BYTE: return bytes([v & 0xFF])
    if t == TAG_SHORT: return struct.pack("<h", v)
    if t == TAG_INT: return struct.pack("<i", v)
    if t == TAG_LONG: return struct.pack("<q", v)
    if t == TAG_FLOAT: return struct.pack("<f", v)
    if t == TAG_DOUBLE: return struct.pack("<d", v)
    if t == TAG_STRING: return _wstr(v)
    if t == TAG_LIST:
        et, items = v
        out = bytes([et]) + struct.pack("<i", len(items))
        for i in items:
            out += _write(i)
        return out
    if t == TAG_COMPOUND:
        out = b""
        for name, cv in v.items():
            out += bytes([cv.tag]) + _wstr(name) + _write(cv)
        return out + bytes([TAG_END])
    if t == TAG_BYTES: return struct.pack("<i", len(v)) + v
    if t == TAG_INT_ARRAY: return struct.pack("<i", len(v)) + struct.pack(f"<{len(v)}i", *v)
    raise ValueError(f"okänd tagg {t}")


def read_level_dat(path):
    d = open(path, "rb").read()
    version, length = struct.unpack_from("<ii", d, 0)
    tag = d[8]
    assert tag == TAG_COMPOUND
    _, o = _rstr(d, 9)
    root, _ = _read(d, o, TAG_COMPOUND)
    return version, root


def write_level_dat(path, version, root):
    body = bytes([TAG_COMPOUND]) + _wstr("") + _write(root)
    open(path, "wb").write(struct.pack("<ii", version, len(body)) + body)


def write_mcstructure(path, root):
    open(path, "wb").write(bytes([TAG_COMPOUND]) + _wstr("") + _write(root))
