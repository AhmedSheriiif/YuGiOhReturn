"""Convert .yga (KCE LZSS-compressed 32-bit image) to PNG."""
import struct, sys, os; sys.path.insert(0, os.path.dirname(__file__))
from kcej import lzss_decompress
from PIL import Image

def load_yga(path):
    b = open(path, 'rb').read(); assert b[:4] == b'yga\0'
    w, h, flag, usize, csize = struct.unpack_from('<5I', b, 4)
    px = lzss_decompress(b[24:24+csize], usize) if flag else b[24:24+usize]
    return w, h, px

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]; ok = bad = 0
    for root, _, files in os.walk(src):
        for f in files:
            if not f.endswith('.yga'): continue
            p = os.path.join(root, f)
            try:
                w, h, px = load_yga(p)
                bpp = len(px) // (w * h)
                mode = {4: 'RGBA', 3: 'RGB'}[bpp]
                img = Image.frombytes(mode, (w, h), px)
                if mode == 'RGBA':  # stored BGRA
                    b_, g, r, a = img.split(); img = Image.merge('RGBA', (r, g, b_, a))
                out = os.path.join(dst, os.path.relpath(p, src))[:-4] + '.png'
                os.makedirs(os.path.dirname(out), exist_ok=True); img.save(out); ok += 1
            except Exception as e:
                bad += 1; print('FAIL', p, e)
    print('converted', ok, 'failed', bad)
