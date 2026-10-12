import pandas as pd
import numpy as np
import os

CSV_FILE = "experiment_results.csv"
TEX_FILE = "results_table.tex"

def main():
    print("[Metrics Compiler] Parsing raw experimental data...")
    
    if not os.path.exists(CSV_FILE):
        print(f"[Error] {CSV_FILE} not found. Run the Bash orchestrator first.")
        return

    # Load the results
    df = pd.read_csv(CSV_FILE)

    # Clean temporal metrics (Convert 'TIMEOUT' or 'MISSING' to numeric bounds for averaging)
    df['MTTR_sec'] = pd.to_numeric(df['MTTR_sec'], errors='coerce').fillna(300.0) 
    df['MTTD_sec'] = pd.to_numeric(df['MTTD_sec'], errors='coerce').fillna(300.0)

    # Group by Virus Type and Generation to average the 3 trials
    summary = df.groupby(['Virus_Type', 'Generation']).agg(
        MTTD_Mean=('MTTD_sec', 'mean'),
        MTTR_Mean=('MTTR_sec', 'mean'),
        Recovery_Mean=('Recovery_Utility', 'mean'),
        Evasions=('Evasion_Success', 'sum'),
        Policy_Passes=('Policy_Compliant', 'sum'),
        Total_Hallucinations=('Hallucinations', 'sum')
    ).reset_index()

    # Calculate Detection Degradation & Policy Failure Rates
    summary['Policy_Violations'] = 3 - summary['Policy_Passes'] # 3 trials total per generation
    
    # Format for academic presentation
    summary['MTTD (s)'] = summary['MTTD_Mean'].map('{:.2f}'.format)
    summary['MTTR (s)'] = summary['MTTR_Mean'].map('{:.2f}'.format)
    summary['Utility (%)'] = summary['Recovery_Mean'].map('{:.1f}'.format)

    # Rename columns for the final LaTeX output
    final_df = summary[[
        'Virus_Type', 'Generation', 'MTTD (s)', 'MTTR (s)', 
        'Utility (%)', 'Evasions', 'Policy_Violations', 'Total_Hallucinations'
    ]].copy()
    
    final_df.rename(columns={
        'Virus_Type': 'Target OS Vector',
        'Evasions': 'Evasion Count (of 3)',
        'Policy_Violations': 'Policy Fails'
    }, inplace=True)

    print("[Metrics Compiler] Generating LaTeX table...")
    
    # Generate the IEEE-compatible LaTeX table
    latex_code = final_df.to_latex(
        index=False,
        caption="Autonomous Agent Defense Resilience Across Malware Generations",
        label="tab:resilience_metrics",
        column_format="llcccccc" # l=left, c=center alignment
    )

    # Inject standard IEEE booktabs formatting for professional tables
    latex_code = latex_code.replace('\\toprule', '\\toprule\n\\midrule')
    latex_code = latex_code.replace('\\begin{table}', '\\begin{table}[htbp]\n\\centering')

    with open(TEX_FILE, "w") as f:
        f.write(latex_code)

    print(f"[Metrics Compiler] Success! IEEE LaTeX table saved to: {TEX_FILE}")
    print("[Metrics Compiler] You can copy/paste the contents directly into your .tex manuscript.")

if __name__ == "__main__":
    main()