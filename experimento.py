"""Roda as 4 abordagens para cada N sob o mesmo orçamento de tempo e grava resultados.csv.

    python experimento.py --tempo 60
"""
import argparse
import csv
import time
from multiprocessing import Pool

from exato import ModeloMTZ
from gerador import TAMANHOS, gerar_instancia, semente_de
from heuristica import heuristica
from hibrido import hibrido

CAMPOS = ["N", "semente", "metodo", "custo", "lb", "gap_pct", "provado", "tempo", "iters_fo"]


def rodar_tamanho(args):
    n, budget = args
    _, d = gerar_instancia(n)
    base = dict(N=n, semente=semente_de(n), iters_fo=0)
    out = []
    _, c, t = heuristica(d)
    out.append(dict(base, metodo="heuristica", custo=c, lb=None, provado=False, tempo=t))
    _, c, lb, prov, t = ModeloMTZ(d).resolver(budget)
    out.append(dict(base, metodo="exato", custo=c, lb=lb, provado=prov, tempo=t))
    for nome, fo in (("warm_start", False), ("hibrido_FO", True)):
        h = hibrido(d, budget, usar_fo=fo)
        out.append(dict(base, metodo=nome, custo=h["custo"], lb=h["lb"], provado=h["provado"],
                        tempo=h["tempo"], iters_fo=h["iters_fo"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tempo", type=float, default=60)
    ap.add_argument("--procs", type=int, default=3)
    ap.add_argument("--tamanhos", type=int, nargs="*", default=TAMANHOS)
    ap.add_argument("--saida", default="resultados.csv")
    a = ap.parse_args()
    t0 = time.time()
    with Pool(a.procs) as p:
        res = [r for lst in p.map(rodar_tamanho, [(n, a.tempo) for n in a.tamanhos], chunksize=1) for r in lst]
    # melhor limite inferior conhecido por N (dá gap também à heurística)
    melhor_lb = {}
    for r in res:
        if r["lb"] is not None and r["lb"] > -1e20:
            melhor_lb[r["N"]] = max(melhor_lb.get(r["N"], 0), r["lb"])
    for r in res:
        lb = melhor_lb.get(r["N"])
        r["gap_pct"] = max(0.0, 100 * (r["custo"] - lb) / r["custo"]) if r["custo"] and lb else None
    with open(a.saida, "w", newline="") as f:
        w = csv.DictWriter(f, CAMPOS)
        w.writeheader()
        for r in res:
            w.writerow({k: (round(r[k], 3) if isinstance(r[k], float) else r[k]) for k in CAMPOS})
    print(f"{'N':>3}{'metodo':>12}{'custo':>8}{'gap%':>8}{'prov':>6}{'t(s)':>8}{'itFO':>6}")
    for r in res:
        g = f"{r['gap_pct']:.2f}" if r["gap_pct"] is not None else "-"
        print(f"{r['N']:>3}{r['metodo']:>12}{r['custo']:>8.0f}{g:>8}{str(r['provado']):>6}{r['tempo']:>8.1f}{r['iters_fo']:>6}")
    print(f"total {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
