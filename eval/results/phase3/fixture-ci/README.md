# Kubernetes fixture evidence - not real Assignment3 measurements

Downloaded unchanged fixture-results.json and indexer log from artifact fixture-eval,
CI45033156542 at source7be4cd598b299c6423b1444ac8026335a2c6fd99.
The indexer log is renamed .jsonl only to preserve its original JSON lines.
deployed-images.json is a reduced deployment-name/image summary of the actual artifact.

This ephemeral Kubernetes run uses the owned CI fixture corpus, real embedding/index
infrastructure, and explicitly STUBBED answer generation. It is not the >=6-document
real corpus, not the25-question A3 golden suite, not a group-laptop demo, not a human
review, not a real faithfulness measurement and not an uncropped terminal screenshot.
Never copy its scores into the A3 PartB results table. It proves only the described
fixture integration and the patched UI image's build/scan/rollout path.
