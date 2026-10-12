#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/prctl.h>

#define MAX_CHUNKS 40 // 400MB total

int main(int argc, char *argv[]) {
    int gen = 1;
    if (argc == 3 && strcmp(argv[1], "--gen") == 0) { gen = atoi(argv[2]); }

    if (gen == 3) {
        prctl(PR_SET_NAME, "systemd-journal", 0, 0, 0); // Camouflage
    }

    void *chunks[MAX_CHUNKS];
    int allocated = 0;

    for (int i = 0; i < MAX_CHUNKS; i++) {
        chunks[i] = malloc(10 * 1024 * 1024); // 10MB chunks
        if (chunks[i]) {
            memset(chunks[i], 0xA5, 10 * 1024 * 1024); // Force physical RAM allocation
            allocated += 10;
        }

        // Mutation Logic
        if (gen == 1) {
            usleep(10000); // Fast allocation
        } else {
            // Gen 2 & 3: Slow, fragmented allocation to evade rate-of-change detection
            usleep(400000); 
        }
    }

    sleep(350); // Hold memory to give Blue Team time to detect and respond

    for (int i = 0; i < MAX_CHUNKS; i++) {
        if (chunks[i]) free(chunks[i]);
    }
    return 0;
}