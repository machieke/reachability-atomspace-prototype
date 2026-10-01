# Reachability validation design pack

Read `benchmark_design.md` for the full dataset and experimental proposal.

`ablation_manifest.example.json` describes eight safe factorial variants. It is not a configuration accepted by an existing runtime.

`deployment_episode.example.json` describes one integration-test episode and evaluator expectations. Its assertion text is not executable, and its evaluator-only section must not be exposed to an agent.

`manifest.json` records hashes of the design inputs from this conversation.

`build_examples.py` regenerates the illustrative JSON files. It requires the three original input artifacts next to this directory. It does not implement or run the proposed benchmark.

No actual AtomSpace/PLN/Freeciv integration experiments are included or claimed. JSON parsing and elementary design-file consistency were checked; this is not evidence that the proposed architecture passes the tests.
