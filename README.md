# TP-III — Heurística + método exato (TSP / MTZ)

Mesmo problema do TP-II (TSP, formulação MTZ, HiGHS 1.15.1, 1 thread). Orçamento: **120 s por abordagem e por N**.

## Arquivos
| Arquivo | Função |
|---|---|
| `gerador.py` | Gerador por N: pontos uniformes em [0,1000]², distância EUC_2D inteira, **semente = 2026 + N** |
| `heuristica.py` | Heurística do TP-I adaptada: vizinho mais próximo (20 partidas) + 2-opt + Or-opt |
| `exato.py` | Modelo MTZ no HiGHS (`highspy`), com warm start, fixação de variáveis e limite dual |
| `hibrido.py` | Warm start e fix-and-optimize |
| `experimento.py` | Roda as 4 abordagens por N → `resultados.csv` |
| `graficos.py` | Gera `comparativo.png` |

Rodar: `pip install highspy numpy matplotlib` → `python experimento.py --tempo 120` → `python graficos.py`.

## Instâncias (N, semente)
(10, 2036) · (20, 2046) · (30, 2056) · (40, 2066) · (60, 2086) · (80, 2106)

## Abordagens (mesmo orçamento)
1. **Heurística pura**: NN + 2-opt + Or-opt (termina em < 2 s).
2. **Exato puro**: MTZ completo, sem incumbente.
3. **Warm start**: a rota da heurística entra como incumbente (`setSolution`) no B&B completo.
4. **Híbrido (warm start + fix-and-optimize)**: warm start, depois 40% do orçamento em fix-and-optimize, depois B&B completo com o melhor incumbente.

**Fix-and-optimize (decisão de projeto):** sorteia-se uma cidade-centro e as *m* cidades mais próximas formam o conjunto S. Ficam livres as arestas que tocam S e ligam a S, aos 8 vizinhos mais próximos ou à rota atual. Todo o resto é fixado na rota incumbente. O *m* é adaptativo (começa em 6; +2 se o sub-MIP fecha sem melhora; −2 se estoura 3 s). A vizinhança é espacial porque no TSP euclidiano as trocas úteis acontecem entre cidades próximas.

## Resultados (120 s)
| N | Heurística | Exato puro | Warm start | Híbrido |
|---|---|---|---|---|
| 10 | 3014 | 3014 ótimo (0,4 s) | 3014 ótimo (0,5 s) | 3014 ótimo |
| 20 | 4233 | 4233 ótimo (2,8 s) | 4233 ótimo (4,9 s) | 4233 ótimo |
| 30 | 4764 | 4764 ótimo (35 s) | 4764 ótimo (19 s) | 4764 ótimo |
| 40 | 5193 | 5193 ótimo (60 s) | 5193 ótimo (17 s) | 5193 ótimo |
| 60 | 5863 (gap 1,8%) | 6549 (gap 12,1%) | 5863 (1,8%) | 5863 (1,8%) |
| 80 | 6949 (6,9%) | 9089 (28,9%) | 6949 (6,9%) | **6906** (6,4%) |

Gap = (custo − melhor limite inferior conhecido para esse N) / custo. A heurística não tem limite próprio e usa o melhor limite dual obtido entre as abordagens. Veja `resultados.csv` e `comparativo.png`.

## Respostas
1. **Onde o exato deixa de fechar o gap?** Entre N=40 (fechou em ~60 s, no limite do orçamento) e N=60 (gap de 12% após 120 s). Em N=30 já leva 35 s e em N=20 leva 3 s. O tempo cresce de forma exponencial, como no TP-II.
2. **O híbrido empurra o limite?** Em *fechar o gap*, não: com N=60 e N=80, nenhuma abordagem provou o ótimo. O limite dual do MTZ é fraco e o incumbente não o melhora. O ganho é em **qualidade da solução**: em N=60 o exato puro termina com 12% de gap e o híbrido com 1,8%. Em N=80 a diferença é de 28,9% para 6,4%. O warm start também acelera a prova de otimalidade onde ela ainda é possível: N=40 fecha em 17 s contra 60 s do exato puro, e N=30 fecha em 19 s contra 35 s.
3. **A heurística pura iguala o híbrido?** Em N ≤ 60 ela já acha a mesma solução que o híbrido, em menos de 1 s. Nessa faixa o ganho de combinar só aparece como *prova* de otimalidade, até N=40. Em N=80 o híbrido encontrou 6906 contra 6949 (0,6% melhor), o único ponto em que o fix-and-optimize melhorou o incumbente.
4. **A estratégia acelerou o solver?** O **warm start** acelerou (N=30 e N=40 fecham de 1,8× a 3,5× mais rápido; no N=20 foi mais lento, 4,9 s contra 2,8 s, dentro da variação esperada do B&B). O **fix-and-optimize**, na nossa implementação, **quase não fez diferença**: com N ≤ 40 a heurística já era ótima, então ele só gastou 40% do orçamento (os híbridos terminam em 48–70 s em vez de ~1 s). Na prática, 40% do tempo foi gasto sem ganho. Só em N=80 ele melhorou algo. Nossa leitura: uma heurística 2-opt + Or-opt com 20 partidas já é muito forte em instâncias euclidianas deste tamanho, e o sub-MIP MTZ também é limitado pela relaxação fraca. Um fix-and-optimize mais útil exigiria vizinhanças maiores ou uma heurística mais fraca como ponto de partida.

## Limitações
- Uma instância (semente) por N, uma execução por abordagem; os tempos do B&B variam entre execuções.
- 6 processos rodaram em paralelo na mesma máquina, cada um com HiGHS em 1 thread.
- O gap da heurística usa limite dual de outra abordagem.
