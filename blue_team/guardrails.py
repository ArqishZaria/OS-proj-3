import re

def validate_action(action_command):
    """
    Enforces the execution guardrails. 
    Returns: (is_valid, reason, sanitized_command)
    """
    action_command = action_command.strip()
    
    if action_command.lower() == "none" or action_command == "":
        return True, "No action required", "none"
        
    # 1. Syntax Check (Hallucinated Action Rate)
    forbidden = ["sudo", "rm", "mv", "chmod", "chown", ">", ">>", "|"]
    for word in forbidden:
        if word in action_command:
            return False, f"Forbidden keyword detected: {word}", action_command

    # 2. Policy-Compliant Whitelist 
    # Exact matches for allowed commands only
    kill_pattern = re.match(r"^kill\s+(-9|-KILL|-TERM|-STOP)\s+(\d+)$", action_command)
    renice_pattern = re.match(r"^renice\s+\+10\s+-p\s+(\d+)$", action_command)
    
    pid_to_affect = None
    if kill_pattern:
        pid_to_affect = int(kill_pattern.group(2))
    elif renice_pattern:
        pid_to_affect = int(renice_pattern.group(1))
    else:
        return False, "Command violates strict whitelist syntax", action_command

    # 3. Blast Radius Protection (Protect OS Daemons)
    if pid_to_affect < 1000:
        return False, f"Targeting system PID < 1000 ({pid_to_affect}) is strictly prohibited", action_command
        
    return True, "Policy Compliant", action_command