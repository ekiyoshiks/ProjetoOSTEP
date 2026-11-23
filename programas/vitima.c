/* VITIMA - dataset fixo, acessos encadeados aleatorios (pointer chasing).
 * Uso:  vitima.exe <MB> <duracao_s> <serie.csv> [rotulo]
 * Ex.:  vitima.exe 156 900 vitima_controle_1.csv          (frente temperatura)
 *       vitima.exe 156 30 saida\ram_75_1.csv 75           (frente RAM)
 * Grava em <serie.csv>: tempo_s;ns_por_acesso (uma linha por lote de 5 milhoes de acessos).
 * Se informar [rotulo], anexa mediana/min/max em resumo.csv.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

#ifdef _WIN32
#include <windows.h>
static double agora_s(void) {
    static LARGE_INTEGER f;
    LARGE_INTEGER c;
    if (!f.QuadPart) QueryPerformanceFrequency(&f);
    QueryPerformanceCounter(&c);
    return (double)c.QuadPart / (double)f.QuadPart;
}
#else
#include <time.h>
static double agora_s(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}
#endif

#define OPERACOES 5000000ULL   /* acessos por lote */
#define MAX_LOTES 200000

static uint64_t estado = 88172645463325252ULL;
static uint64_t rnd(void) {            /* xorshift64 */
    estado ^= estado << 13;
    estado ^= estado >> 7;
    estado ^= estado << 17;
    return estado;
}

static int cmp(const void *a, const void *b) {
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

int main(int argc, char **argv) {
    if (argc < 4) {
        printf("Uso: %s <MB> <duracao_s> <serie.csv> [rotulo]\n", argv[0]);
        return 1;
    }
    size_t mb = (size_t)atoi(argv[1]);
    double duracao = atof(argv[2]);
    const char *saida = argv[3];
    const char *rotulo = (argc > 4) ? argv[4] : NULL;

    size_t n = mb * 1024ULL * 1024ULL / sizeof(uint32_t);
    uint32_t *prox = (uint32_t *)malloc(n * sizeof(uint32_t));
    double *lat = (double *)malloc(MAX_LOTES * sizeof(double));
    if (!prox || !lat) { printf("Erro ao reservar memoria.\n"); return 1; }

    /* Algoritmo de Sattolo: gera UM unico ciclo aleatorio passando por todas as posicoes */
    for (size_t i = 0; i < n; i++) prox[i] = (uint32_t)i;
    for (size_t i = n - 1; i > 0; i--) {
        size_t j = (size_t)(rnd() % i);
        uint32_t t = prox[i]; prox[i] = prox[j]; prox[j] = t;
    }

    FILE *f = fopen(saida, "w");
    if (!f) { printf("Erro ao criar %s\n", saida); return 1; }
    fprintf(f, "tempo_s;ns_por_acesso\n");

    volatile uint32_t sink;            /* impede o compilador de apagar o laco */
    uint32_t idx = 0;

    for (int w = 0; w < 2; w++) {      /* aquecimento: 2 lotes nao registrados */
        for (unsigned long long i = 0; i < OPERACOES; i++) idx = prox[idx];
        sink = idx;
    }

    printf("Vitima: %zu MB | %.0f s | saida %s\n", mb, duracao, saida);
    double inicio = agora_s();
    int lotes = 0;
    for (;;) {
        double t0 = agora_s();
        if (t0 - inicio >= duracao || lotes >= MAX_LOTES) break;
        for (unsigned long long i = 0; i < OPERACOES; i++) idx = prox[idx];
        sink = idx;
        double t1 = agora_s();
        double ns = (t1 - t0) * 1e9 / (double)OPERACOES;
        lat[lotes++] = ns;
        fprintf(f, "%.3f;%.3f\n", t1 - inicio, ns);
        fflush(f);
        printf("t=%.1f s | %.2f ns/acesso\n", t1 - inicio, ns);
    }
    fclose(f);

    if (lotes > 0) {
        double *c = (double *)malloc(lotes * sizeof(double));
        for (int i = 0; i < lotes; i++) c[i] = lat[i];
        qsort(c, lotes, sizeof(double), cmp);
        double med = (lotes % 2) ? c[lotes / 2] : (c[lotes / 2 - 1] + c[lotes / 2]) / 2.0;
        printf("RESUMO: %d lotes | mediana %.2f | min %.2f | max %.2f ns/acesso\n",
               lotes, med, c[0], c[lotes - 1]);
        if (rotulo) {
            FILE *r = fopen("resumo.csv", "a");
            if (r) {
                fprintf(r, "%s;%s;%.2f;%.2f;%.2f\n", rotulo, saida, med, c[0], c[lotes - 1]);
                fclose(r);
            }
        }
        free(c);
    }
    free(prox); free(lat);
    return 0;
}
