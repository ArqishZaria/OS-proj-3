import time
import os
import subprocess
import json
from telemetry import get_system_telemetry
from agent_swarm import build_graph
from guardrails import validate_action

def pin_to_core(core_id=3):
    """Isolates the Blue Team to a specific CPU core for OOB defense simulation."""
    try:
        os.sched_setaffinity(0, {core_id})
        print(f"[Daemon] Successfully pinned Blue Team to CPU Core {core_id}.")
    except AttributeError:
        print("[Warning] OS lacks sched_setaffinity support. Recommend running via taskset.")

def main():
    print("[Blue Team Daemon] Initializing Autonomous Defense...")
    pin_to_core(3)
    graph = build_graph()
    
    while True:
        start_time = time.time()
        
        # 1. Fetch OS Telemetry
        telemetry = get_system_telemetry()
        
        initial_state = {
            "telemetry": telemetry,
            "analysis": "",
            "proposed_action": "none",
            "causal_chain": "none",
            "collateral_damage_avoided": True
        }
        
        # 2. Invoke LangGraph AI Swarm
        final_state = graph.invoke(initial_state)
        action = final_state.get("proposed_action", "none")
        
        # 3. Guardrails & Execution
        if action and action.lower() != "none":
            is_valid, reason, safe_cmd = validate_action(action)
            
            # Print the exact Forensic JSON required for paper metrics
            forensic_log = {
                "timestamp": time.time(),
                "causal_chain": final_state.get("causal_chain"),
                "collateral_damage_avoided": final_state.get("collateral_damage_avoided"),
                "action_attempted": action,
                "policy_compliant": is_valid,
                "policy_reason": reason
            }
            print(f"[FORENSICS] {json.dumps(forensic_log)}")
            
            # Execute if Whitelist passes
            if is_valid:
                print(f"[Executor] Policy passed. Executing: {safe_cmd}")
                try:
                    subprocess.run(safe_cmd.split(), check=True)
                except subprocess.CalledProcessError as e:
                    print(f"[Executor Error] Failed to actuate command: {e}")
            else:
                print(f"[Executor Blocked] {reason}")
        
        # 4. Strict 1.0s Polling Cadence
        elapsed = time.time() - start_time
        sleep_time = max(0.0, 1.0 - elapsed)
        time.sleep(sleep_time)

if __name__ == "__main__":
    main()