/* AGRESSOR - processo ATIVO: reserva memoria e le/escreve nela sem parar (frente temperatura).
 * Uso: agressor.exe [MB]     (padrao 256)       Ctrl+C para encerrar.
 */
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    size_t mb = (argc > 1) ? (size_t)atoi(argv[1]) : 256;
    size_t bytes = mb * 1024ULL * 1024ULL;
    volatile unsigned char *mem = (volatile unsigned char *)malloc(bytes);
    if (!mem) { printf("Erro ao reservar memoria.\n"); return 1; }

    for (size_t i = 0; i < bytes; i += 4096) mem[i] = (unsigned char)(i % 256);

    printf("Agressor iniciado: %zu MB. Ctrl+C para encerrar.\n", mb);
    for (;;) {
        for (size_t i = 0; i < bytes; i += 64) mem[i]++;
    }
    return 0;
}
