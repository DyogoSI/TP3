"""Gera relatorio_tp3.pdf (tabelas, gráfico e respostas) a partir de resultados.csv e comparativo.png."""
import csv

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ss = getSampleStyleSheet()
corpo = ParagraphStyle("c", parent=ss["BodyText"], fontSize=10, leading=14, spaceAfter=6)
h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontSize=15, spaceBefore=10)
h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=12, spaceBefore=8)
peq = ParagraphStyle("p", parent=corpo, fontSize=8.5, leading=11, textColor=colors.HexColor("#444444"))

NOMES = {"heuristica": "Heurística", "exato": "Exato puro", "warm_start": "Warm start",
         "hibrido_FO": "Híbrido (WS+F&O)"}
rows = list(csv.DictReader(open("resultados.csv")))
Ns = sorted({int(r["N"]) for r in rows})
sem = {int(r["N"]): r["semente"] for r in rows}


def tabela(dados, larguras, destaque=None):
    t = Table(dados, colWidths=larguras, repeatRows=1)
    est = [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4e89")),
           ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTSIZE", (0, 0), (-1, -1), 8.5),
           ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbbbbb")), ("ALIGN", (1, 0), (-1, -1), "CENTER"),
           ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f5f9")])]
    return t if t.setStyle(TableStyle(est + (destaque or []))) is None else t


def cel(r):
    c = f"{float(r['custo']):.0f}"
    g = f"{float(r['gap_pct']):.1f}%" if r["gap_pct"] else "-"
    return Paragraph(f"<b>{c}</b>{' (ótimo)' if r['provado'] == 'True' else ''}<br/>gap {g} · {float(r['tempo']):.1f}s",
                     ParagraphStyle("t", parent=peq, alignment=1, fontSize=8, leading=10))


hist = [["N", "Semente"] + [NOMES[m] for m in NOMES]]
for n in Ns:
    hist.append([n, sem[n]] + [cel(next(r for r in rows if int(r["N"]) == n and r["metodo"] == m)) for m in NOMES])

doc = SimpleDocTemplate("relatorio_tp3.pdf", pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                        topMargin=1.6 * cm, bottomMargin=1.6 * cm,
                        title="TP-III: Heurística + Método Exato (TSP/MTZ)")
P = lambda t, s=corpo: Paragraph(t, s)
f = [P("TP-III · Heurística + Método Exato", ss["Title"]),
     P("Problema do Caixeiro Viajante (formulação MTZ) · Cauã Fortes, Dyogo Henrique e Maycon Luiz", peq),
     P("1. Objetivo e configuração", h1),
     P("Combinamos a heurística do TP-I (vizinho mais próximo + 2-opt + Or-opt) com o modelo MTZ do TP-II, "
       "resolvido pelo HiGHS 1.15.1 (1 thread). Para cada N rodamos quatro abordagens com o mesmo orçamento de "
       "<b>120 s</b>: heurística pura, exato puro, exato com warm start (a rota da heurística como incumbente) e "
       "híbrido (warm start + fix-and-optimize + B&amp;B completo)."),
     P("<b>Instâncias.</b> Gerador parametrizado por N: pontos uniformes em [0,1000]², distância EUC_2D inteira, "
       "semente = 2026 + N. Tamanhos e sementes: " + "; ".join(f"N={n} (semente {sem[n]})" for n in Ns) + "."),
     P("<b>Fix-and-optimize.</b> Sorteia-se uma cidade-centro e as <i>m</i> cidades mais próximas formam o conjunto S. "
       "Ficam livres as arestas que tocam S e ligam a S, aos 8 vizinhos mais próximos ou à rota atual; todo o "
       "resto é fixado na rota incumbente. O <i>m</i> é adaptativo (começa em 6; +2 se o sub-MIP fecha sem "
       "melhora; −2 se estoura 3 s). O método usa 40% do orçamento e o restante vai para o B&amp;B completo com o "
       "melhor incumbente."),
     P("2. Resultados", h1),
     tabela(hist, [1.5 * cm, 1.4 * cm] + [3.6 * cm] * 4),
     P("Cada célula traz custo, gap e tempo. O gap é (custo − melhor limite inferior conhecido para o N) / custo; "
       "o limite inferior vem do melhor limite dual entre as abordagens (a heurística não tem limite próprio). "
       "Uma instância e uma execução por N.", peq),
     Image("comparativo.png", width=17.2 * cm, height=17.2 * cm * 720 / 2550),
     P("Figura 1. Gap, custo e tempo por N, com o mesmo orçamento de tempo para as quatro abordagens.", peq),
     P("3. Respostas às perguntas", h1),
     P("<b>A partir de que tamanho o exato deixa de fechar o gap?</b> Entre N=40 e N=60. Em N=40 o exato puro prova "
       "o ótimo em ~60 s, no limite do orçamento. Em N=60 termina com gap de 12,1% e em N=80 com 28,9%. O tempo "
       "cresce de forma exponencial (N=20: 2,8 s; N=30: 35 s), como já vimos no TP-II."),
     P("<b>O híbrido empurra esse limite? Em quanto?</b> Em fechar o gap, não: em N=60 e N=80 nenhuma abordagem "
       "provou o ótimo, porque o limite dual do MTZ é fraco e o incumbente não o melhora. O ganho é na qualidade da "
       "solução: em N=60 o gap cai de 12,1% (exato puro) para 1,8%, e em N=80 de 28,9% para 6,4%. O warm start "
       "também acelera a prova de otimalidade onde ela ainda é possível (N=40: 17 s contra 60 s)."),
     P("<b>A heurística pura já é tão boa quanto o híbrido?</b> Até N=60 sim: ela chega à mesma solução em menos "
       "de 1 s, e o ganho de combinar se resume a provar a otimalidade (possível só até N=40). Em N=80 o híbrido "
       "foi 0,6% melhor (6906 contra 6949), o único ponto onde o fix-and-optimize melhorou o incumbente."),
     P("<b>A estratégia escolhida acelerou o solver?</b> O <i>warm start</i> acelerou (N=30: 19 s contra 35 s; "
       "N=40: 17 s contra 60 s; em N=20 foi mais lento, 4,9 s contra 2,8 s, o que cabe na variação normal do "
       "B&amp;B). O <i>fix-and-optimize</i> quase não fez diferença: até N=40 a heurística já era ótima, então "
       "ele só consumiu 40% do orçamento (os híbridos terminam em 48–70 s, contra ~1 s da heurística). "
       "Na nossa leitura, uma heurística 2-opt + Or-opt com 20 partidas já é muito forte em instâncias euclidianas "
       "deste tamanho, e o sub-MIP em MTZ também sofre com a relaxação fraca. Um fix-and-optimize mais útil "
       "pediria vizinhanças maiores ou uma heurística inicial mais fraca."),
     P("4. Limitações", h1),
     P("Uma semente por N e uma execução por abordagem, então os tempos do B&amp;B variam entre execuções. "
       "Os 6 tamanhos rodaram em paralelo (6 processos) na mesma máquina, cada um com o HiGHS em 1 thread. "
       "O gap da heurística usa o limite dual obtido por outra abordagem. "
       "Código: <font face='Courier'>gerador.py, heuristica.py, exato.py, hibrido.py, experimento.py, graficos.py</font>.")]
doc.build(f)
print("ok")
