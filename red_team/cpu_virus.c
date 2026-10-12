#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/wait.h>

void consume_cpu() {
    volatile unsigned long counter = 0;
    for (int i = 0; i < 50000000; i++) { counter += (i * 3) ^ 0x5A5A; }
}

int main(int argc, char *argv[]) {
    int gen = 1;
    if (argc == 3 && strcmp(argv[1], "--gen") == 0) { gen = atoi(argv[2]); }

    printf("[CPU Red Team] Launched. Generation: %d\n", gen);

    // Generation 3: Behavioral Camouflage (Process Renaming & Daemonizing)
    if (gen == 3) {
        // Disguise the process name in top/ps telemetry
        prctl(PR_SET_NAME, "kworker/u4:2", 0, 0, 0); 
        
        pid_t pid = fork();
        if (pid > 0) {
            printf("[CPU Gen 3] Forked child PID %d. Parent exiting to orphan child.\n", pid);
            exit(0); // Parent dies, child is inherited by system init (orphaned)
        }
        // Child continues execution disguised as a kernel worker
    }

    time_t start_time = time(NULL);
    while (time(NULL) - start_time < 350) { // 350 second attack window
        consume_cpu();
        
        // Generation 2 & 3: Timing Evasion (Pulse execution)
        if (gen >= 2) { usleep(100000); } // 100ms sleep drops average CPU% in top
    }
    return 0;
}