# Assignment 3 cluster trace samples

Trace JSON lines copied from the `traces` PVC of the minikube cluster on 24 November 2026.
File names keep the pod that wrote them.

| File | What it holds |
|---|---|
| `traces-api-7bfc46b695-m749l.jsonl`, `traces-api-7bfc46b695-kc554.jsonl` | Live api pods during suite run 1. Includes h08 (trace `9e04846187974764815db6b6825bacb8`, the D5 diagnosis) and the D4 injection test (trace `1d64072e...`) |
| `traces-api-848c6f59b7-xjlv6.jsonl` | Trace `a3-promoted-103424` after promoting `rahbar-same` (collection `rahbar-same-c172...`) |
| `traces-api-65f5bcccd4-ssw6c.jsonl` | Trace `a3-undone-103424` after `kubectl rollout undo`: previous collection `rahbar-3615c46d...` and the same embedding digest `0a109f42...` |

```bash
python scripts/trace_tool.py show 9e04846187974764815db6b6825bacb8 traces/a3-cluster
python scripts/trace_summary.py traces/a3-cluster
```
