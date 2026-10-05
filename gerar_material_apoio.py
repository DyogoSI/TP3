"""Gera material_de_apoio_tp3.docx (explicação do código do TP-III para o grupo)."""
import csv

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

NAVY, MUTED = RGBColor(0x0B, 0x2A, 0x3B), RGBColor(0x5B, 0x6B, 0x76)
res = {(int(r["N"]), r["metodo"]): r for r in csv.DictReader(open("resultados.csv"))}
Ns = sorted({k[0] for k in res})

doc = Document()
for sec in doc.sections:
    sec.left_margin = sec.right_margin = Pt(64)
    sec.top_margin = sec.bottom_margin = Pt(56)
st = doc.styles["Normal"]
st.font.name, st.font.size = "Calibri", Pt(11)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
st.paragraph_format.space_after = Pt(6)
for nome, tam in (("Title", 24), ("Heading 1", 15), ("Heading 2", 12.5)):
    s = doc.styles[nome]
    s.font.name, s.font.size, s.font.bold, s.font.color.rgb = "Cambria", Pt(tam), True, NAVY
    s.element.rPr.rFonts.set(qn("w:ascii"), "Cambria")
    s.element.rPr.rFonts.set(qn("w:hAnsi"), "Cambria")
cod = doc.styles.add_style("Codigo", WD_STYLE_TYPE.PARAGRAPH)
cod.font.name, cod.font.size = "Consolas", Pt(9)
cod.element.rPr.rFonts.set(qn("w:ascii"), "Consolas")
cod.element.rPr.rFonts.set(qn("w:hAnsi"), "Consolas")
cod.paragraph_format.space_after = Pt(0)
cod.paragraph_format.left_indent = Pt(8)


def shade(el_pr, fill):
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), fill)
    el_pr.append(sh)


def P(texto, bold_ate=None):
    """Parágrafo. `bold_ate`: trecho inicial em negrito (ex.: nome de função)."""
    p = doc.add_paragraph()
    if bold_ate and texto.startswith(bold_ate):
        p.add_run(bold_ate).bold = True
        p.add_run(texto[len(bold_ate):])
    else:
        p.add_run(texto)
    return p


def B(texto, bold_ate=None):
    p = doc.add_paragraph(style="List Bullet")
    if bold_ate and texto.startswith(bold_ate):
        p.add_run(bold_ate).bold = True
        p.add_run(texto[len(bold_ate):])
    else:
        p.add_run(texto)
    p.paragraph_format.space_after = Pt(2)


num = doc.styles.add_style("Num", WD_STYLE_TYPE.PARAGRAPH)
num.base_style = doc.styles["Normal"]
num.paragraph_format.left_indent, num.paragraph_format.first_line_indent = Pt(22), Pt(-16)
num.paragraph_format.space_after = Pt(2)


def N(texto):
    """Item numerado; a contagem reinicia em 1 quando o parágrafo anterior não é item."""
    k = int(doc.paragraphs[-1].text.split(".")[0]) + 1 if doc.paragraphs[-1].style.name == "Num" else 1
    doc.add_paragraph(f"{k}.	{texto}", style="Num")


def code(texto):
    linhas = texto.strip("\n").split("\n")
    for i, l in enumerate(linhas):
        p = doc.add_paragraph(l or " ", style="Codigo")
        shade(p._p.get_or_add_pPr(), "F4F7F9")
        if i == len(linhas) - 1:
            p.paragraph_format.space_after = Pt(8)


