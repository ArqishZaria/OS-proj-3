import subprocess

def get_system_telemetry():
    """
    Polls standard Linux utilities (ps, free) to create a telemetry snapshot.
    Returns a dictionary of the current system state.
    """
    # 1. Get memory usage via standard 'free'
    try:
        mem_out = subprocess.check_output(["free", "-m"], text=True)
    except Exception:
        mem_out = "Error retrieving memory status."
    
    # 2. Get top 25 processes via standard 'ps'
    # Output format: PID, PPID, %CPU, %MEM, COMMAND
    try:
        ps_out = subprocess.check_output(
            ["ps", "-eo", "pid,ppid,pcpu,pmem,comm", "--sort=-pcpu", "--no-headers"], 
            text=True
        )
    except Exception:
        ps_out = ""
    
    processes = []
    for line in ps_out.strip().split("\n")[:25]:
        parts = line.split()
        if len(parts) >= 5:
            processes.append({
                "pid": int(parts[0]),
                "ppid": int(parts[1]),
                "cpu_percent": float(parts[2]),
                "mem_percent": float(parts[3]),
                "command": " ".join(parts[4:])
            })
            
    return {
        "memory_status": mem_out.strip(),
        "top_processes": processes
    }