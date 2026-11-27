import sys, os; sys.path.insert(0, 'tools')
from kcej import extract
G = r"C:\Users\ahmed\OneDrive\Desktop\Yu-Gi-Oh!\Yu-Gi-Oh!\Joey The Passion"
for a, o in [('data.dat', 'extracted/data'), ('Voice.dat', 'extracted/voice')]:
    bad = extract(os.path.join(G, a), o)
    print(a, 'short outputs:', len(bad), bad[:5])
