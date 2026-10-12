CC = gcc
CFLAGS = -Wall -Wextra -O2

TARGETS = cpu_virus mem_virus io_virus

all: $(TARGETS)

cpu_virus: cpu_virus.c
	$(CC) $(CFLAGS) -o cpu_virus cpu_virus.c

mem_virus: mem_virus.c
	$(CC) $(CFLAGS) -o mem_virus mem_virus.c

io_virus: io_virus.c
	$(CC) $(CFLAGS) -o io_virus io_virus.c

clean:
	rm -f $(TARGETS)
	rm -rf /tmp/os_arena