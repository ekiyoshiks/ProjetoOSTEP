"""analise.py - recalcula as tabelas e os graficos do relatorio a partir dos CSVs medidos.

Uso (a partir da raiz do repositorio):
    python3 analise/analise.py

Le:   resultados/saida/ram_<pct>_<rep>.csv                  (vitima.exe, ';' como separador)
      programas/{energia_controle,custo_exp_baixa,custo_exp_media,custo_exp_alta}.csv
                                                                (vitima.exe durante as execucoes de custo)
      resultados/{controle,experimental}/*.CSV                  (HWiNFO, ',' como separador)
Gera: analise/saida/tabela_latencia.csv, tabela_termica.csv, resumo.txt,
      fig_latencia.png, fig_termica.png
Nenhum numero e digitado a mao: tudo vem dos arquivos medidos.
"""
import csv
import statistics as st
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "analise" / "saida"
SAIDA.mkdir(parents=True, exist_ok=True)
NIVEIS = [0, 25, 50, 75, 90, 100, 110]
# series da vitima gravadas durante as execucoes de custo (energia), em programas/
ARQ_CUSTO = {"controle": "energia_controle.csv", "baixa": "custo_exp_baixa.csv",
             "media": "custo_exp_media.csv", "alta": "custo_exp_alta.csv"}
REPS = [1, 2, 3]

# colunas do HWiNFO (0-based, conferidas pelo cabecalho dos CSVs)
COL_HORA, COL_MEM, COL_PF, COL_CPU, COL_TEMP, COL_POT = 1, 7, 10, 65, 115, 165


def serie_latencia(caminho):
    linhas = caminho.read_text().splitlines()[1:]
    return [float(l.split(";")[1]) for l in linhas if ";" in l]


def segundos(hora):
    h, m, s = hora.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def log_termico(caminho):
    with open(caminho, encoding="latin-1") as f:
        linhas = [r for r in list(csv.reader(f))[1:] if len(r) > COL_POT and r[0][:1].isdigit()]
    t = [segundos(r[COL_HORA]) for r in linhas]
    temp = [float(r[COL_TEMP]) for r in linhas]
    pot = [float(r[COL_POT]) for r in linhas]
    cpu = [float(r[COL_CPU]) for r in linhas]
    mem = [float(r[COL_MEM]) for r in linhas]
    pf = [float(r[COL_PF]) for r in linhas]
    dur = t[-1] - t[0]
    en = sum((pot[i] + pot[i - 1]) / 2 * (t[i] - t[i - 1]) for i in range(1, len(t)))  # integral trapezoidal de P dt
    return {
        "inicio": linhas[0][COL_HORA], "dur_min": dur / 60, "n": len(linhas),
        "temp_media": st.mean(temp), "temp_max": max(temp), "temp_ini": st.median(temp[:30]),
        "pot_media": en / dur, "energia_J": en,
        "cpu_media": st.mean(cpu), "mem_max": max(mem), "pf_mb": st.median(pf),
    }


# ---------------- latencia (frente RAM) ----------------
tab_lat, medianas_todas, pts = [], [], {}
for p in NIVEIS:
    meds = []
    for r in REPS:
        v = serie_latencia(RAIZ / "resultados" / "saida" / f"ram_{p}_{r}.csv")
        meds.append(st.median(v))
        medianas_todas.append(st.median(v))
    pts[p] = meds
    tab_lat.append({"ocupacao_pct": p, "rep1": round(meds[0], 2), "rep2": round(meds[1], 2),
                    "rep3": round(meds[2], 2), "media_das_medianas": round(st.mean(meds), 2),
                    "var_vs_0pct_pct": None})
base = st.mean(pts[0])
for linha, p in zip(tab_lat, NIVEIS):
    linha["var_vs_0pct_pct"] = round((st.mean(pts[p]) / base - 1) * 100, 2)
