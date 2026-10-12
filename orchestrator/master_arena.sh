#!/bin/bash

# Configuration
VENV_PATH="/home/bwajid/ai-agent-env/bin/activate"
RESULTS_CSV="experiment_results.csv"
TIMEOUT_SEC=300  # System Death / Evasion Threshold

# Initialize Metrics CSV
echo "Virus_Type,Generation,Trial,MTTD_sec,MTTR_sec,Recovery_Utility,Evasion_Success,Policy_Compliant,Hallucinations" > $RESULTS_CSV

echo "[Arena] Initializing Cyber Resilience Testbed..."
source "$VENV_PATH"
echo "[Arena] LangGraph Environment Activated."

# Build the C binaries just in case
cd ../red_team && make && cd ../orchestrator

# for virus in cpu_virus mem_virus io_virus; do
for virus in io_virus; do
    for gen in 1 2 3; do
        for trial in 1 2 3; do
            
            echo "----------------------------------------------------"
            echo "[Arena] Starting: $virus | Gen: $gen | Trial: $trial"
            
            # 1. Start Benign Background Workload (Ground Truth)
            ./ground_truth.sh &
            BENIGN_PID=$!
            
            # 2. Start Blue Team Daemon (Unbuffered output via -u flag)
            python3 -u ../blue_team/daemon.py > blue_team_run.log 2>&1 &
            DAEMON_PID=$!
            
            # Give Daemon time to establish normal baseline
            sleep 3 
            
            # 3. Launch Red Team Attack
            START_TIME=$(date +%s%3N) # Millisecond precision
            ../red_team/$virus --gen $gen &
            VIRUS_PID=$!
            
            # 4. Stopwatch & Monitoring Loop
            RECOVERED=0
            EVADED=0
            ELAPSED_SEC=0
            
            while [ $ELAPSED_SEC -lt $TIMEOUT_SEC ]; do
                CURRENT_TIME=$(date +%s%3N)
                ELAPSED_SEC=$(( (CURRENT_TIME - START_TIME) / 1000 ))
                
                # Check for original binaries AND Gen 3 camouflaged process names
                if ! pgrep -f "(cpu_virus|mem_virus|io_virus|kworker/u4:2|systemd-journal|rsyslogd)" > /dev/null; then
                    RECOVERED=1
                    break
                fi
                sleep 0.5
            done
            
            # 5. Calculate Metrics
            if [ $RECOVERED -eq 1 ]; then
                # Success: System Recovered
                MTTR_SEC=$ELAPSED_SEC
                EVASION_SUCCESS=0
            else
                # Failure: Timeout reached (OS effectively dead)
                MTTR_SEC="TIMEOUT"
                EVASION_SUCCESS=1
            fi
            
            # Parse Python JSON Logs for MTTD and Guardrail Data
            MTTD_SEC=$(grep -oP '"timestamp": \K[0-9.]+' blue_team_run.log | head -1 | awk -v st=$((START_TIME/1000)) '{print $1 - st}')
            if [ -z "$MTTD_SEC" ]; then MTTD_SEC="MISSING"; fi
            
            POLICY_FAILS=$(grep -c '"policy_compliant": false' blue_team_run.log)
            HALLUCINATIONS=$(grep -c 'Forbidden keyword detected' blue_team_run.log)
            
            # Check if Benign Process Survived (Post-Recovery Utility)
            if ps -p $BENIGN_PID > /dev/null; then
                RECOVERY_UTILITY=100
            else
                RECOVERY_UTILITY=0
                echo "[!] Target Precision Error: Benign Process Killed!"
            fi
            
            # Write to CSV
            echo "$virus,$gen,$trial,$MTTD_SEC,$MTTR_SEC,$RECOVERY_UTILITY,$EVASION_SUCCESS,$((POLICY_FAILS == 0 ? 1 : 0)),$HALLUCINATIONS" >> $RESULTS_CSV
            
            # 6. Environmental Reset (Kill-Switch)
            kill -9 $BENIGN_PID $DAEMON_PID $VIRUS_PID 2>/dev/null
            pkill -9 -f "(cpu_virus|mem_virus|io_virus|kworker/u4:2|systemd-journal|rsyslogd)" 2>/dev/null
            rm -rf /tmp/os_benign_tasks /tmp/os_arena
            
            echo "[Arena] Trial Complete. MTTR: $MTTR_SEC sec. Resetting environment..."
            sleep 2
        done
    done
done

echo "[Arena] Experiment fully completed. Results saved to $RESULTS_CSV."
echo "[Arena] Compiling IEEE LaTeX metrics table..."
python3 metrics_compiler.py