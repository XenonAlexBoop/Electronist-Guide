"""Rebuild ElectronistGuide.exe by swapping the app's own byte-code into the
existing (Windows) PyInstaller one-dir executable. Runs under CPython 3.12
(same bytecode magic as the bundled python312.dll)."""
import sys, os, struct, marshal, zlib, importlib.util, glob
SRC, ORIG, OUT = sys.argv[1:4]
assert sys.version_info[:2] == (3, 12)
data = open(ORIG, 'rb').read()
MAGIC = b'MEI\014\013\012\013\016'
ck = data.rfind(MAGIC)
COOKIE_FMT = '!8sIIII64s'
magic, pkglen, tocoff, toclen, pyver, pylib = struct.unpack(COOKIE_FMT, data[ck:ck + struct.calcsize(COOKIE_FMT)])
pkg_start = ck + struct.calcsize(COOKIE_FMT) - pkglen
boot = data[:pkg_start]
pkg = data[pkg_start:ck + struct.calcsize(COOKIE_FMT)]
# parse CArchive TOC
entries = []
p = tocoff
while p < tocoff + toclen:
    elen, off, clen, ulen, cflag, tc = struct.unpack('!IIIIBc', pkg[p:p + 18])
    name = pkg[p + 18:p + elen].rstrip(b'\0').decode()
    entries.append([name, off, clen, ulen, cflag, tc.decode(), pkg[off:off + clen]])
    p += elen
print("CArchive entries:", [(e[0], e[5]) for e in entries])

# ---------------- PYZ ----------------
pyz_e = next(e for e in entries if e[0] == 'PYZ.pyz')
pyz = pyz_e[6] if not pyz_e[4] else zlib.decompress(pyz_e[6])
assert pyz[:4] == b'PYZ\0' and pyz[4:8] == importlib.util.MAGIC_NUMBER
(toc_off,) = struct.unpack('!i', pyz[8:12])
toc = marshal.loads(pyz[toc_off:])
toc = list(toc.items()) if isinstance(toc, dict) else list(toc)
blobs = {name: (tc, pyz[o:o + l]) for name, (tc, o, l) in toc}
order = [name for name, _ in toc]

# project modules (from source)
mods = {}
for path in glob.glob(os.path.join(SRC, '*.py')) + glob.glob(os.path.join(SRC, '*', '*.py')):
    rel = os.path.relpath(path, SRC)
    if rel == 'main.py':
        continue
    parts = rel[:-3].split(os.sep)
    is_pkg = parts[-1] == '__init__'
    name = '.'.join(parts[:-1]) if is_pkg else '.'.join(parts)
    co_name = '\\'.join(parts) + '.py'
    code = compile(open(path, encoding='utf-8').read(), co_name, 'exec', dont_inherit=True, optimize=0)
    mods[name] = (1 if is_pkg else 0, zlib.compress(marshal.dumps(code), 6))
app_roots = {n.split('.')[0] for n in mods}
removed = [n for n in order if n.split('.')[0] in app_roots and n not in mods]
print("removed from PYZ:", removed)
for n in removed:
    order.remove(n); blobs.pop(n)
added = [n for n in mods if n not in blobs]
print("added to PYZ:", added)
for n, v in mods.items():
    blobs[n] = v
    if n not in order:
        order.append(n)
body = bytearray(b'\0' * 17)
newtoc = []
for n in order:
    tc, blob = blobs[n]
    newtoc.append((n, (tc, len(body), len(blob))))
    body += blob
toc_offset = len(body)
body += marshal.dumps(newtoc)
body[0:12] = b'PYZ\0' + importlib.util.MAGIC_NUMBER + struct.pack('!i', toc_offset)
new_pyz = bytes(body)

# ---------------- main script ----------------
main_code = compile(open(os.path.join(SRC, 'main.py'), encoding='utf-8').read(), 'main.py', 'exec',
                    dont_inherit=True, optimize=0)
main_raw = marshal.dumps(main_code)

# ---------------- rebuild CArchive ----------------
out = bytearray()
toc_entries = []
for name, off, clen, ulen, cflag, tc, blob in entries:
    if name == 'PYZ.pyz':
        raw, cflag2 = new_pyz, cflag
        blob2 = zlib.compress(raw, 9) if cflag else raw
        ulen2 = len(raw)
    elif name == 'main':
        blob2 = zlib.compress(main_raw, 9) if cflag else main_raw
        ulen2 = len(main_raw); cflag2 = cflag
    else:
        blob2, ulen2, cflag2 = blob, ulen, cflag
    toc_entries.append((len(out), len(blob2), ulen2, cflag2, tc, name))
    out += blob2
toc_off2 = len(out)
ser = b''
for o, cl, ul, cf, tc, name in toc_entries:
    nb = name.encode() 
    nl = len(nb) + 1
    el = 18 + nl
    if el % 16:
        nl += 16 - el % 16
    ser += struct.pack('!IIIIBc%ds' % nl, 18 + nl, o, cl, ul, cf, tc.encode(), nb)
out += ser
total = len(out) + struct.calcsize(COOKIE_FMT)
out += struct.pack(COOKIE_FMT, MAGIC, total, toc_off2, len(ser), pyver, pylib)
open(OUT, 'wb').write(boot + bytes(out))
print("wrote", OUT, len(boot) + len(out), "bytes")
