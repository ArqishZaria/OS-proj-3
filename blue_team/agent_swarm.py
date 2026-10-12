import json
import requests
from typing import TypedDict
from langgraph.graph import StateGraph, END

# Local Inference Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"

# MODEL_NAME = "tinyllama:latest" # small model. 1B parameters.
# MODEL_NAME = "llama3.2:3b"    # medium model. 2B parameters.
MODEL_NAME = "llama3.1:8b"    # large model. 8B parameters.

# Graph State Definition
class SwarmState(TypedDict):
    telemetry: dict
    analysis: str
    proposed_action: str
    causal_chain: str
    collateral_damage_avoided: bool

def llm_generate(prompt: str) -> str:
    """Invokes local Ollama instance with strict Temperature constraints."""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "temperature": 0.0 # Force deterministic output for JSON forensics
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        return response.json().get("response", "")
    except Exception as e:
        return ""

def telemetry_agent(state: SwarmState) -> SwarmState:
    """Node 1: Evaluates raw telemetry and flags anomalies."""
    telemetry_str = json.dumps(state["telemetry"], indent=2)
    prompt = f"""
    You are an OS security telemetry agent. Analyze the following processes and memory state.
    Look for CPU starvation (>80% usage), memory hoarding, or orphaned suspicious processes.
    If the system is normal, output ONLY the exact phrase 'STATUS: NORMAL'.
    If anomalous, concisely describe the anomaly and the offending PID.
    
    Telemetry:
    {telemetry_str}
    """
    state["analysis"] = llm_generate(prompt).strip()
    return state

def reasoner_agent(state: SwarmState) -> SwarmState:
    """Node 2: Determines causal chain and selects policy-compliant action."""
    if "STATUS: NORMAL" in state["analysis"].upper():
        state["proposed_action"] = "none"
        state["causal_chain"] = "none"
        state["collateral_damage_avoided"] = True
        return state

    prompt = f"""
    You are an OS Reasoner Agent. Based on the telemetry anomaly, determine the causal chain.
    Propose a mitigation command from this exact list:
    [kill -TERM <PID>, kill -9 <PID>, kill -STOP <PID>, renice +10 -p <PID>]
    
    Anomaly Analysis:
    {state["analysis"]}
    
    You MUST output your conclusion EXACTLY in this JSON format (no markdown formatting, no other text):
    {{
        "causal_chain": "PID_XXXX -> suspicious_behavior",
        "action_executed": "<bash command>",
        "collateral_damage_avoided": true
    }}
    """
    response = llm_generate(prompt)
    
    try:
        # Extract the JSON object directly from the response string
        json_str = response[response.find("{"):response.rfind("}")+1]
        data = json.loads(json_str)
        state["causal_chain"] = data.get("causal_chain", "none")
        state["proposed_action"] = data.get("action_executed", "none")
        state["collateral_damage_avoided"] = data.get("collateral_damage_avoided", True)
    except Exception:
        state["proposed_action"] = "none"
        state["causal_chain"] = "Parse Error"
        state["collateral_damage_avoided"] = False

    return state

def build_graph():
    """Compiles the Agentic workflow."""
    workflow = StateGraph(SwarmState)
    workflow.add_node("telemetry_agent", telemetry_agent)
    workflow.add_node("reasoner_agent", reasoner_agent)
    workflow.set_entry_point("telemetry_agent")
    workflow.add_edge("telemetry_agent", "reasoner_agent")
    workflow.add_edge("reasoner_agent", END)
    return workflow.compile()