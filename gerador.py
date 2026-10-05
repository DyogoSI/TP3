"""Gerador parametrizado de instâncias TSP euclidianas (EUC_2D, distâncias inteiras).

N cidades sorteadas uniformemente em [0, 1000]^2 com semente documentada:
    semente = SEMENTE_BASE + N        (SEMENTE_BASE = 2026)
Distância = int(hypot + 0.5), a mesma convenção EUC_2D da TSPLIB usada no TP-II.
"""
import math
import random

SEMENTE_BASE = 2026
LADO = 1000
TAMANHOS = [10, 20, 30, 40, 60, 80]


def semente_de(n):
    return SEMENTE_BASE + n


def gerar_instancia(n, semente=None):
    rng = random.Random(semente_de(n) if semente is None else semente)
    coords = [(rng.uniform(0, LADO), rng.uniform(0, LADO)) for _ in range(n)]
    d = [[0 if i == j else int(math.hypot(coords[i][0] - coords[j][0],
                                          coords[i][1] - coords[j][1]) + 0.5)
          for j in range(n)] for i in range(n)]
    return coords, d


def custo_rota(rota, d):
    return sum(d[rota[k]][rota[(k + 1) % len(rota)]] for k in range(len(rota)))
