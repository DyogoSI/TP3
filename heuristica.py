"""Heurística do TP-I adaptada ao TSP: vizinho mais próximo + busca local (2-opt e Or-opt),
com múltiplas partidas (uma por cidade inicial, até `max_starts`)."""
import time

from gerador import custo_rota


def vizinho_mais_proximo(d, inicio):
    n = len(d)
    rota, vis = [inicio], [False] * n
    vis[inicio] = True
    while len(rota) < n:
        a = rota[-1]
        b = min((j for j in range(n) if not vis[j]), key=lambda j: d[a][j])
        rota.append(b)
        vis[b] = True
    return rota


def dois_opt(rota, d):
    n, melhorou = len(rota), True
    while melhorou:
        melhorou = False
        for i in range(n - 1):
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue
                a, b, c, e = rota[i], rota[i + 1], rota[j], rota[(j + 1) % n]
                if d[a][c] + d[b][e] < d[a][b] + d[c][e]:
                    rota[i + 1:j + 1] = reversed(rota[i + 1:j + 1])
                    melhorou = True
    return rota


def or_opt(rota, d):
    """Move segmentos de 1 a 3 cidades para a melhor posição (uma passada)."""
    n, melhorou = len(rota), False
    for seg in (1, 2, 3):
        for i in range(n):
            s = [rota[(i + k) % n] for k in range(seg)]
            ant, pos = rota[(i - 1) % n], rota[(i + seg) % n]
            ganho = d[ant][s[0]] + d[s[-1]][pos] - d[ant][pos]
            resto = [c for c in rota if c not in s]
            melhor, mpos = 0, None
            for p in range(len(resto)):
                u, v = resto[p], resto[(p + 1) % len(resto)]
                for orient in (s, s[::-1]):
                    delta = d[u][orient[0]] + d[orient[-1]][v] - d[u][v]
                    if ganho - delta > melhor:
                        melhor, mpos = ganho - delta, (p, orient)
            if mpos:
                p, orient = mpos
                rota[:] = resto[:p + 1] + orient + resto[p + 1:]
                melhorou = True
    return rota, melhorou


def busca_local(rota, d):
    while True:
        rota = dois_opt(rota, d)
        rota, mel = or_opt(rota, d)
        if not mel:
            return rota


def heuristica(d, max_starts=20):
    """Retorna (melhor rota começando em 0, custo, tempo)."""
    t0, n = time.time(), len(d)
    melhor, cmelhor = None, float("inf")
    for inicio in range(min(n, max_starts)):
        r = busca_local(vizinho_mais_proximo(d, inicio), d)
        c = custo_rota(r, d)
        if c < cmelhor:
            melhor, cmelhor = r[:], c
    k = melhor.index(0)
    return melhor[k:] + melhor[:k], cmelhor, time.time() - t0
