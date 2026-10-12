import os
import matplotlib
matplotlib.use('Agg')  # headless backend: avoids GTK/GLib errors on WSL/servers

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# IEEE Publication Formatting Standards
plt.style.use('seaborn-v0_8-paper')
plt.rcParams.update({
    'font.size': 8,
    'font.family': 'serif',
    'axes.labelsize': 8,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 8,
    'figure.dpi': 300,
})

# Map a model label (used on the charts) to its results CSV file.
MODEL_FILES = {
    'TinyLlama\n(1.1B)': 'experiment_results_tinyllama.csv',
    'Llama-3.2\n(3B)':  'experiment_results_ollama3B.csv',
    'Llama-3.1\n(8B)':  'experiment_results_ollama8B.csv',
}


def load(path):
    """Load one results CSV, coercing TIMEOUT/MISSING to the 300s bound."""
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    for col in ('MTTD_sec', 'MTTR_sec'):
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(300.0)
    # make the guardrail/evasion columns numeric too, just in case
    for col in ('Recovery_Utility', 'Evasion_Success', 'Policy_Compliant', 'Hallucinations'):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df


def errors_of(df):
    """Total reasoning errors = hallucinations + policy non-compliances."""
    return int(df['Hallucinations'].sum() + (df['Policy_Compliant'] == 0).sum())


# Load everything once; drop models whose CSV is absent.
DATA = {label: load(path) for label, path in MODEL_FILES.items()}
DATA = {k: v for k, v in DATA.items() if v is not None}


def fig1_capability_vs_latency():
    """Fig 1: MTTD (bars) vs total reasoning errors (line), mid/large models."""
    wanted = ['Llama-3.2\n(3B)', 'Llama-3.1\n(8B)']
    models = [m for m in wanted if m in DATA]
    if not models:
        print("[Fig 1] skipped: need the 3B and/or 8B CSV.")
        return

    mttd = [DATA[m]['MTTD_sec'].mean() for m in models]
    total_errors = [errors_of(DATA[m]) for m in models]

    fig, ax1 = plt.subplots(figsize=(5.0, 2.5))
    ax1.bar(models, mttd, color='#cccccc', edgecolor='black', width=0.4, label='MTTD (s)')
    ax1.set_ylabel('Mean Time to Detect (s)', color='black')
    ax1.set_ylim(0, max(320, max(mttd) * 1.15))

    ax2 = ax1.twinx()
    ax2.plot(models, total_errors, color='black', marker='o', linewidth=1.5, label='Total Errors')
    ax2.set_ylabel('Reasoning Errors', color='black')
    ax2.set_ylim(-5, max(65, (max(total_errors) + 1) * 1.2))

    l1, lab1 = ax1.get_legend_handles_labels()
    l2, lab2 = ax2.get_legend_handles_labels()
    ax1.legend(l1 + l2, lab1 + lab2, loc='center left', bbox_to_anchor=(1.2, 0.5))
    plt.tight_layout()
    plt.savefig('Fig. 1. Inference Latency vs. Reasoning Fidelity.png', bbox_inches='tight')
    plt.close()


def fig2_camouflage_efficacy():
    """Fig 2: MTTD per virus across generations (uses the largest model present)."""
    for label in ['Llama-3.1\n(8B)', 'Llama-3.2\n(3B)', 'TinyLlama\n(1.1B)']:
        if label in DATA:
            df = DATA[label]
            break
    else:
        print("[Fig 2] skipped: no CSV found.")
        return

    g = df.groupby(['Virus_Type', 'Generation'])['MTTD_sec'].mean().unstack()
    generations = ['Gen 1', 'Gen 2', 'Gen 3']
    styles = {
        'cpu_virus': ('s', '-',  'black',   'CPU Virus'),
        'mem_virus': ('^', '--', '#555555', 'MEM Virus'),
        'io_virus':  ('o', ':',  '#888888', 'I/O Virus'),
    }

    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    for virus, (mk, ls, col, lab) in styles.items():
        if virus in g.index:
            vals = [g.loc[virus].get(gnum, np.nan) for gnum in (1, 2, 3)]
            ax.plot(generations, vals, marker=mk, linestyle=ls, color=col, linewidth=1.5, label=lab)

    ax.set_ylabel('Mean Time to Detect (s)')
    ax.legend(loc='upper left')
    plt.tight_layout()
    plt.savefig('Fig. 2. Camouflage Efficacy on AI Detection.png', bbox_inches='tight')
    plt.close()


def fig3_cognitive_degradation():
    """Fig 3: stacked policy-fails + hallucinations per model."""
    models = list(DATA.keys())
    if not models:
        print("[Fig 3] skipped: no CSV found.")
        return

    policy_fails = np.array([int((DATA[m]['Policy_Compliant'] == 0).sum()) for m in models])
    hallucinations = np.array([int(DATA[m]['Hallucinations'].sum()) for m in models])

    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    ax.bar(models, policy_fails, color='#ffffff', edgecolor='black', hatch='////', width=0.4, label='Policy Fails')
    ax.bar(models, hallucinations, bottom=policy_fails, color='#666666', edgecolor='black', width=0.4, label='Hallucinations')
    ax.set_ylabel('Total Count')
    ax.legend(loc='upper left')
    plt.tight_layout()
    plt.savefig('Fig. 3. Breakdown of Agent Reasoning Failures.png', bbox_inches='tight')
    plt.close()


def fig4_out_of_band_resilience():
    """Fig 4: evasion rate vs benign-OS utility, pooled across all data."""
    all_df = pd.concat(DATA.values(), ignore_index=True)
    evasion = all_df['Evasion_Success'].mean() * 100.0
    utility = all_df['Recovery_Utility'].mean()

    fig, ax = plt.subplots(figsize=(3.5, 1.5))
    ax.barh(
        ['Evasion Rate\n(AI Failed)', 'Benign OS Utility\n(Sandbox Succeeded)'],
        [evasion, utility],
        color=['#333333', '#dddddd'], edgecolor='black', height=0.5,
    )
    ax.set_xlabel('Percentage (%)')
    ax.set_xlim(0, 110)
    plt.tight_layout()
    plt.savefig('Fig. 4. Sandbox Efficacy During Agent Failure.png', bbox_inches='tight')
    plt.close()


if __name__ == '__main__':
    if not DATA:
        print("No experiment_results_*.csv files found in this folder.")
        print("Run the arena first, then rename its output to one of:")
        for f in MODEL_FILES.values():
            print(f"   {f}")
    else:
        print("Loaded models: " + ", ".join(m.replace("\n", " ") for m in DATA))
        fig1_capability_vs_latency()
        fig2_camouflage_efficacy()
        fig3_cognitive_degradation()
        fig4_out_of_band_resilience()
        print("Done. Four figures generated from your own CSV data.")
