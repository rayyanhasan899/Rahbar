# Phase 2 offline trace samples

These two JSONL records were produced by the actual answer/trace code using the
owned tests.fakes.POISON passage, in-memory fake Redis/retrieval and httpx.MockTransport.
No model/service/cluster was contacted. Provider/model names describe configured
payloads, not a real Ollama execution. Unknown index/digest fields are deliberately
unknown. Timings measure only this fake local execution and must never be quoted
as production latency, threshold calibration or PartB/D5/Kubernetes evidence.

The first record captures actual mocked transport messages and neutralization;
the second retains original cache provenance with no fresh model invocation.
Use `python scripts/trace_tool.py show <trace_id> traces/phase2-offline` and
`python scripts/trace_summary.py traces/phase2-offline`. The generator was the
ignored .venv/phase2_trace_demo.py; the committed regression tests cover these
same paths and can be rerun offline. Real trace samples/screenshots remain Phase3.
