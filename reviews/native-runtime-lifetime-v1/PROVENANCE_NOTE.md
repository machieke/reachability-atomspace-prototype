# Consumer provenance clarification

The frozen sources.json/report.json retain the inherited informational field
`frozen_consumer_revision=d2a6b6605eaefc32f0c56e2a7c0d5e9bf11cffb8` from the
previous harness. That commit introduced the earlier work-loop consumer; it does
not identify the actual multi-hop consumer file used in this experiment.

The actual consumer is `experimental_multihop/consumer.py`, introduced at
`b509d2b8d7388a570b5a666e1c845b95d207ad20`, with SHA256
`3ec9c16ed98f2aff48a0db15b88d9c368edc4cdcb133a9789dff6ed96b68c19a`. This hash matches the sealed source manifest and the
file at that commit. It is also unchanged from preserved closure c088775.

The measured implementation/auditor revision remains `fa6c2674bc5977475f1aad9e6c884405ef7b7414`.
The auditor validates the full exact source-file manifest; it does not use the
inherited consumer-revision label as an integrity check. This clarification
changes no frozen source, cohort, receipt, decision or result. Original metadata
and earlier reviews remain intact for independent inspection.
