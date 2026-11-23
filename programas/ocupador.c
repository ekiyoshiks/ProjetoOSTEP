/* OCUPADOR - processo OCIOSO que ocupa X% da RAM fisica (frente RAM).
 * Uso: ocupador.exe <percentual>      Ex.: ocupador.exe 75
 * Escreve em toda a memoria (dados aleatorios, para o Windows nao comprimir),
 * cria o arquivo pronto.flag e depois fica dormindo ate ser encerrado (Ctrl+C).
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

#ifdef _WIN32
#include <windows.h>
static unsigned long long ram_total(void) {
    MEMORYSTATUSEX m;
    m.dwLength = sizeof(m);
    GlobalMemoryStatusEx(&m);
    return m.ullTotalPhys;
}
static void dormir(void) { Sleep(1000); }
#else
#include <unistd.h>
static unsigned long long ram_total(void) {
    return (unsigned long long)sysconf(_SC_PHYS_PAGES) * (unsigned long long)sysconf(_SC_PAGE_SIZE);
}
static void dormir(void) { sleep(1); }
#endif

int main(int argc, char **argv) {
    if (argc < 2) { printf("Uso: %s <percentual>\n", argv[0]); return 1; }
    double pct = atof(argv[1]);
    unsigned long long total = ram_total();
    unsigned long long alvo = (unsigned long long)((double)total * pct / 100.0);
    const size_t PEDACO = 256ULL * 1024 * 1024;
    uint64_t s = 0x9E3779B97F4A7C15ULL;
    unsigned long long feito = 0;

    printf("RAM total: %.2f GiB | alvo: %.1f%% = %.2f GiB\n",
           total / 1073741824.0, pct, alvo / 1073741824.0);

    while (feito < alvo) {
        size_t n = (alvo - feito > PEDACO) ? PEDACO : (size_t)(alvo - feito);
        uint64_t *p = (uint64_t *)malloc(n);   /* nunca liberado: o processo segura a RAM */
        if (!p) { printf("Falha ao alocar apos %.2f GiB.\n", feito / 1073741824.0); break; }
        for (size_t i = 0; i < n / 8; i++) {   /* escreve tudo com dados pseudoaleatorios */
            s ^= s << 13; s ^= s >> 7; s ^= s << 17;
            p[i] = s;
        }
        feito += n;
    }
    printf("Ocupados %.2f GiB (%.1f%% da RAM).\n", feito / 1073741824.0,
           100.0 * (double)feito / (double)total);

    FILE *f = fopen("pronto.flag", "w");
    if (f) { fprintf(f, "ok\n"); fclose(f); }

    printf("Ocioso. Ctrl+C para liberar.\n");
    for (;;) dormir();
    return 0;
}
