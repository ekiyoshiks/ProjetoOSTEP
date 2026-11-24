# Projeto 2 - Custo (Sistemas Operacionais, Mackenzie, 2026.2)

**Pergunta:** quanto o aumento da memória consumida por um processo degrada a latência de outro
processo que acessa repetidamente um conjunto de dados?

Máquina de medição: Samsung Galaxy Book4, Intel Core i5-1335U, 16 GB de RAM, Windows.
Sensores: HWiNFO (1 amostra por segundo). Todos os dados foram medidos pelo grupo.

## Estrutura

| Pasta ou arquivo | Conteúdo |
|---|---|
| `relatorio/` | PDF do relatório |
| `programas/` | `vitima.c`, `ocupador.c`, `agressor.c` e `rodar_ram.bat` (código-fonte), mais as séries de latência da vítima gravadas nas execuções de energia (`energia_controle.csv`, `custo_exp_baixa.csv`, `custo_exp_media.csv`, `custo_exp_alta.csv`) |
| `resultados/saida/` | 21 séries da frente de RAM: `ram_<ocupação %>_<repetição>.csv` (saída do `vitima`) |
| `resultados/controle/` e `resultados/experimental/` | Logs do HWiNFO. Temperatura: `temp_control` e `temp_exp_*` (10/11). Energia: `custo_controle` e `custo_exp_*` (19/11) |
| `dashboard.html` | Dashboard feito a partir dos CSVs (abra no navegador) |
| `analise/analise.py` | Recalcula as tabelas e os gráficos do relatório direto dos CSVs |
| `analise/saida/` | Resultado do `analise.py` (tabelas `.csv`, gráficos `.png`, `resumo.txt`) |

## Como as medições foram feitas

- **Latência:** `rodar_ram.bat` roda `ocupador.exe <pct>` (ocupa pct% da RAM física e fica ocioso) e
  `vitima.exe 156 30 saida\ram_<pct>_<rep>.csv <pct>` (156 MB, 30 s). Níveis 0, 25, 50, 75, 90, 100 e
  110%, com 3 repetições cada. A vítima faz pointer chasing em um ciclo aleatório (Sattolo) e grava
  os ns por acesso de cada lote de 5 milhões de acessos, depois de 2 lotes de aquecimento descartados.
- **Temperatura e energia:** HWiNFO gravando em CSV enquanto rodavam `agressor.exe` e `vitima.exe`
  (execuções experimentais baixa, média e alta) ou sem o agressor (controle). Colunas usadas:
  `CPU Package [°C]`, `CPU Package Power [W]`, `Total CPU Usage [%]`, `Physical Memory Load [%]`,
  `Page File Used [MB]`. Energia = integral trapezoidal da potência (E = ∫P·dt). As execuções
  `custo_*` (19/11) gravam também a latência da vítima.

## Reproduzir as tabelas e gráficos

```
pip install matplotlib
python3 analise/analise.py
```
