# RAHBAR Assignment 3: submission

CS4032, group: Abdul Moez Yousaf (24i-3048), Syed Rayyan Hassan (24i-3000).
Due 28 November 2026, 11:59 PM.

## Deliverables

| Deliverable | Where |
|---|---|
| Repository | https://github.com/rayyanhasan899/Rahbar, branch `dev2` |
| Report (8 pages and the screenshot appendix) | `docs/assignment-3/report/RAHBAR-A3-REPORT.pdf` |
| Demo guide | `docs/assignment-3/DEMO.md` |

## Steps before submitting

1. Push the branch:
   ```bash
   git push origin dev2
   ```
2. Check that GitHub shows the report:
   https://github.com/rayyanhasan899/Rahbar/blob/dev2/docs/assignment-3/report/RAHBAR-A3-REPORT.pdf
3. Submit the branch URL, https://github.com/rayyanhasan899/Rahbar/tree/dev2, and attach the
   report PDF. Alternatively, merge `dev2` into `main` and submit the repository URL. GitHub opens
   `main` by default, so graders will not see the A3 work there unless it is merged.

## Where each item the brief asks for is

| Item | Location |
|---|---|
| Code | `api/`, `indexer/`, `eval/`, `scripts/` |
| Kubernetes manifests | `k8s/`, with fresh-cluster steps in `k8s/README.md` |
| Golden set (37 questions) and gate thresholds | `eval/golden.jsonl`, `eval/gate.yaml`, `k8s/eval/gate-configmap.yaml` |
| Evaluation results | `eval/results/cluster/` (suites, gate runs, coverage) |
| Trace samples | `traces/a3-cluster/` |
| Screenshots in the report appendix | `docs/evidence/a3/screenshots/full/` (other evidence in `docs/evidence/a3/`) |
| Commands for each part (A to F) | `README.md`, section "Assignment 3: RAGOps commands per part" |
