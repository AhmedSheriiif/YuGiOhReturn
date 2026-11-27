"""KCEJYUGI archive reader for Yu-Gi-Oh! Power of Chaos (data.dat / Voice.dat)."""
import struct, sys

def swap(b): return bytes(((x << 4) | (x >> 4)) & 0xFF for x in b)

def read_index(path):
    with open(path, 'rb') as f:
        magic = f.read(8); assert magic == b'KCEJYUGI', magic
        n, = struct.unpack('<I', f.read(4))
        out = []
        for i in range(n):
            raw = f.read(0x10C)
            name = swap(raw[:0x100].split(b'\0')[0]).decode('latin1')
            off, usize, csize = struct.unpack('<III', raw[0x100:])
            out.append((name, off, usize, csize))
    return out

if __name__ == '__main__':
    for e in read_index(sys.argv[1]):
        print('%-60s off=%08x u=%9d c=%9d' % e)

def lzss_decompress(src, usize, fill=0):
    N, F, TH = 4096, 18, 2
    ring = bytearray([fill]) * N; r = N - F
    out = bytearray(); i = 0; flags = 0
    while len(out) < usize and i < len(src):
        flags >>= 1
        if not flags & 0x100:
            flags = src[i] | 0xFF00; i += 1
            if i >= len(src): break
        if flags & 1:
            c = src[i]; i += 1
            out.append(c); ring[r] = c; r = (r + 1) & (N - 1)
        else:
            if i + 1 >= len(src): break
            lo, hi = src[i], src[i+1]; i += 2
            pos = lo | ((hi & 0xF0) << 4); ln = (hi & 0x0F) + TH + 1
            for k in range(ln):
                c = ring[(pos + k) & (N - 1)]
                out.append(c); ring[r] = c; r = (r + 1) & (N - 1)
    return bytes(out[:usize])

def extract(path, outdir, fill=0):
    import os
    f = open(path, 'rb'); bad = []
    for name, off, u, c in read_index(path):
        f.seek(off); raw = f.read(c)
        data = raw if u == c else lzss_decompress(raw, u, fill)
        if len(data) != u: bad.append((name, len(data), u))
        p = os.path.join(outdir, *name.replace('bin#', 'bin').split(chr(92)))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'wb').write(data)
    return bad