def tabela(cab, linhas, larguras=None):
    t = doc.add_table(rows=1, cols=len(cab))
    t.style = "Table Grid"
    for c, h in zip(t.rows[0].cells, cab):
        c.text = h
        shade(c._tc.get_or_add_tcPr(), "0B2A3B")
        r = c.paragraphs[0].runs[0]
        r.font.bold, r.font.color.rgb, r.font.size = True, RGBColor(255, 255, 255), Pt(10)
    for k, l in enumerate(linhas):
        cells = t.add_row().cells
        for c, v in zip(cells, l):
            c.text = str(v)
            c.paragraphs[0].runs[0].font.size = Pt(10)
            if k % 2:
                shade(c._tc.get_or_add_tcPr(), "F4F7F9")
    if larguras:
        for row in t.rows:
            for c, w in zip(row.cells, larguras):
                c.width = Pt(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


H1 = lambda t: doc.add_heading(t, 1)
H2 = lambda t: doc.add_heading(t, 2)

doc.add_paragraph("Material de apoio: entendendo o código do TP-III", style="Title")
P("Este material explica o código do trabalho de um jeito simples, para todo mundo do grupo conseguir responder "
  "qualquer pergunta sobre ele. O TP-III reaproveita o problema do TP-II (TSP com a formulação MTZ) e acrescenta "
  "uma heurística e a combinação dela com o método exato. Todo o código está na pasta tp3/.")

H1("1. Visão geral")
P("A pasta tem sete arquivos de código, mais os arquivos gerados:")
tabela(["Arquivo", "Para que serve"], [
    ["gerador.py", "Cria as instâncias: N cidades sorteadas, com semente documentada, e a tabela de distâncias."],
    ["heuristica.py", "A heurística do TP-I adaptada: vizinho mais próximo + 2-opt + Or-opt."],
    ["exato.py", "O modelo MTZ do TP-II, montado direto no HiGHS. Aceita warm start, fixação de variáveis e informa o limite dual."],
    ["hibrido.py", "Warm start e fix-and-optimize: a parte nova do trabalho."],
    ["experimento.py", "Roda as 4 abordagens para cada N com o mesmo tempo e grava resultados.csv."],
    ["graficos.py e relatorio.py", "Geram comparativo.png e o relatório em PDF a partir do resultados.csv."],
    ["montar_slides.py e gerar_roteiro_docx.py", "Geram os slides (com o roteiro nas notas) e o roteiro em Word."],
], [150, 330])
P("O caminho que o programa faz para cada tamanho N é este:")
N("O gerador cria as N cidades e a tabela de distâncias (gerador.py).")
N("A heurística pura roda sozinha e devolve rota, custo e tempo (heuristica.py).")
N("O exato puro monta o modelo MTZ e resolve com limite de tempo, sem ajuda (exato.py).")
N("O warm start dá a rota da heurística ao solver como solução inicial e resolve (hibrido.py com usar_fo=False).")
N("O híbrido faz warm start, depois o fix-and-optimize, depois o B&B completo (hibrido.py com usar_fo=True).")
N("O experimento junta tudo, calcula o gap e grava resultados.csv (experimento.py).")

H1("2. Como rodar")
P("Instale o Python e as bibliotecas:")
code("python -m pip install -r requirements.txt")
P("Teste rápido, de uns 40 segundos:")
code("python experimento.py --tempo 15 --tamanhos 10 20 30 --saida teste.csv")
P("Rodada completa (uns 6 minutos), depois gráficos e PDF. Cada comando em uma linha separada:")
code("python experimento.py --tempo 120 --procs 6\npython graficos.py\npython relatorio.py")
P("As opções do experimento são --tempo (orçamento em segundos por abordagem), --procs (quantos tamanhos rodam em "
  "paralelo), --tamanhos (lista de N) e --saida (nome do CSV). Os slides saem com python montar_slides.py.")

H1("3. O gerador de instâncias (gerador.py)")
B("gerar_instancia(n) sorteia n pontos uniformes no quadrado [0, 1000] x [0, 1000].")
B("A semente é 2026 + N. Assim a instância de cada tamanho é sempre a mesma e qualquer pessoa reproduz o resultado.")
B("A distância é int(hypot + 0.5), a mesma regra EUC_2D da TSPLIB, arredondada para inteiro, como no TP-II.")
B("TAMANHOS = [10, 20, 30, 40, 60, 80]. O 10 resolve quase na hora; no 80 o exato claramente não fecha o gap.")
P("Por que sementes fixas? Para comparar as abordagens na mesma instância e para o professor poder refazer.")

H1("4. A heurística (heuristica.py)")
B("vizinho_mais_proximo(d, inicio): parte de uma cidade e vai sempre para a cidade não visitada mais próxima.", "vizinho_mais_proximo(d, inicio):")
B("dois_opt(rota, d): troca duas arestas por outras duas, invertendo o trecho do meio, sempre que isso diminui o custo.", "dois_opt(rota, d):")
B("or_opt(rota, d): tira um segmento de 1 a 3 cidades e o reinsere na melhor posição, nas duas orientações.", "or_opt(rota, d):")
B("busca_local: repete 2-opt e Or-opt até nenhum dos dois melhorar a rota.", "busca_local:")
B("heuristica(d, max_starts=20): roda a construção + busca local a partir de até 20 cidades iniciais e fica com a melhor "
  "rota. No final a rota é girada para começar na cidade 0, como o modelo espera.", "heuristica(d, max_starts=20):")
P("Ela leva menos de 2 segundos até N=80. Não prova nada sobre otimalidade: só devolve uma boa rota.")

H1("5. O modelo exato (exato.py)")
P("É o mesmo modelo MTZ do TP-II, mas montado direto no HiGHS (biblioteca highspy) em vez de usar o PuLP. "
  "Fizemos assim porque o PuLP não deixa passar uma solução inicial, mudar os limites das variáveis rapidamente "
  "nem ler o limite dual. O HiGHS puro faz as três coisas.")
H2("Como as variáveis são numeradas")
code("""
ix(i, j) = i * (n - 1) + (j se j < i, senão j - 1)    # posição da variável x[i, j]
iu(i)    = n * (n - 1) + i - 1                        # posição da variável u[i]
""")
P("O modelo tem n(n-1) variáveis x (binárias) e n-1 variáveis u (contínuas, com limites 1 e n-1), "
  "ou seja n² − 1 variáveis, igual ao TP-II. As restrições também são as mesmas: 2n de grau (uma saída e uma "
  "entrada por cidade) e (n-1)(n-2) de MTZ.")
H2("Configuração do solver")
B("threads = 1: cada execução usa um núcleo, para a comparação ser justa.")
B("mip_rel_gap = 0: só para quando provar o ótimo ou acabar o tempo.")
B("random_seed = 0 e output_flag = False (sem log).")
H2("Os métodos da classe ModeloMTZ")
B("warm_start(rota): converte a rota em valores de x (1 nas arestas usadas) e de u (a posição de cada cidade) e entrega "
  "ao HiGHS com setSolution. É o incumbente inicial (limite primal).", "warm_start(rota):")
B("fixar(rota, livres): para cada aresta que não está em livres, trava o limite inferior e o superior no valor que ela tem na "
  "rota. O solver só enxerga as arestas livres.", "fixar(rota, livres):")
B("liberar_tudo(): devolve os limites originais (0 e 1) depois de um sub-problema.", "liberar_tudo():")
B("resolver(tempo): roda o HiGHS com o limite de tempo e devolve (rota, custo, limite_dual, provado, tempo). "
  "provado é verdadeiro se o status for ótimo.", "resolver(tempo):")
B("rota_de(col): lê as variáveis x que ficaram em 1 e reconstrói a rota partindo da cidade 0.", "rota_de(col):")

H1("6. O híbrido (hibrido.py): a parte mais importante")
P("Esta é a parte que vocês devem saber explicar. A função hibrido(d, budget, usar_fo) faz três fases dentro do mesmo "
  "orçamento de tempo:")
N("Warm start: roda a heurística e entrega a rota ao HiGHS como incumbente.")
N("Fix-and-optimize (só se usar_fo=True): gasta 40% do orçamento melhorando a rota por vizinhanças pequenas.")
N("B&B completo: roda o modelo inteiro com o melhor incumbente até o tempo acabar. É essa fase que dá o limite dual e o gap.")
P("Com usar_fo=False a fase 2 é pulada. É o que chamamos de “warm start” nos resultados, para separar o efeito do "
  "warm start do efeito do fix-and-optimize.")
H2("Como funciona uma iteração do fix-and-optimize")
N("Sorteia uma cidade-centro e pega as m cidades mais próximas dela. Esse grupo é o conjunto S.")
N("Marca como livres as arestas que tocam S e ligam: a outra cidade de S, um dos 8 vizinhos mais próximos da cidade de S "
  "(K_VIZ = 8), ou que já estão na rota atual.")
N("Fixa todas as outras arestas no valor da rota atual (fixar). Sobra um problema pequeno.")
N("Entrega a rota atual como warm start e resolve esse sub-problema com limite de 3 s.")
N("Se achou um custo menor, adota a nova rota. Restaura os limites (liberar_tudo) e repete.")
H2("O tamanho m da vizinhança é adaptativo")
B("Começa em 6.")
B("Se o sub-problema é resolvido até o ótimo sem melhorar a rota, m sobe 2 (a vizinhança estava pequena demais).")
B("Se estoura os 3 s, m cai 2, com mínimo de 4 (estava grande demais).")
P("A decisão de projeto é a vizinhança espacial: no TSP euclidiano as trocas úteis acontecem entre cidades próximas, "
  "então liberar o que está perto faz mais sentido do que sortear arestas ao acaso.")

H1("7. O experimento (experimento.py)")
B("rodar_tamanho(n, budget) roda as quatro abordagens em uma instância e devolve quatro linhas de resultado.", "rodar_tamanho(n, budget)")
B("Os tamanhos rodam em paralelo (Pool), cada um em um processo. Cada HiGHS usa 1 thread, então não disputam núcleo.")
B("O gap é (custo − melhor limite inferior conhecido) / custo. O limite inferior de cada N é o maior limite dual obtido "
  "entre as abordagens. A heurística não tem limite próprio, então usa esse. Valores negativos por arredondamento viram 0.")
B("A saída é o resultados.csv, com N, semente, método, custo, limite inferior, gap, se provou o ótimo, tempo e "
  "número de iterações do fix-and-optimize.")

H1("8. Resultados que vocês precisam saber de cabeça")
P("Orçamento de 120 s por abordagem. Variáveis = n² − 1; restrições = 2n + (n−1)(n−2). Cada célula mostra custo e tempo; "
  "“ótimo” significa que o solver provou a otimalidade.")
linhas = []
for n in Ns:
    def cel(m):
        r = res[(n, m)]
        if r["provado"] == "True":
            return f"{float(r['custo']):.0f} (ótimo, {float(r['tempo']):.1f} s)".replace(".", ",")
        g = float(r["gap_pct"]) if r["gap_pct"] else 0
        return f"{float(r['custo']):.0f} (gap {g:.1f}%)".replace(".", ",")
    linhas.append([n, n * n - 1, 2 * n + (n - 1) * (n - 2), cel("heuristica"), cel("exato"), cel("warm_start"), cel("hibrido_FO")])
tabela(["N", "Vars", "Restr", "Heurística", "Exato puro", "Warm start", "Híbrido"], linhas, [24, 38, 38, 100, 100, 100, 100])
P("As conclusões, em uma frase cada:")
B("O exato fecha o gap até N=40 (no limite do tempo) e deixa de fechar em N=60.")
B("O híbrido não consegue fechar o gap em N=60 e 80, mas termina com solução muito melhor que o exato puro.")
B("Até N=60 a heurística pura já iguala o híbrido; só em N=80 o híbrido é 0,6% melhor (6906 contra 6949).")
B("O warm start acelera a prova (N=40: 17 s contra 60 s). O fix-and-optimize quase não ajudou, e consumiu 40% do tempo.")

H1("9. Erros que já apareceram (e como resolver)")
B("OSError: [Errno 22] Invalid argument: 'comparativo.png': o Windows trava o arquivo enquanto a imagem está aberta num "
  "visualizador. Feche a janela e rode python graficos.py de novo.", "OSError: [Errno 22] Invalid argument: 'comparativo.png':")
B("argument --procs: invalid int value: '6python': dois comandos foram colados na mesma linha. Rode um por linha.",
  "argument --procs: invalid int value: '6python':")
B("cd : Não é possível localizar o caminho '...\\tp3\\tp3': o terminal já estava dentro da pasta tp3; não precisa do cd tp3.",
  "cd : Não é possível localizar o caminho '...\\tp3\\tp3':")
B("ModuleNotFoundError (highspy, numpy, matplotlib, reportlab, pptx, docx): rode python -m pip install -r requirements.txt "
  "(para os slides e o Word: pip install python-pptx python-docx).", "ModuleNotFoundError (highspy, numpy, matplotlib, reportlab, pptx, docx):")
B("O experimento parece travado: é normal. Com --tempo 120 cada abordagem pode usar os 120 s, e o resultado só aparece no fim.")
B("Os tempos mudam um pouco entre execuções ou máquinas: o B&B tem variação. O que não muda é a tendência.")

H1("10. Perguntas que podem cair sobre o código")
P("Por que usar o HiGHS direto e não o PuLP como no TP-II? O PuLP não deixa dar solução inicial, mudar limites de variáveis "
  "e ler o limite dual com facilidade. O modelo matemático é exatamente o mesmo.", "Por que usar o HiGHS direto e não o PuLP como no TP-II?")
P("O que é warm start? É dar ao solver uma solução viável logo na largada. Ela vira o limite primal (a melhor solução conhecida), "
  "e o branch-and-bound já pode descartar tudo que for pior.", "O que é warm start?")
P("O que é fix-and-optimize? Pega uma solução conhecida, fixa a maior parte das variáveis e deixa o exato resolver só uma "
  "vizinhança pequena. Repete trocando quais variáveis ficam livres.", "O que é fix-and-optimize?")
P("Qual a diferença para o relax-and-fix? No relax-and-fix resolve-se a relaxação linear e fixam-se as variáveis "
  "“mais confiantes”. Aqui partimos de uma solução inteira (a da heurística), então escolhemos o fix-and-optimize.",
  "Qual a diferença para o relax-and-fix?")
P("Por que a vizinhança é espacial? No TSP euclidiano, melhorar uma rota quase sempre envolve cidades próximas umas das outras.",
  "Por que a vizinhança é espacial?")
P("Por que o híbrido demora 50 s mesmo em N=10? Porque o fix-and-optimize usa 40% do orçamento, mesmo que a heurística já tenha "
  "achado o ótimo. Ele não sabe que já está no ótimo; só o B&B completo prova isso.",
  "Por que o híbrido demora 50 s mesmo em N=10?")
P("Por que a heurística não tem gap próprio? Ela não calcula limite inferior. Usamos o melhor limite dual obtido pelas outras abordagens.",
  "Por que a heurística não tem gap próprio?")
P("O limite dual melhorou com o híbrido? Pouco. O MTZ tem relaxação fraca, então o limite inferior sobe devagar em qualquer "
  "abordagem. Por isso nenhuma fecha o gap em N=60 e 80.", "O limite dual melhorou com o híbrido?")
P("Os resultados são definitivos? Não. Usamos uma instância por N e uma execução por abordagem, com 6 processos em paralelo "
  "na mesma máquina. Os tempos do B&B variam entre execuções.", "Os resultados são definitivos?")
P("O que mudaria para a heurística não ser tão forte? Uma heurística inicial mais fraca (só vizinho mais próximo, por exemplo) "
  "deixaria mais espaço para o fix-and-optimize melhorar a rota.", "O que mudaria para a heurística não ser tão forte?")

doc.save("material_de_apoio_tp3.docx")
print("ok")
