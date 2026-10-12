#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string.h>
#include <sys/prctl.h>

int main(int argc, char *argv[]) {
    int gen = 1;
    if (argc == 3 && strcmp(argv[1], "--gen") == 0) { gen = atoi(argv[2]); }

    if (gen == 3) { prctl(PR_SET_NAME, "rsyslogd", 0, 0, 0); }

    char buffer[4096];
    memset(buffer, 'X', sizeof(buffer));
    
    mkdir("/tmp/os_arena", 0700);

    // Create the actual "persistence payload" quietly
    int payload_fd = open("/tmp/os_arena/hidden_cron.sh", O_WRONLY | O_CREAT, 0700);
    write(payload_fd, "#!/bin/bash\necho 'payload'", 26);
    close(payload_fd);

    // Generate I/O noise to mask the payload creation
    for (int i = 0; i < 20; i++) {
        char filepath[256];
        snprintf(filepath, sizeof(filepath), "/tmp/os_arena/noise_%d.log", i);
        
        int fd = open(filepath, O_WRONLY | O_CREAT | O_TRUNC, 0600);
        if (fd >= 0) {
            for (int j = 0; j < 200; j++) { write(fd, buffer, sizeof(buffer)); }
            close(fd);
        }
        
        if (gen >= 2) { usleep(150000); } // Pulsed I/O to evade simple bandwidth thresholds
    }

    sleep(350);
    system("rm -rf /tmp/os_arena/*"); // Cleanup
    return 0;
}