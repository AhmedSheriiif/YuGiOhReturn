import sys; sys.path.insert(0, 'tools')
from kcej import read_index
P = r"C:\Users\ahmed\OneDrive\Desktop\Yu-Gi-Oh!\Yu-Gi-Oh!\Joey The Passion\data.dat"
idx = {e[0]: e for e in read_index(P)}
f = open(P, 'rb')
for n in sys.argv[1:]:
    name, off, u, c = idx[n]; f.seek(off); b = f.read(min(c, 96))
    print(n, u, c); print(b.hex(' ')); print(repr(b)); print()
