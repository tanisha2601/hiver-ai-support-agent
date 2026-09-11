"""
Hiver AI Support Agent - Human-in-the-Loop Review Tool (Optimized for Speed)
GUI built with Python Tkinter for rapid manual review and human-in-the-loop verification of the 200 evaluation examples.

Keyboard Shortcuts:
  A = Accept AI suggestion, mark human_verified=True, immediately jump to next unverified example
  E = Focus/open human edit controls
  N = Next example
  P = Previous example
  S = Save progress

Usage:
  python -m src.evaluation.manual_labeler
  python -m src.evaluation.manual_labeler --validate
  python -m src.evaluation.manual_labeler --summary
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np

VALID_INTENTS = [
    "DELIVERY_SHIPPING",
    "PRIME_SUBSCRIPTION",
    "REFUND_RETURN",
    "DAMAGED_MISSING_ITEM",
    "PAYMENT_BILLING",
    "ACCOUNT_LOGIN",
    "ORDER_MODIFICATION",
    "CUSTOMER_SERVICE_COMPLAINT",
    "OTHER"
]

VALID_DIFFICULTIES = ["easy", "medium", "hard"]

DEFAULT_SOURCE_PATH = "evaluation/golden_set.csv"
DEFAULT_TARGET_PATH = "evaluation/golden_set_human.csv"
RANDOM_SEED = 42


def init_human_dataset(source_path=DEFAULT_SOURCE_PATH, target_path=DEFAULT_TARGET_PATH, seed=RANDOM_SEED):
    """
    Initializes the human review CSV if it doesn't already exist.
    Preserves original heuristic/AI labels as `ai_suggested_*` columns.
    Randomizes the order using a fixed seed, but retains original tweet_ids.
    Does NOT populate fake human labels.
    """
    if os.path.exists(target_path):
        df = pd.read_csv(target_path, dtype=str).fillna('')
        for col in ['human_verified', 'changed_from_ai', 'annotation_source']:
            if col not in df.columns:
                df[col] = ''
        return df

    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source golden set not found at {source_path}")

    source_df = pd.read_csv(source_path, dtype=str).fillna('')
    
    # Randomize using fixed random seed
    shuffled_df = source_df.sample(frac=1, random_state=seed).reset_index(drop=True)
    
    text_col = shuffled_df['customer_text'] if 'customer_text' in shuffled_df.columns else shuffled_df.get('text', '')
    
    human_df = pd.DataFrame({
        'example_id': shuffled_df.get('example_id', [f"GOLD_{i+1:03d}" for i in range(len(shuffled_df))]),
        'tweet_id': shuffled_df['tweet_id'].astype(str),
        'conversation_id': shuffled_df['conversation_id'].astype(str),
        'text': text_col,
        'customer_text': text_col,
        'previous_context': shuffled_df.get('previous_context', ''),
        'intent': '',
        'difficulty': '',
        'needs_context': '',
        'annotator': '',
        'annotation_source': '',
        'human_verified': '',
        'changed_from_ai': '',
        'ai_suggested_intent': shuffled_df.get('intent', ''),
        'ai_suggested_difficulty': shuffled_df.get('difficulty', ''),
        'ai_suggested_needs_context': shuffled_df.get('needs_context', ''),
        'annotation_notes': ''
    })
    
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    human_df.to_csv(target_path, index=False)
    print(f"Initialized randomized human evaluation template at: {target_path} ({len(human_df)} examples)")
    return human_df


def save_dataset(df, target_path=DEFAULT_TARGET_PATH):
    """Safely saves the DataFrame to disk."""
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    df.to_csv(target_path, index=False)


def get_progress_summary(df_or_path=DEFAULT_TARGET_PATH):
    """Computes summary statistics for human-in-the-loop review progress."""
    if isinstance(df_or_path, str):
        if not os.path.exists(df_or_path):
            return {
                "total": 0, "verified": 0, "remaining": 0,
                "accepted": 0, "corrected": 0, "intent_distribution": {}
            }
        df = pd.read_csv(df_or_path, dtype=str)
    else:
        df = df_or_path

    total = len(df)
    # Human-verified requires explicit human action
    verified_mask = df.get('human_verified', pd.Series(False, index=df.index)).astype(str).str.lower().isin(['true', '1', 'yes'])
    verified = int(verified_mask.sum())
    remaining = total - verified

    accepted_mask = verified_mask & (df['annotation_source'].astype(str) == 'human_verified')
    corrected_mask = verified_mask & (df['annotation_source'].astype(str) == 'human_corrected')
    
    accepted = int(accepted_mask.sum())
    corrected = int(corrected_mask.sum())

    distribution = {}
    if verified > 0:
        counts = df.loc[verified_mask, 'intent'].value_counts().to_dict()
        for intent in VALID_INTENTS:
            distribution[intent] = counts.get(intent, 0)
    else:
        for intent in VALID_INTENTS:
            distribution[intent] = 0

    return {
        "total": total,
        "verified": verified,
        "remaining": remaining,
        "accepted": accepted,
        "corrected": corrected,
        "intent_distribution": distribution
    }


def validate_human_dataset(df_or_path=DEFAULT_TARGET_PATH):
    """
    Validates that the human-reviewed dataset satisfies all assignment requirements:
    1. Exactly 200 examples
    2. Every example has explicit human action (human_verified == 'True')
    3. All 9 intents represented
    4. No missing intent
    5. No missing difficulty
    6. No missing needs_context
    7. No duplicate tweet_id
    8. Valid annotation_source ('human_verified' or 'human_corrected')
    """
    if isinstance(df_or_path, str):
        if not os.path.exists(df_or_path):
            return False, [f"Target file does not exist: {df_or_path}"], {}
        df = pd.read_csv(df_or_path, dtype=str)
    else:
        df = df_or_path

    errors = []
    total = len(df)

    # 1. Exactly 200 examples
    if total != 200:
        errors.append(f"Expected exactly 200 rows, found {total}.")

    # 7. No duplicate tweet_id
    dupes = df['tweet_id'].duplicated().sum()
    if dupes > 0:
        dup_ids = df[df['tweet_id'].duplicated()]['tweet_id'].tolist()
        errors.append(f"Found {dupes} duplicate tweet_id entries: {dup_ids[:5]}.")

    # 2. Every example must have an explicit human action
    if 'human_verified' not in df.columns:
        errors.append("Missing required column 'human_verified'.")
        unverified_count = total
    else:
        verified_mask = df['human_verified'].astype(str).str.lower().isin(['true', '1', 'yes'])
        unverified_count = total - int(verified_mask.sum())
        if unverified_count > 0:
            errors.append(f"{unverified_count} of 200 examples have NOT been verified by a human.")

    # 4. No missing intent
    missing_intent = df['intent'].isna() | (df['intent'].astype(str).str.strip() == '')
    if missing_intent.sum() > 0:
        errors.append(f"{missing_intent.sum()} examples are missing an intent.")

    invalid_intents = df[~missing_intent & ~df['intent'].isin(VALID_INTENTS)]['intent'].unique()
    if len(invalid_intents) > 0:
        errors.append(f"Invalid intent values found: {invalid_intents}.")

    # 5. No missing difficulty
    missing_diff = df['difficulty'].isna() | (df['difficulty'].astype(str).str.strip() == '')
    if missing_diff.sum() > 0:
        errors.append(f"{missing_diff.sum()} examples are missing difficulty.")

    invalid_diff = df[~missing_diff & ~df['difficulty'].str.lower().isin(VALID_DIFFICULTIES)]['difficulty'].unique()
    if len(invalid_diff) > 0:
        errors.append(f"Invalid difficulty values found: {invalid_diff}.")

    # 6. No missing needs_context
    missing_ctx = df['needs_context'].isna() | (df['needs_context'].astype(str).str.strip() == '')
    if missing_ctx.sum() > 0:
        errors.append(f"{missing_ctx.sum()} examples are missing needs_context.")

    # 8. Valid annotation_source
    if 'annotation_source' not in df.columns:
        errors.append("Missing required column 'annotation_source'.")
    else:
        missing_source = df['annotation_source'].isna() | (df['annotation_source'].astype(str).str.strip() == '')
        if missing_source.sum() > 0:
            errors.append(f"{missing_source.sum()} examples are missing 'annotation_source'.")
        invalid_sources = df[~missing_source & ~df['annotation_source'].isin(['human_verified', 'human_corrected'])]['annotation_source'].unique()
        if len(invalid_sources) > 0:
            errors.append(f"Invalid annotation_source values found: {invalid_sources}.")

    # 3. All 9 intents represented
    present_intents = set(df.loc[~missing_intent, 'intent'].unique())
    missing_categories = set(VALID_INTENTS) - present_intents
    if missing_categories:
        errors.append(f"Not all 9 intents are represented. Missing: {missing_categories}.")

    summary = get_progress_summary(df)
    is_valid = len(errors) == 0
    return is_valid, errors, summary


def run_gui(source_path=DEFAULT_SOURCE_PATH, target_path=DEFAULT_TARGET_PATH, annotator_name="human_reviewer"):
    """Launches the optimized Tkinter human-in-the-loop review interface."""
    import tkinter as tk
    from tkinter import ttk, messagebox

    df = init_human_dataset(source_path, target_path)

    def find_next_unverified(from_idx):
        verified_mask = df.get('human_verified', pd.Series(False, index=df.index)).astype(str).str.lower().isin(['true', '1', 'yes'])
        # Look forward
        forward = df.index[(df.index > from_idx) & (~verified_mask)]
        if len(forward) > 0:
            return forward[0]
        # Wrap around
        backward = df.index[(df.index <= from_idx) & (~verified_mask)]
        if len(backward) > 0:
            return backward[0]
        # All verified, advance normally
        return min(from_idx + 1, len(df) - 1)

    # Initial start index: first unverified example
    verified_mask = df.get('human_verified', pd.Series(False, index=df.index)).astype(str).str.lower().isin(['true', '1', 'yes'])
    unverified_indices = df[~verified_mask].index
    start_index = unverified_indices[0] if len(unverified_indices) > 0 else 0

    root = tk.Tk()
    root.title("Hiver AI Support Agent - Fast Human-in-the-Loop Reviewer")
    root.geometry("880x760")
    root.minsize(820, 680)

    current_idx = [start_index]

    # Variables
    var_intent = tk.StringVar()
    var_difficulty = tk.StringVar(value="medium")
    var_needs_context = tk.StringVar(value="no")
    var_status = tk.StringVar()

    # --- Styles ---
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Title.TLabel", font=("Arial", 11, "bold"), foreground="#0f172a")
    style.configure("Subhead.TLabel", font=("Arial", 9, "bold"), foreground="#334155")
    style.configure("Shortcut.TLabel", font=("Arial", 8, "bold"), foreground="#64748b")
    style.configure("Progress.TLabel", font=("Arial", 9, "bold"), foreground="#0f172a")
    style.configure("Accept.TButton", font=("Arial", 11, "bold"), foreground="#047857", padding=6)
    style.configure("Edit.TButton", font=("Arial", 9, "bold"), foreground="#1d4ed8", padding=4)
    style.configure("Nav.TButton", font=("Arial", 9), padding=3)

    # --- Top Frame: Header & Compact Progress Indicator ---
    top_frame = ttk.Frame(root, padding=(10, 8, 10, 4))
    top_frame.pack(fill=tk.X)

    header_row = ttk.Frame(top_frame)
    header_row.pack(fill=tk.X)

    lbl_title = ttk.Label(header_row, text="Hiver AI Support Agent — Rapid HITL Review", style="Title.TLabel")
    lbl_title.pack(side=tk.LEFT)

    lbl_shortcuts = ttk.Label(header_row, text="[A] Accept  |  [E] Edit  |  [N] Next  |  [P] Prev  |  [S] Save", style="Shortcut.TLabel")
    lbl_shortcuts.pack(side=tk.RIGHT)

    # Progress Indicator
    lbl_progress = ttk.Label(top_frame, text="", style="Progress.TLabel")
    lbl_progress.pack(anchor=tk.W, pady=(3, 3))

    prog_bar = ttk.Progressbar(top_frame, orient=tk.HORIZONTAL, mode='determinate', maximum=200)
    prog_bar.pack(fill=tk.X, pady=(0, 4))

    # --- Middle Frame: Content Area ---
    main_frame = ttk.Frame(root, padding=(10, 2, 10, 4))
    main_frame.pack(fill=tk.BOTH, expand=True)

    # 1. Previous Conversation Context (Compact)
    ctx_frame = ttk.LabelFrame(main_frame, text=" Previous Context ", padding=4)
    ctx_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 4))

    txt_context = tk.Text(ctx_frame, height=2, wrap=tk.WORD, bg="#f8fafc", fg="#475569", font=("Arial", 9), relief="flat")
    txt_context.pack(fill=tk.BOTH, expand=True)

    # 2. Customer Message (Clear & High-Contrast)
    msg_frame = ttk.LabelFrame(main_frame, text=" Customer Message ", padding=6)
    msg_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

    txt_message = tk.Text(msg_frame, height=3, wrap=tk.WORD, bg="#ffffff", fg="#0f172a", font=("Arial", 10, "bold"), relief="flat")
    txt_message.pack(fill=tk.BOTH, expand=True)

    # 3. AI Suggestion Card (Prominent & Fast Action Button)
    ai_box = ttk.LabelFrame(main_frame, text=" AI Suggestion & Quick Action ", padding=8)
    ai_box.pack(fill=tk.X, pady=(0, 6))

    ai_info_row = ttk.Frame(ai_box)
    ai_info_row.pack(fill=tk.X, pady=(0, 4))

    lbl_ai_display = ttk.Label(ai_info_row, text="", font=("Arial", 10, "bold"), foreground="#0f172a")
    lbl_ai_display.pack(side=tk.LEFT)

    lbl_verified_status = ttk.Label(ai_info_row, text="", font=("Arial", 9, "italic"), foreground="#059669")
    lbl_verified_status.pack(side=tk.RIGHT)

    btn_accept_quick = ttk.Button(
        ai_box,
        text="✓ ACCEPT SUGGESTION  [Press A]  (Move to next unverified)",
        style="Accept.TButton",
        command=lambda: accept_suggestion()
    )
    btn_accept_quick.pack(fill=tk.X, pady=(2, 0))

    # 4. Human Edit Section (Compact)
    annot_frame = ttk.LabelFrame(main_frame, text=" Human Edit Controls [Press E to focus] ", padding=8)
    annot_frame.pack(fill=tk.X, pady=(0, 4))

    intent_grid_frame = ttk.Frame(annot_frame)
    intent_grid_frame.pack(fill=tk.X, pady=(0, 4))

    radio_buttons = []
    for i, intent in enumerate(VALID_INTENTS):
        r = i // 3
        c = i % 3
        rb = ttk.Radiobutton(
            intent_grid_frame,
            text=intent,
            value=intent,
            variable=var_intent
        )
        rb.grid(row=r, column=c, sticky=tk.W, padx=4, pady=1)
        radio_buttons.append(rb)

    meta_grid = ttk.Frame(annot_frame)
    meta_grid.pack(fill=tk.X, pady=(2, 4))

    lbl_diff = ttk.Label(meta_grid, text="Difficulty:", style="Subhead.TLabel")
    lbl_diff.pack(side=tk.LEFT, padx=(0, 4))

    for d in VALID_DIFFICULTIES:
        rb_d = ttk.Radiobutton(meta_grid, text=d.capitalize(), value=d, variable=var_difficulty)
        rb_d.pack(side=tk.LEFT, padx=3)

    lbl_ctx_req = ttk.Label(meta_grid, text="   Needs Context?", style="Subhead.TLabel")
    lbl_ctx_req.pack(side=tk.LEFT, padx=(10, 4))

    for val in ["yes", "no"]:
        rb_c = ttk.Radiobutton(meta_grid, text=val.capitalize(), value=val, variable=var_needs_context)
        rb_c.pack(side=tk.LEFT, padx=3)

    btn_edit_save = ttk.Button(
        annot_frame,
        text="✎ Save / Apply Human Edit  (Corrected)",
        style="Edit.TButton",
        command=lambda: apply_human_edit()
    )
    btn_edit_save.pack(anchor=tk.W, pady=(2, 0))

    # --- Bottom Controls & Status ---
    bottom_frame = ttk.Frame(root, padding=(10, 4, 10, 8))
    bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

    lbl_status_msg = ttk.Label(bottom_frame, textvariable=var_status, foreground="#059669", font=("Arial", 9))
    lbl_status_msg.pack(side=tk.TOP, anchor=tk.W, pady=(0, 4))

    btn_box = ttk.Frame(bottom_frame)
    btn_box.pack(fill=tk.X)

    btn_prev = ttk.Button(btn_box, text="⬅ [P] Previous", style="Nav.TButton", command=lambda: navigate(-1))
    btn_prev.pack(side=tk.LEFT, padx=(0, 4))

    btn_save = ttk.Button(btn_box, text="💾 [S] Save", style="Nav.TButton", command=lambda: trigger_save())
    btn_save.pack(side=tk.LEFT, padx=4)

    btn_summary = ttk.Button(btn_box, text="📊 Summary", style="Nav.TButton", command=lambda: show_summary_popup())
    btn_summary.pack(side=tk.LEFT, padx=4)

    btn_finish = ttk.Button(btn_box, text="✅ Validate", style="Nav.TButton", command=lambda: run_finish_validation())
    btn_finish.pack(side=tk.LEFT, padx=4)

    btn_next = ttk.Button(btn_box, text="[N] Next ➡", style="Nav.TButton", command=lambda: navigate(1))
    btn_next.pack(side=tk.RIGHT, padx=(4, 0))

    # --- Actions & Logic ---
    def load_example(idx):
        if idx < 0 or idx >= len(df):
            return

        current_idx[0] = idx
        row = df.iloc[idx]

        # Context
        txt_context.config(state=tk.NORMAL)
        txt_context.delete("1.0", tk.END)
        raw_ctx = str(row.get('previous_context', ''))
        if raw_ctx.strip() and raw_ctx != 'nan':
            txt_context.insert(tk.END, raw_ctx)
        else:
            txt_context.insert(tk.END, "[No previous context - First turn of conversation]")
        txt_context.config(state=tk.DISABLED)

        # Message
        txt_message.config(state=tk.NORMAL)
        txt_message.delete("1.0", tk.END)
        raw_text = str(row.get('text', row.get('customer_text', '')))
        txt_message.insert(tk.END, raw_text)
        txt_message.config(state=tk.DISABLED)

        # AI Suggestion
        ai_intent = str(row.get('ai_suggested_intent', 'N/A'))
        ai_diff = str(row.get('ai_suggested_difficulty', 'N/A'))
        ai_ctx = str(row.get('ai_suggested_needs_context', 'N/A'))
        lbl_ai_display.config(
            text=f"AI Candidate:  {ai_intent}   |   Diff: {ai_diff}   |   NeedsCtx: {ai_ctx}"
        )

        is_verified = str(row.get('human_verified', '')).lower() in ['true', '1', 'yes']
        if is_verified:
            source = str(row.get('annotation_source', 'verified'))
            lbl_verified_status.config(text=f"✓ Already Reviewed ({source})", foreground="#059669")
            var_intent.set(str(row.get('intent', '')))
            var_difficulty.set(str(row.get('difficulty', 'medium')).lower())
            ctx_val = str(row.get('needs_context', '')).lower()
            var_needs_context.set("yes" if ctx_val in ['true', 'yes', '1'] else "no")
            var_status.set(f"Example {idx + 1} reviewed ({source}). Press A to re-accept, or E to edit.")
        else:
            lbl_verified_status.config(text="● Awaiting Human Action", foreground="#d97706")
            var_intent.set(ai_intent if ai_intent in VALID_INTENTS else "")
            var_difficulty.set(ai_diff if ai_diff in VALID_DIFFICULTIES else "medium")
            ai_ctx_bool = "yes" if str(ai_ctx).lower() in ['true', 'yes', '1'] else "no"
            var_needs_context.set(ai_ctx_bool)
            var_status.set("Press 'A' to accept AI suggestion, or 'E' to edit.")

        # Update Progress Bar & Small Progress Indicator
        summary = get_progress_summary(df)
        prog_bar['value'] = summary['verified']
        lbl_progress.config(
            text=f"Ex {idx + 1}/200 (ID: {row['tweet_id']})  |  "
                 f"Verified: {summary['verified']}/200  |  Remaining: {summary['remaining']}  |  "
                 f"Accepted: {summary['accepted']}  |  Corrected: {summary['corrected']}"
        )
        btn_prev.config(state=tk.NORMAL if idx > 0 else tk.DISABLED)

    def accept_suggestion():
        """Accept AI suggestion, mark verified, and jump immediately to next unverified."""
        idx = current_idx[0]
        row = df.iloc[idx]

        ai_intent = str(row.get('ai_suggested_intent', '')).strip()
        ai_diff = str(row.get('ai_suggested_difficulty', 'medium')).strip().lower()
        ai_ctx = str(row.get('ai_suggested_needs_context', 'False')).strip()

        df.at[idx, 'intent'] = ai_intent
        df.at[idx, 'difficulty'] = ai_diff
        df.at[idx, 'needs_context'] = ai_ctx
        df.at[idx, 'human_verified'] = "True"
        df.at[idx, 'changed_from_ai'] = "False"
        df.at[idx, 'annotation_source'] = "human_verified"
        df.at[idx, 'annotator'] = annotator_name
        df.at[idx, 'annotation_notes'] = "Accepted AI candidate suggestion without change"

        save_dataset(df, target_path)

        # Immediately find and jump to the next unverified example
        next_target = find_next_unverified(idx)
        summary = get_progress_summary(df)

        if summary['remaining'] == 0:
            load_example(idx)
            messagebox.showinfo("All Examples Verified!", "Great job! All 200 examples have been human verified.\nYou can click 'Validate' to run final checks.")
        else:
            load_example(next_target)

    def apply_human_edit():
        """Save manual edits/corrections and jump to next unverified."""
        idx = current_idx[0]
        row = df.iloc[idx]

        chosen_intent = var_intent.get().strip()
        if not chosen_intent:
            messagebox.showwarning("Missing Intent", "Please select an intent before saving.")
            return

        chosen_diff = var_difficulty.get().strip().lower()
        chosen_ctx = "True" if var_needs_context.get() == "yes" else "False"

        ai_intent = str(row.get('ai_suggested_intent', '')).strip()
        ai_diff = str(row.get('ai_suggested_difficulty', '')).strip().lower()
        ai_ctx = str(row.get('ai_suggested_needs_context', '')).strip()

        changed_fields = []
        if chosen_intent != ai_intent:
            changed_fields.append(f"intent ({ai_intent} -> {chosen_intent})")
        if chosen_diff != ai_diff:
            changed_fields.append(f"difficulty ({ai_diff} -> {chosen_diff})")
        if chosen_ctx.lower() != ai_ctx.lower():
            changed_fields.append(f"needs_context ({ai_ctx} -> {chosen_ctx})")

        has_changed = len(changed_fields) > 0

        df.at[idx, 'intent'] = chosen_intent
        df.at[idx, 'difficulty'] = chosen_diff
        df.at[idx, 'needs_context'] = chosen_ctx
        df.at[idx, 'human_verified'] = "True"
        df.at[idx, 'changed_from_ai'] = "True" if has_changed else "False"
        df.at[idx, 'annotation_source'] = "human_corrected" if has_changed else "human_verified"
        df.at[idx, 'annotator'] = annotator_name
        df.at[idx, 'annotation_notes'] = f"Human corrected: {', '.join(changed_fields)}" if has_changed else "Human verified"

        save_dataset(df, target_path)

        # Move to next unverified example
        next_target = find_next_unverified(idx)
        summary = get_progress_summary(df)

        if summary['remaining'] == 0:
            load_example(idx)
            messagebox.showinfo("All Examples Verified!", "Great job! All 200 examples have been human verified.")
        else:
            load_example(next_target)

    def focus_edit_controls():
        """Focus the edit controls on pressing E."""
        if radio_buttons:
            radio_buttons[0].focus_set()
        var_status.set("Edit controls focused. Select options and press Enter or click 'Save / Apply Human Edit'.")

    def trigger_save():
        save_dataset(df, target_path)
        var_status.set(f"Progress saved at {pd.Timestamp.now().strftime('%H:%M:%S')}")

    def navigate(delta):
        next_idx = current_idx[0] + delta
        if 0 <= next_idx < len(df):
            load_example(next_idx)

    def show_summary_popup():
        summary = get_progress_summary(df)
        dist_str = "\n".join([f"  • {k:28s}: {v}" for k, v in summary['intent_distribution'].items()])
        msg = (
            f"Review Progress:\n"
            f"-----------------------------------------\n"
            f"Total:      {summary['total']}\n"
            f"Verified:   {summary['verified']} / 200\n"
            f"Remaining:  {summary['remaining']} / 200\n"
            f"Accepted:   {summary['accepted']}\n"
            f"Corrected:  {summary['corrected']}\n\n"
            f"Intent Breakdown (Verified):\n"
            f"{dist_str}\n"
        )
        messagebox.showinfo("Progress Summary", msg)

    def run_finish_validation():
        save_dataset(df, target_path)
        is_valid, errors, summary = validate_human_dataset(df)
        if is_valid:
            messagebox.showinfo(
                "Validation Success",
                f"Validation PASSED!\n\n"
                f"All 200 examples have been human verified.\n"
                f"Accepted: {summary['accepted']} | Corrected: {summary['corrected']}\n"
                f"All 9 intents represented.\n"
                f"Dataset saved to: {target_path}"
            )
        else:
            err_str = "\n".join([f"• {e}" for e in errors])
            messagebox.showwarning(
                "Validation Incomplete",
                f"Validation found incomplete items:\n\n{err_str}\n\n"
                f"Progress: {summary['verified']}/200 verified ({summary['remaining']} remaining)."
            )

    # Keyboard Shortcuts
    root.bind('<a>', lambda e: accept_suggestion())
    root.bind('<A>', lambda e: accept_suggestion())
    root.bind('<e>', lambda e: focus_edit_controls())
    root.bind('<E>', lambda e: focus_edit_controls())
    root.bind('<n>', lambda e: navigate(1))
    root.bind('<N>', lambda e: navigate(1))
    root.bind('<Right>', lambda e: navigate(1))
    root.bind('<p>', lambda e: navigate(-1))
    root.bind('<P>', lambda e: navigate(-1))
    root.bind('<Left>', lambda e: navigate(-1))
    root.bind('<s>', lambda e: trigger_save())
    root.bind('<S>', lambda e: trigger_save())
    root.bind('<Control-s>', lambda e: trigger_save())

    def on_closing():
        save_dataset(df, target_path)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Initial Load
    load_example(start_index)
    root.mainloop()


def main():
    parser = argparse.ArgumentParser(description="Hiver AI Support Agent - Fast Human-in-the-Loop Review Tool")
    parser.add_argument("--source", default=DEFAULT_SOURCE_PATH, help="Path to golden_set.csv")
    parser.add_argument("--target", default=DEFAULT_TARGET_PATH, help="Path to golden_set_human.csv")
    parser.add_argument("--annotator", default="human_reviewer", help="Annotator name identifier")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Random seed for ordering")
    parser.add_argument("--validate", action="store_true", help="Run validation checks on the human-reviewed dataset")
    parser.add_argument("--summary", action="store_true", help="Print progress summary and distribution")

    args = parser.parse_args()

    init_human_dataset(args.source, args.target, seed=args.seed)

    if args.validate:
        is_valid, errors, summary = validate_human_dataset(args.target)
        print("=" * 60)
        print("HUMAN-IN-THE-LOOP EVALUATION DATASET VALIDATION REPORT")
        print("=" * 60)
        print(f"File:           {args.target}")
        print(f"Total:          {summary['total']}")
        print(f"Human Verified: {summary['verified']}/200")
        print(f"Remaining:      {summary['remaining']}/200")
        print(f"Accepted:       {summary['accepted']}")
        print(f"Corrected:      {summary['corrected']}")
        print("-" * 60)
        print("Intent Breakdown (Verified):")
        for intent, count in summary['intent_distribution'].items():
            print(f"  {intent:28s}: {count}")
        print("-" * 60)
        if is_valid:
            print("STATUS: PASS (All 200 examples human-verified and valid)")
            sys.exit(0)
        else:
            print("STATUS: INCOMPLETE / ISSUES FOUND:")
            for err in errors:
                print(f"  [X] {err}")
            sys.exit(1)

    elif args.summary:
        summary = get_progress_summary(args.target)
        print(f"Verified: {summary['verified']}/{summary['total']}  |  Remaining: {summary['remaining']}  |  Accepted: {summary['accepted']}  |  Corrected: {summary['corrected']}")
        print("Intent Breakdown:")
        for intent, count in summary['intent_distribution'].items():
            print(f"  {intent:28s}: {count}")
    else:
        run_gui(args.source, args.target, annotator_name=args.annotator)


if __name__ == "__main__":
    main()