with open(SAIDA / "tabela_latencia.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(tab_lat[0])); w.writeheader(); w.writerows(tab_lat)

# ---------------- temperatura / energia ----------------
arquivos = [
    ("Temp. controle", "controle/temp_control.CSV"),
    ("Temp. baixa", "experimental/temp_exp_baixa.CSV"),
    ("Temp. media", "experimental/temp_exp_media.CSV"),
    ("Temp. alta", "experimental/temp_exp_alta.CSV"),
    ("Custo controle", "controle/custo_controle.CSV"),
    ("Custo baixa", "experimental/custo_exp_baixa.CSV"),
    ("Custo media", "experimental/custo_exp_media.CSV"),
    ("Custo alta", "experimental/custo_exp_alta.CSV"),
]
tab_term = []
for nome, rel in arquivos:
    d = log_termico(RAIZ / "resultados" / rel)
    d["execucao"] = nome
    tab_term.append(d)

# latencia da vitima durante as execucoes de custo
lat_custo = {}
for k in ("controle", "baixa", "media", "alta"):
    v = serie_latencia(RAIZ / "programas" / ARQ_CUSTO[k])
    lat_custo[k] = (st.mean(v), st.median(v), len(v))
with open(SAIDA / "tabela_latencia_custo.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["execucao", "n", "media_ns", "mediana_ns"])
    for k, (m, md, n) in lat_custo.items():
        w.writerow([k, n, round(m, 2), round(md, 2)])
campos = ["execucao", "inicio", "dur_min", "temp_ini", "temp_media", "temp_max", "pot_media",
          "energia_J", "cpu_media", "mem_max", "pf_mb"]
with open(SAIDA / "tabela_termica.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(campos)
    for d in tab_term:
        w.writerow([d[c] if c in ("execucao", "inicio") else round(d[c], 2) for c in campos])

# ---------------- resumo em texto ----------------
t_ctl, t_exp = tab_term[0], tab_term[1:4]
c_ctl, c_exp = tab_term[4], tab_term[5:8]
with open(SAIDA / "resumo.txt", "w") as f:
    f.write(f"latencia: medianas de {len(medianas_todas)} execucoes entre "
            f"{min(medianas_todas):.2f} e {max(medianas_todas):.2f} ns "
            f"(amplitude {max(medianas_todas) - min(medianas_todas):.2f} ns)\n")
    f.write(f"latencia 110% vs 0%: {st.mean(pts[110]) - base:+.2f} ns "
            f"({(st.mean(pts[110]) / base - 1) * 100:+.2f}%)\n")
    f.write(f"temperatura media: controle {t_ctl['temp_media']:.1f} C | "
            f"experimentais {[round(d['temp_media'], 1) for d in t_exp]} | "
            f"media exp {st.mean(d['temp_media'] for d in t_exp):.1f} C\n")
    pm = st.mean(d['pot_media'] for d in c_exp)
    f.write(f"potencia media (custo): controle {c_ctl['pot_media']:.2f} W | "
            f"agressor {[round(d['pot_media'], 2) for d in c_exp]} | media {pm:.2f} W "
            f"({(pm / c_ctl['pot_media'] - 1) * 100:+.0f}%)\n")
    f.write("latencia da vitima no custo (media, ns): " +
            ", ".join(f"{k} {m:.1f}" for k, (m, md, n) in lat_custo.items()) + "\n")
    f.write("temperatura inicial (mediana dos 30 s iniciais): " +
            str([(d['execucao'], d['temp_ini']) for d in tab_term]) + "\n")
print(open(SAIDA / "resumo.txt").read())

# ---------------- graficos ----------------
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
fig, (ax, az) = plt.subplots(1, 2, figsize=(6.4, 3.2), dpi=200, gridspec_kw={"width_ratios": [1, 1]})
xs = list(range(len(NIVEIS)))
for a_, lim, tit in ((ax, (0, 200), "Escala completa (começa em 0)"), (az, (155, 157.5), "Zoom em 155 a 157,5 ns")):
    for i, p in enumerate(NIVEIS):
        a_.scatter([i] * 3, pts[p], color="#7a8694", s=16, zorder=2,
                   label="repetição (mediana)" if i == 0 else None)
    a_.plot(xs, [st.mean(pts[p]) for p in NIVEIS], color="#1f5fa8", marker="o", ms=3.5, lw=1.5, zorder=3,
            label="média das 3" if a_ is ax else None)
    a_.set_xticks(xs); a_.set_xticklabels([f"{p}%" for p in NIVEIS], fontsize=7)
    a_.set_ylim(*lim); a_.set_title(tit, fontsize=8.5)
    a_.set_xlabel("RAM ocupada pelo outro processo", fontsize=8)
ax.set_ylabel("Latência da vítima (ns/acesso)")
ax.legend(frameon=False, loc="lower right", fontsize=7)
fig.tight_layout(); fig.savefig(SAIDA / "fig_latencia.png"); plt.close(fig)

def barras(sel, rot, titulo, arq):
    fig, axs = plt.subplots(1, 2, figsize=(6.4, 3.0), dpi=200)
    cores = ["#9aa5b1"] + ["#d9822b"] * (len(sel) - 1)
    for a, key, lab in zip(axs, ["temp_media", "pot_media"],
                           ["Temperatura média CPU Package (°C)", "Potência média do pacote (W)"]):
        a.bar(rot, [d[key] for d in sel], color=cores); a.set_ylabel(lab, fontsize=8)
        a.tick_params(axis="x", labelsize=8)
        for i, d in enumerate(sel):
            a.text(i, d[key], f"{d[key]:.1f}", ha="center", va="bottom", fontsize=8)
    fig.suptitle(titulo, fontsize=10)
    fig.tight_layout(); fig.savefig(SAIDA / arq); plt.close(fig)

rot = ["Controle", "Baixa", "Média", "Alta"]
barras(tab_term[0:4], rot, "Temperatura: agressor + vítima contra controle (10/11)", "fig_termica.png")
barras(tab_term[4:8], rot, "Energia: agressor + vítima contra controle (19/11)", "fig_energia.png")
