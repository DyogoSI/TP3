"""Híbrido: heurística (warm start) -> fix-and-optimize por vizinhança espacial -> B&B completo
com o melhor incumbente como limite primal.

Vizinhança (decisão de projeto): sorteia-se uma cidade-centro e toma-se as `m` cidades mais
próximas (conjunto S). Ficam LIVRES as arestas x_ij com i ou j em S cujo outro extremo está em
S, entre os K vizinhos mais próximos da cidade de S, ou que pertençam à rota incumbente. Todas
as demais arestas ficam FIXADAS no valor da rota atual. O tamanho m é adaptativo: cresce se o
sub-MIP é provado ótimo sem melhora, diminui se estoura o tempo do sub-MIP."""
import random
import time

import numpy as np

from exato import ModeloMTZ
from heuristica import heuristica

K_VIZ = 8


def fix_and_optimize(modelo, rota, custo, t_fim, rng, m0=6, sub_t=3.0):
    d, n = modelo.d, modelo.n
    viz = [set(sorted(range(n), key=lambda j: d[i][j])[:K_VIZ + 1]) for i in range(n)]
    m, iters = min(m0, n), 0
    while time.time() < t_fim:
        centro = rng.randrange(n)
        S = set(sorted(range(n), key=lambda j: d[centro][j])[:m])
        tour = {rota[k]: rota[(k + 1) % n] for k in range(n)}
        livre = np.zeros(modelo.nx, bool)
        for i in range(n):
            for j in range(n):
                if i == j or (i not in S and j not in S):
                    continue
                if tour[i] == j or (i in S and j in S) or (i in S and j in viz[i]) or (j in S and i in viz[j]):
                    livre[modelo.ix(i, j)] = True
        modelo.fixar(rota, livre)
        modelo.warm_start(rota)
        r, c, _, provado, _ = modelo.resolver(min(sub_t, t_fim - time.time()))
        modelo.liberar_tudo()
        iters += 1
        if r is not None and c < custo - 1e-6:
            rota, custo = r, int(round(c))
        elif provado:
            m = min(m + 2, n)
        else:
            m = max(m - 2, 4)
    return rota, custo, iters


def hibrido(d, budget, usar_fo=True, frac_fo=0.4, seed=0):
    """Retorna dict com custo, limite dual, provado, tempo e iterações de fix-and-optimize."""
    t0 = time.time()
    rota, custo, _ = heuristica(d)
    modelo = ModeloMTZ(d)
    iters = 0
    if usar_fo:
        t_fim = time.time() + frac_fo * (budget - (time.time() - t0))
        rota, custo, iters = fix_and_optimize(modelo, rota, custo, t_fim, random.Random(seed))
    modelo.warm_start(rota)  # incumbente inicial do B&B completo
    r, c, lb, provado, _ = modelo.resolver(budget - (time.time() - t0))
    if r is not None and c < custo:
        rota, custo = r, int(round(c))
    return {"custo": custo, "lb": lb, "provado": provado, "tempo": time.time() - t0,
            "iters_fo": iters, "rota": rota}
