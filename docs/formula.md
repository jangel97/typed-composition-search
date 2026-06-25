# Recall Decomposition

Our system operates in two sequential stages:

1. **Entity prediction** (performed by the LLM)
2. **Graph resolution** to recover the required tools

For any given query, there are only two possible outcomes:

* The entities are predicted correctly.
* The entities are predicted incorrectly.

Therefore, the overall end-to-end recall can be expressed as the expected recall over these two cases:

[
\boxed{
Recall_{e2e}
============

P(correct)\cdot Recall_{correct}
+
P(wrong)\cdot Recall_{wrong}
}
]

where:

* (P(correct)) is the probability that the LLM predicts the correct source and target entity types (e.g., type prediction accuracy).
* (P(wrong)=1-P(correct)) is the probability that the prediction is incorrect.
* (Recall_{correct}) is the average recall when the entity prediction is correct.
* (Recall_{wrong}) is the average recall when the entity prediction is incorrect.

## Intuition

This equation is simply the **law of total expectation** applied to recall.

Across all queries:

* A fraction (P(correct)) follows the correct graph path and achieves some average recall.
* The remaining fraction (P(wrong)) follows a different graph path, which may still recover part of the relevant information.

The overall recall is therefore the weighted average of these two cases.

## Ideal Case

If the graph only succeeds when the entity prediction is correct, then

[
Recall_{wrong}\approx0.
]

The equation simplifies to

[
Recall_{e2e}
\approx
P(correct)\cdot Recall_{oracle},
]

where (Recall_{oracle}) denotes the recall achieved when the correct entities are provided to the graph.

## Real-World Case

In practice, an incorrect entity prediction does **not** necessarily imply complete failure.

For example:

* the predicted entity may be semantically close to the correct one;
* different entity pairs may share part of the same tool composition;
* multiple valid graph paths may recover similar tools.

As a result,

[
Recall_{wrong} > 0,
]

meaning that the system can still retrieve some of the relevant tools even when the entity prediction is incorrect.

## Interpretation

This decomposition cleanly separates two independent factors affecting end-to-end performance:

* **Model quality**, represented by (P(correct)).
* **Graph robustness to classification errors**, represented by (Recall_{wrong}).

This distinction makes it possible to determine whether improvements in end-to-end recall come from better entity prediction or from a graph topology that is inherently more tolerant to classification errors.
