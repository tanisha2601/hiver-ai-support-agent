# Human-in-the-Loop Evaluation Review Guide

This document describes the human-in-the-loop verification process for the evaluation dataset (`evaluation/golden_set_human.csv`).

---

## 1. Important Methodology Disclosure

**Transparency Note**: The 200 evaluation examples were originally curated and given candidate labels using an automated heuristic script (`src/evaluation/auto_label_golden_set.py`).

Rather than claiming that all 200 examples were independently annotated from scratch by a human, this project provides a **human-in-the-loop verification tool for AI-assisted candidate labels**:
* Presents candidate examples to a human reviewer alongside conversation context and taxonomy guidelines.
* Provides rapid actions to either:
  1. **Accept** the candidate suggestion after manual verification (`annotation_source = "human_verified"`).
  2. **Correct / Override** the intent, difficulty, or context flags (`annotation_source = "human_corrected"`).
* Enforces that no example counts as human-verified without explicit human action.
* In this submission, the final evaluation results are reported against the AI-assisted golden set; human verification remains an available tooling workflow rather than a completed benchmark.

---

## 2. Dataset Metadata Fields

The human-reviewed dataset (`evaluation/golden_set_human.csv`) contains:

| Column | Description |
| :--- | :--- |
| `tweet_id` | Identifier of the customer tweet. |
| `conversation_id` | Conversation thread identifier. |
| `text` / `customer_text` | Customer message text. |
| `previous_context` | Preceding conversation turn(s) if available. |
| `intent` | Verified semantic intent (Human confirmed or edited). |
| `difficulty` | Verified difficulty: `easy`, `medium`, or `hard`. |
| `needs_context` | Verified context dependency: `True` or `False`. |
| `annotator` | Identifier of the human reviewer. |
| `annotation_source` | `human_verified` (accepted) or `human_corrected` (modified). |
| `human_verified` | `True` once explicitly reviewed by the human. |
| `changed_from_ai` | `True` if the human altered any candidate field, else `False`. |
| `ai_suggested_intent` | Original heuristic AI candidate intent. |
| `ai_suggested_difficulty` | Original heuristic difficulty. |
| `ai_suggested_needs_context`| Original heuristic context dependency flag. |
| `annotation_notes` | Details on review action or modified fields. |

---

## 3. Label Definitions & Taxonomy

| Intent | Description | Example Phrases |
| :--- | :--- | :--- |
| `DELIVERY_SHIPPING` | Tracking, delay, courier issues, delivery estimate. | *"Where is my package?", "Still not delivered."* |
| `PRIME_SUBSCRIPTION` | Prime membership billing, auto-renewal, Prime Video. | *"Cancel Prime", "Prime video buffering on TV."* |
| `REFUND_RETURN` | Return labels, drop-off locations, refund status. | *"I returned this last week, where is my refund?"* |
| `DAMAGED_MISSING_ITEM` | Defective, broken, unsealed, missing parts. | *"Box arrived crushed, item is broken."* |
| `PAYMENT_BILLING` | Double charges, unknown transaction, invoice. | *"I was charged twice for order #123."* |
| `ACCOUNT_LOGIN` | Passwords, OTP issues, 2FA, lockout. | *"Cannot log in, OTP not sending to mobile."* |
| `ORDER_MODIFICATION` | Address change, order cancellation before dispatch. | *"Change delivery address before shipping."* |
| `CUSTOMER_SERVICE_COMPLAINT` | Agent grievances, long holds, disconnects. | *"Agent hung up after holding for 30 minutes."* |
| `OTHER` | Feedback, off-topic remarks, general inquiry. | *"Thanks for the assistance! Have a nice day."* |

---

## 4. How to Run the Human-in-the-Loop Reviewer

The tool is a local, lightweight desktop interface built using Python's standard `tkinter` library.

### Start the Review GUI
```bash
python -m src.evaluation.manual_labeler
```
*(Optional: `--annotator "Your Name"` to record your name).*

### Review Workflow
1. Read the **Customer Message** and any **Previous Conversation Context**.
2. Examine the **AI-Assisted Candidate Suggestion**.
3. **If correct**: Click **`✓ Accept Suggestion (Human Verified)`** (Hotkey: `A`).
   - Copies candidate values to human fields.
   - Marks `human_verified = True`, `annotation_source = "human_verified"`.
   - Automatically advances to the next example.
4. **If incorrect or needs refinement**: Adjust the intent, difficulty, or context radio buttons, then click **`✎ Save / Apply Human Edit (Corrected)`**.
   - Marks `human_verified = True`, `annotation_source = "human_corrected"`.
   - Automatically records what fields changed.
   - Advances to the next example.
5. You can navigate back with `⬅ Previous` or exit anytime; all progress auto-saves immediately.

---

## 5. Verification & Validation Commands

### Check Progress Without GUI
```bash
python -m src.evaluation.manual_labeler --summary
```
*Outputs current progress: verified / 200, remaining, accepted count, and corrected count.*

### Run Dataset Validation
```bash
python -m src.evaluation.manual_labeler --validate
```
*Enforces the validation rules:*
* Exactly 200 rows.
* Every single row has an explicit human action (`human_verified == 'True'`).
* All 9 intents represented.
* Zero missing `intent`, `difficulty`, `needs_context`, or `annotation_source`.
* Zero duplicate `tweet_id` entries.
