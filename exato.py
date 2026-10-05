"""Modelo MTZ do TP-II resolvido diretamente com o HiGHS (highspy), com suporte a
warm start (incumbente), fixação de variáveis e leitura do limite dual (gap)."""
import time

import highspy
import numpy as np


class ModeloMTZ:
    def __init__(self, d):
        self.d, self.n = d, len(d)
        n = self.n
        self.nx = n * (n - 1)
        self.ncol = self.nx + n - 1
        self.h = h = highspy.Highs()
        h.setOptionValue("output_flag", False)
        h.setOptionValue("threads", 1)
        h.setOptionValue("mip_rel_gap", 0.0)
        h.setOptionValue("random_seed", 0)

        lp = highspy.HighsLp()
        lp.num_col_ = self.ncol
        cost = np.zeros(self.ncol)
        lb, ub = np.zeros(self.ncol), np.ones(self.ncol)
        for i in range(n):
            for j in range(n):
                if i != j:
                    cost[self.ix(i, j)] = d[i][j]
        lb[self.nx:], ub[self.nx:] = 1, n - 1
        lp.col_cost_, lp.col_lower_, lp.col_upper_ = cost, lb, ub

        inf = highspy.kHighsInf
        rows, rl, ru = [], [], []
        for i in range(n):  # uma saída e uma entrada por cidade
            rows.append([(self.ix(i, j), 1.0) for j in range(n) if j != i]); rl.append(1); ru.append(1)
            rows.append([(self.ix(j, i), 1.0) for j in range(n) if j != i]); rl.append(1); ru.append(1)
        for i in range(1, n):  # MTZ
            for j in range(1, n):
                if i != j:
                    rows.append([(self.iu(i), 1.0), (self.iu(j), -1.0), (self.ix(i, j), float(n))])
                    rl.append(-inf); ru.append(n - 1)
        start, idx, val = [0], [], []
        for r in rows:
            for c, v in r:
                idx.append(c); val.append(v)
            start.append(len(idx))
        lp.num_row_ = len(rows)
        lp.row_lower_, lp.row_upper_ = np.array(rl, float), np.array(ru, float)
        lp.a_matrix_.format_ = highspy.MatrixFormat.kRowwise
        lp.a_matrix_.start_ = np.array(start, dtype=np.int32)
        lp.a_matrix_.index_ = np.array(idx, dtype=np.int32)
        lp.a_matrix_.value_ = np.array(val, dtype=float)
        lp.integrality_ = [highspy.HighsVarType.kInteger] * self.nx + [highspy.HighsVarType.kContinuous] * (n - 1)
        h.passModel(lp)
        self.lb0, self.ub0 = lb.copy(), ub.copy()
        self.todas = np.arange(self.ncol, dtype=np.int32)

    def ix(self, i, j):
        return i * (self.n - 1) + (j if j < i else j - 1)

    def iu(self, i):
        return self.nx + i - 1

    def vetor_rota(self, rota):
        v = np.zeros(self.ncol)
        for k, a in enumerate(rota):
            v[self.ix(a, rota[(k + 1) % self.n])] = 1
            if a != 0:
                v[self.iu(a)] = k
        return v

    def rota_de(self, col):
        prox = {i: j for i in range(self.n) for j in range(self.n)
                if i != j and col[self.ix(i, j)] > 0.5}
        rota, a = [0], prox[0]
        while a != 0 and len(rota) <= self.n:
            rota.append(a)
            a = prox[a]
        return rota if len(rota) == self.n else None

    def warm_start(self, rota):
        sol = highspy.HighsSolution()
        sol.col_value = list(self.vetor_rota(rota))
        self.h.setSolution(sol)

    def fixar(self, rota, livres):
        """Fixa as arestas x fora de `livres` (máscara booleana) no valor da rota dada."""
        lb, ub = self.lb0.copy(), self.ub0.copy()
        base = self.vetor_rota(rota)
        fixas = ~livres
        lb[:self.nx][fixas] = base[:self.nx][fixas]
        ub[:self.nx][fixas] = base[:self.nx][fixas]
        self.h.changeColsBounds(self.ncol, self.todas, lb, ub)

    def liberar_tudo(self):
        self.h.changeColsBounds(self.ncol, self.todas, self.lb0, self.ub0)

    def resolver(self, tempo):
        """Retorna (rota|None, custo|None, limite_dual, provado_otimo, tempo)."""
        self.h.setOptionValue("time_limit", float(max(tempo, 0.05)))
        t0 = time.time()
        self.h.run()
        dt = time.time() - t0
        info = self.h.getInfo()
        provado = self.h.getModelStatus() == highspy.HighsModelStatus.kOptimal
        rota = custo = None
        if info.primal_solution_status == 2:
            rota = self.rota_de(list(self.h.getSolution().col_value))
            if rota is not None:
                custo = info.objective_function_value
        return rota, custo, info.mip_dual_bound, provado, dt
