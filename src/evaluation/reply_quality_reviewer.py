"""
Tkinter Desktop Reviewer for Human Reply-Quality Evaluation.
Used to score the ~30 human agreement sample in evaluation/reply_quality_human_review.csv.

Keyboard Shortcuts:
  1-5 = Set score for active rubric dimension
  N   = Next example
  P   = Previous example
  S   = Save progress
"""

import os
import sys
import argparse
import pandas as pd

DEFAULT_REVIEW_PATH = "evaluation/reply_quality_human_review.csv"

RUBRIC_DIMS = [
    ("human_relevance", "1. Relevance (1=Off-topic, 5=Directly on-point)"),
    ("human_helpfulness", "2. Helpfulness (1=Useless, 5=Actionable resolution)"),
    ("human_groundedness", "3. Groundedness (1=Contradictory/unsupported, 5=Fully evidenced)"),
    ("human_clarity", "4. Clarity (1=Unclear/awkward, 5=Crisp & concise)"),
    ("human_unsupported_claims", "5. Unsupported Claims (1=Fabricated, 5=Zero unsupported claims)"),
    ("human_overall", "★ Overall Quality (1=Unacceptable, 5=Excellent)")
]


def load_review_dataset(path=DEFAULT_REVIEW_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Review file not found at '{path}'.")
    return pd.read_csv(path, dtype=str).fillna('')


def save_review_dataset(df, path=DEFAULT_REVIEW_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)


def get_review_progress(df):
    total = len(df)
    reviewed_mask = (
        df['human_relevance'].str.strip().ne('') &
        df['human_helpfulness'].str.strip().ne('') &
        df['human_groundedness'].str.strip().ne('') &
        df['human_clarity'].str.strip().ne('') &
        df['human_unsupported_claims'].str.strip().ne('') &
        df['human_overall'].str.strip().ne('')
    )
    reviewed = int(reviewed_mask.sum())
    return reviewed, total - reviewed, total


def run_gui(review_path=DEFAULT_REVIEW_PATH):
    import tkinter as tk
    from tkinter import ttk, messagebox

    df = load_review_dataset(review_path)

    # Start on first incomplete item
    incomplete = df[df['human_overall'].str.strip() == ''].index
    start_idx = incomplete[0] if len(incomplete) > 0 else 0

    root = tk.Tk()
    root.title("Hiver AI Support Agent - Reply Quality Human Reviewer")
    root.geometry("920x820")
    root.minsize(840, 720)

    current_idx = [start_idx]

    # Scoring Variables (Strings 1-5)
    var_scores = {col: tk.StringVar(value="") for col, _ in RUBRIC_DIMS}
    var_notes = tk.StringVar(value="")
    var_status = tk.StringVar(value="")

    # --- Styles ---
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Title.TLabel", font=("Arial", 11, "bold"), foreground="#0f172a")
    style.configure("Subhead.TLabel", font=("Arial", 9, "bold"), foreground="#1e293b")
    style.configure("Dim.TLabel", font=("Arial", 9, "bold"), foreground="#0f172a")
    style.configure("Shortcut.TLabel", font=("Arial", 8, "bold"), foreground="#64748b")
    style.configure("Save.TButton", font=("Arial", 10, "bold"), foreground="#047857", padding=5)

    # --- Top Frame ---
    top_frame = ttk.Frame(root, padding=(10, 6, 10, 4))
    top_frame.pack(fill=tk.X)

    head_row = ttk.Frame(top_frame)
    head_row.pack(fill=tk.X)

    lbl_title = ttk.Label(head_row, text="Reply Quality Human Review (LLM-as-Judge Agreement Sample)", style="Title.TLabel")
    lbl_title.pack(side=tk.LEFT)

    lbl_keys = ttk.Label(head_row, text="[N] Next  |  [P] Prev  |  [S] Save Progress", style="Shortcut.TLabel")
    lbl_keys.pack(side=tk.RIGHT)

    lbl_prog = ttk.Label(top_frame, text="", font=("Arial", 9, "bold"), foreground="#0f172a")
    lbl_prog.pack(anchor=tk.W, pady=(2, 2))

    prog_bar = ttk.Progressbar(top_frame, orient=tk.HORIZONTAL, mode='determinate', maximum=len(df))
    prog_bar.pack(fill=tk.X, pady=(0, 4))

    # --- Main Content ---
    main_frame = ttk.Frame(root, padding=(10, 2, 10, 4))
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Query & Context
    info_frame = ttk.LabelFrame(main_frame, text=" Customer Query & Conversation Context ", padding=6)
    info_frame.pack(fill=tk.X, pady=(0, 4))

    lbl_intent_badge = ttk.Label(info_frame, text="", font=("Arial", 9, "bold"), foreground="#2563eb")
    lbl_intent_badge.pack(anchor=tk.W, pady=(0, 2))

    txt_context = tk.Text(info_frame, height=2, wrap=tk.WORD, bg="#f8fafc", fg="#475569", font=("Arial", 9), relief="flat")
    txt_context.pack(fill=tk.X, pady=(0, 2))

    txt_message = tk.Text(info_frame, height=2, wrap=tk.WORD, bg="#ffffff", fg="#0f172a", font=("Arial", 10, "bold"), relief="flat")
    txt_message.pack(fill=tk.X)

    # Evidence & Generated Reply (Split Pane or Stack)
    pair_frame = ttk.Frame(main_frame)
    pair_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

    ev_frame = ttk.LabelFrame(pair_frame, text=" Retrieved Historical Precedents (Evidence) ", padding=6)
    ev_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))

    txt_evidence = tk.Text(ev_frame, height=6, wrap=tk.WORD, bg="#f1f5f9", fg="#334155", font=("Arial", 8), relief="flat")
    txt_evidence.pack(fill=tk.BOTH, expand=True)

    rep_frame = ttk.LabelFrame(pair_frame, text=" Generated Reply Under Evaluation ", padding=6)
    rep_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(4, 0))

    txt_reply = tk.Text(rep_frame, height=6, wrap=tk.WORD, bg="#f0fdf4", fg="#14532d", font=("Arial", 10, "bold"), relief="flat")
    txt_reply.pack(fill=tk.BOTH, expand=True)

    # Rubric Scoring Cards
    rubric_frame = ttk.LabelFrame(main_frame, text=" Human Scoring (Score strictly 1 to 5) ", padding=6)
    rubric_frame.pack(fill=tk.X, pady=(0, 4))

    for col, label_text in RUBRIC_DIMS:
        row_f = ttk.Frame(rubric_frame)
        row_f.pack(fill=tk.X, pady=1)

        lbl_dim = ttk.Label(row_f, text=label_text, width=42, anchor=tk.W, style="Dim.TLabel")
        lbl_dim.pack(side=tk.LEFT)

        for score in [1, 2, 3, 4, 5]:
            rb = ttk.Radiobutton(
                row_f,
                text=str(score),
                value=str(score),
                variable=var_scores[col]
            )
            rb.pack(side=tk.LEFT, padx=8)

    # Notes field
    notes_frame = ttk.Frame(rubric_frame)
    notes_frame.pack(fill=tk.X, pady=(4, 2))
    ttk.Label(notes_frame, text="Notes (Optional):", width=16, style="Subhead.TLabel").pack(side=tk.LEFT)
    ent_notes = ttk.Entry(notes_frame, textvariable=var_notes)
    ent_notes.pack(side=tk.LEFT, fill=tk.X, expand=True)

    # --- Bottom Controls ---
    bot_frame = ttk.Frame(root, padding=(10, 4, 10, 8))
    bot_frame.pack(fill=tk.X, side=tk.BOTTOM)

    lbl_status_msg = ttk.Label(bot_frame, textvariable=var_status, foreground="#059669", font=("Arial", 9))
    lbl_status_msg.pack(side=tk.TOP, anchor=tk.W, pady=(0, 4))

    btn_row = ttk.Frame(bot_frame)
    btn_row.pack(fill=tk.X)

    btn_prev = ttk.Button(btn_row, text="⬅ [P] Previous", command=lambda: navigate(-1))
    btn_prev.pack(side=tk.LEFT, padx=(0, 4))

    btn_save = ttk.Button(btn_row, text="💾 [S] Save Progress", command=lambda: save_current())
    btn_save.pack(side=tk.LEFT, padx=4)

    btn_next = ttk.Button(btn_row, text="[N] Next ➡", command=lambda: navigate(1))
    btn_next.pack(side=tk.RIGHT, padx=(4, 0))

    btn_save_next = ttk.Button(
        btn_row,
        text="✓ Save & Next Example",
        style="Save.TButton",
        command=lambda: save_and_advance()
    )
    btn_save_next.pack(side=tk.RIGHT, padx=4)

    # --- Logic ---
    def load_example(idx):
        if idx < 0 or idx >= len(df):
            return

        current_idx[0] = idx
        row = df.iloc[idx]

        lbl_intent_badge.config(text=f"Tweet ID: {row['tweet_id']}  |  Predicted Intent: {row['predicted_intent']}")

        # Update text boxes
        txt_context.config(state=tk.NORMAL)
        txt_context.delete("1.0", tk.END)
        raw_ctx = str(row.get('previous_context', '')).strip()
        txt_context.insert(tk.END, raw_ctx if raw_ctx and raw_ctx != 'nan' else "[No preceding context - First turn]")
        txt_context.config(state=tk.DISABLED)

        txt_message.config(state=tk.NORMAL)
        txt_message.delete("1.0", tk.END)
        txt_message.insert(tk.END, str(row.get('text', '')))
        txt_message.config(state=tk.DISABLED)

        txt_evidence.config(state=tk.NORMAL)
        txt_evidence.delete("1.0", tk.END)
        txt_evidence.insert(tk.END, str(row.get('retrieved_evidence', 'No evidence')))
        txt_evidence.config(state=tk.DISABLED)

        txt_reply.config(state=tk.NORMAL)
        txt_reply.delete("1.0", tk.END)
        txt_reply.insert(tk.END, str(row.get('generated_reply', '')))
        txt_reply.config(state=tk.DISABLED)

        # Pre-populate ONLY saved human scores
        for col, _ in RUBRIC_DIMS:
            val = str(row.get(col, '')).strip()
            var_scores[col].set(val if val in ['1', '2', '3', '4', '5'] else "")

        var_notes.set(str(row.get('human_notes', '')).strip())

        # Update progress header
        reviewed, remaining, total = get_review_progress(df)
        prog_bar['value'] = reviewed
        lbl_prog.config(text=f"Example {idx + 1} of {total}  |  Reviewed: {reviewed}/{total}  ({remaining} remaining)")
        btn_prev.config(state=tk.NORMAL if idx > 0 else tk.DISABLED)
        var_status.set(f"Loaded example {idx + 1}.")

    def save_current(show_msg=True):
        idx = current_idx[0]
        # Record scores
        for col, _ in RUBRIC_DIMS:
            df.at[idx, col] = var_scores[col].get().strip()
        df.at[idx, 'human_notes'] = var_notes.get().strip()

        save_review_dataset(df, review_path)
        if show_msg:
            var_status.set(f"Saved scores for example {idx + 1} (Tweet ID: {df.at[idx, 'tweet_id']}).")

    def save_and_advance():
        save_current(show_msg=False)
        idx = current_idx[0]
        if idx + 1 < len(df):
            load_example(idx + 1)
        else:
            reviewed, remaining, total = get_review_progress(df)
            if remaining == 0:
                messagebox.showinfo("Review Complete", "All 30 examples have been reviewed! You can now run `llm_human_agreement.py`.")
            else:
                var_status.set("Reached final example. Click Previous or finish remaining items.")

    def navigate(delta):
        save_current(show_msg=False)
        next_idx = current_idx[0] + delta
        if 0 <= next_idx < len(df):
            load_example(next_idx)

    # Shortcuts
    root.bind('<n>', lambda e: navigate(1))
    root.bind('<N>', lambda e: navigate(1))
    root.bind('<p>', lambda e: navigate(-1))
    root.bind('<P>', lambda e: navigate(-1))
    root.bind('<s>', lambda e: save_current())
    root.bind('<S>', lambda e: save_current())
    root.bind('<Return>', lambda e: save_and_advance())

    def on_closing():
        save_current(show_msg=False)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    load_example(start_idx)
    root.mainloop()


def main():
    parser = argparse.ArgumentParser(description="Human Reply-Quality Reviewer")
    parser.add_argument("--path", default=DEFAULT_REVIEW_PATH, help="Path to reply_quality_human_review.csv")
    args = parser.parse_args()
    run_gui(args.path)


if __name__ == "__main__":
    main()
