#!/bin/bash
# Simulates benign background activity (Math operations and harmless file I/O)
echo "[Ground Truth] Benign workload started (PID: $$)"

mkdir -p /tmp/os_benign_tasks
while true; do
    # Harmless CPU tick
    for i in {1..10000}; do
        let "x = $i * $i"
    done
    
    # Harmless disk touch
    touch /tmp/os_benign_tasks/tick.txt
    
    sleep 1.5
done