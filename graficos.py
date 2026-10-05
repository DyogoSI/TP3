"""Gráficos comparativos a partir de resultados.csv."""
import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROT = {"heuristica": "Heurística pura", "exato": "Exato puro (MTZ/HiGHS)",
       "warm_start": "Exato + warm start", "hibrido_FO": "Híbrido (warm start + fix-and-optimize)"}
COR = {"heuristica": "#2a9d8f", "exato": "#c1121f", "warm_start": "#e9a23b", "hibrido_FO": "#1d4e89"}

linhas = list(csv.DictReader(open("resultados.csv")))
Ns = sorted({int(r["N"]) for r in linhas})


def serie(metodo, campo):
    d = {int(r["N"]): r[campo] for r in linhas if r["metodo"] == metodo}
    return [float(d[n]) if d[n] not in ("", None) else float("nan") for n in Ns]


fig, ax = plt.subplots(1, 3, figsize=(17, 4.8))
for m in ROT:
    ax[0].plot(Ns, serie(m, "gap_pct"), "o-", label=ROT[m], color=COR[m])
    ax[1].plot(Ns, serie(m, "custo"), "o-", label=ROT[m], color=COR[m])
    ax[2].plot(Ns, serie(m, "tempo"), "o-", label=ROT[m], color=COR[m])
ax[0].set_ylabel("Gap vs. melhor limite inferior (%)")
ax[1].set_ylabel("Custo da melhor solução")
ax[2].set_ylabel("Tempo até o fim (s)")
ax[2].set_yscale("log")
for a in ax:
    a.set_xlabel("N (cidades)")
    a.grid(alpha=.3)
ax[0].legend(fontsize=8)
fig.suptitle("TSP-MTZ: heurística x exato x híbrido, mesmo orçamento de tempo por N")
fig.tight_layout()
fig.savefig("comparativo.png", dpi=150)
print("ok")
