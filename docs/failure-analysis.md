# Failure Analysis

The top failure modes from the end-to-end evaluation are documented below.

## Weak Retrieval (No Grounding)
- **Number of affected examples**: 43
- **Example**: Tweet 545729
- **Why the system failed**: The hybrid retriever could not find any historically similar examples above the minimum similarity threshold.
- **Proposed improvement**: Increase the size of the historical corpus or lower the fallback retrieval threshold for safe intents.

## Intent Misclassification
- **Number of affected examples**: 29
- **Example**: Tweet 2142987: Predicted OTHER, True DAMAGED_MISSING_ITEM
- **Why the system failed**: The weak-supervision trained model failed to predict the manually assigned gold intent, often due to overlapping vocabulary (e.g. delivery vs damaged).
- **Proposed improvement**: Gather a manually annotated training set or utilize a more powerful semantic embedding classifier.

## Conservative Complaint Escalation
- **Number of affected examples**: 25
- **Example**: Tweet 1018224
- **Why the system failed**: The policy explicitly hard-escalates all serious complaints regardless of confidence.
- **Proposed improvement**: Allow the agent to generate an empathetic de-escalation reply before routing to a human.

## Unsupported Action Escalation
- **Number of affected examples**: 13
- **Example**: Tweet 2399207
- **Why the system failed**: The user requested an action the agent cannot perform natively without high grounding.
- **Proposed improvement**: Implement API tool calling capabilities to actually modify orders.

## Over-escalation on Ambiguous Follow-ups
- **Number of affected examples**: 1
- **Example**: Tweet 1828696
- **Why the system failed**: Short messages were correctly classified but escalated aggressively due to a missing context signal.
- **Proposed improvement**: Build an entity extractor to check if order IDs/tracking numbers exist before escalating.

