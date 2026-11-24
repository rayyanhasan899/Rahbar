# M14: rehearsal on a fresh cluster

A disposable minikube profile (`rahbar-rehearsal`, 4 GiB, 2 CPUs) was built from a clean
clone, following only `README.md` and `k8s/README.md`. The main cluster was stopped
during the run (its data kept) and started again afterwards. Full log:
`rehearsal-20261124.txt`.

## First attempt (commit 5629dbe): failed

The first indexer Job failed within seconds. The base ConfigMap listed
`/corpus/batch-a` and `/corpus/batch-b` in `INCOMING_DIRS`, but `deploy_local.py` copies
only `corpus/raw` into the corpus volume, so the scope folders did not exist. Our main
cluster had worked only because the batches had been copied in by hand earlier.
`deploy_local.py` also kept waiting on the failed Job instead of stopping.

Fix (commit 65167a6): the base scope is `/corpus`, the Batch A/B scope is a documented
Part A step in `k8s/README.md`, and `deploy_local.py` exits with the Job's log when the
indexer Job fails.

## Second attempt (commit 65167a6): passed, 12:29 to 12:41

| Step | Result |
|---|---|
| clean clone, `make install`, `make test`, `pytest eval/tests` | passed (55 and 44 tests) |
| `make fetch`, `corpus/fetch.py --verify` | all PVC source hashes verified |
| `make cluster`, `make images`, `deploy_local.py` | indexer Job completed; API and UI rolled out |
| first answer through the Ingress | "Six years [academic-rules-handbook-jun-2026.pdf / 1.23]" |
| eval Job with `LABEL=baseline`, `CREATE_BASELINE=true` | baseline written, gate passed |

The README example `MODEL_IP=192.168.65.254` was correct on this laptop. README says
`git checkout main`; the rehearsal used branch dev2 because the A3 work is not merged yet.
The rehearsal baseline used the 37-question golden set, so its numbers (recall@5 0.969,
faithfulness 0.316 over 19 judged answers) are not comparable with the 31-question runs
in the report.
