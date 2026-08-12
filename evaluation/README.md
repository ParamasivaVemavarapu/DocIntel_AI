# DocIntel Evaluation

This offline benchmark contains four synthetic, human-labeled questions and recorded retrieval/citation outputs. It measures:

- **Macro Precision@K:** relevant chunks divided by retrieved chunks, averaged per query.
- **Macro Recall@K:** retrieved relevant chunks divided by all relevant chunks, averaged per query.
- **Citation correctness:** citations mapped to human-marked supporting chunks divided by all returned citations.

Run:

```bash
python evaluation/evaluate.py
```

The command prints JSON metrics and fails when configured quality gates are missed. Replace the recorded output fields in `golden_set.jsonl` with outputs from a new retriever build to compare versions. The small synthetic set is a regression fixture, not evidence of production performance.
