# Manual steps for Moez

Your laptop hosts everything: minikube, Ollama, every run, every screenshot.

## One-time setup on your laptop

- [ ] Open a WSL 2 terminal (Ubuntu) in the repository folder. The Makefile and scripts
      expect Linux/WSL 2.
- [ ] Python 3.12 in WSL: `make install PY=python3.12` creates `.venv` (already in
      `.gitignore`), then `source .venv/bin/activate`, `make test`, `make lint`,
      `python -m pytest eval/tests -q`.
- [ ] Ollama on Windows running; `ollama list` shows `nomic-embed-text` and `llama3.2:3b`.
      Ollama must listen beyond localhost for minikube to reach it: set the Windows user
      environment variable `OLLAMA_HOST=0.0.0.0:11434`, restart Ollama, allow it in
      the Windows firewall for the private network only.
- [ ] Docker Desktop: Settings > Resources (WSL integration) on for your distro.
- [ ] Corpus: `make fetch`, `python corpus/fetch.py --verify`.
- [ ] Cluster: `make cluster MINIKUBE_MEMORY=6144 MINIKUBE_CPUS=4`, then the README's
      apply order with `MODEL_IP` checked as in PLAN.md (`minikube ssh -- getent hosts
      host.minikube.internal`).
- [ ] `make images TAG=$(git rev-parse HEAD)` (also builds `rahbar-eval`), deploy.
- [ ] Check one answer through the Ingress before any Part B run.

## Part B

- [ ] `python eval/convert_golden.py`; open each PDF at the candidate page and set the
      real physical `page`; set `origin` truthfully for each of the 15 (who wrote them in
      Assignment 2).
- [ ] Write at least 4 hand questions yourself (Rayyan writes the other 4+), including
      hard ones (paraphrase, two chunks, Batch B after Part A).
- [ ] Add at least 5 unanswerable questions in total (topics the corpus does not cover).
- [ ] `python eval/synth_questions.py --n 20`, review your half: check each against its
      page, fix wording, set `reviewed: true`, copy accepted ones into `golden.jsonl`.
- [ ] `python eval/golden_check.py` passes.
- [ ] Before each suite run, empty the answer cache:
      `kubectl -n rahbar exec deploy/redis -- redis-cli FLUSHALL`.
- [ ] Baseline run: `kubectl -n rahbar apply -f k8s/eval-job.yaml` with `LABEL=baseline`
      (or locally `python eval/suite.py --label baseline` through a port-forward).
- [ ] Hand-label 8+ answers into `eval/hand_labels.jsonl` before reading the judge's
      verdicts; then `python eval/end_to_end.py --agreement <result.json>`.
- [ ] Second run with the same seed; `python eval/suite.py --compare A.json B.json`;
      explain the remaining variation (CPU floating point in Ollama, judge, HNSW ties).
- [ ] Noise test: `--typos` run; noise documents ingested by Rayyan's ingestion Job into
      a copy collection, suite with `--label noise-docs`.
- [ ] Screenshot B: the evaluation summary with all three levels.

## Part C

- [ ] Choose the change (chunk size or overlap), set it in `k8s/candidate/configmap.yaml`.
- [ ] Choose and justify thresholds from the baseline numbers; write them into
      `eval/gate.yaml` and `k8s/eval/gate-configmap.yaml`.
- [ ] Build the candidate collection (Rayyan's candidate ingestion Job), apply
      `k8s/candidate/api-candidate.yaml`, run `k8s/candidate/eval-job-candidate.yaml`.
- [ ] A deliberately bad candidate (for example `CHUNK_SIZE=60`) that fails the gate, and
      one that passes. Screenshots C. Release decision with reasons.

## Part E

- [ ] Write about 20 of the 40 live queries (Rayyan writes the rest): about 28 in the
      golden set's domain, at least 12 outside it.
- [ ] Look at the similarity distribution, choose `--threshold` and `--min-share`,
      justify them (the paper's example: under 85% covered is a gap).
- [ ] E3: after Rayyan's Batch B ingestion, re-run the suite, compare, explain.
- [ ] E4: 6 new golden questions for the uncovered topics, re-run coverage. Screenshots E.

## Part F

- [ ] Gate ConfigMap edit changes the outcome without rebuilding:
      `kubectl -n rahbar edit configmap rahbar-gate`, re-run the eval Job (screenshot).
- [ ] `scripts/release.sh` with a candidate stopped by the gate (never rolled out).
- [ ] `scripts/release.sh --force` with a bad candidate, then
      `kubectl -n rahbar rollout undo deployment/api`, `kubectl rollout status`, one
      question, and its trace showing the previous collection and embedding digest.
- [ ] F5: `kubectl top pod -n rahbar --containers` during an eval run and an ingestion run
      (`minikube addons enable metrics-server` is part of `make cluster`); set requests
      and limits from those numbers; copy the numbers into the report.
- [ ] Screenshot F: `kubectl get all,pvc,configmap,cronjob,job -n rahbar`; logs of a
      completed ingestion Job and a completed eval Job.
- [ ] Copy results from the PVC (`k8s/eval/results-shell.yaml`, `kubectl cp`) into
      `eval/results/` and commit them.

## Report and demo

- [ ] Sections B, C, E, F; short answers (b), (d), (f) with Rayyan; G2 rows for
      monitorability, reliability, adaptability.
- [ ] Contribution table and AI statement together.
- [ ] Rehearse on a fresh `minikube delete && make cluster`, following only the README
      and `k8s/README.md`.
- [ ] Be able to explain Rayyan's verification, ledger and trace code.
