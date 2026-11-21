# Manual steps for Rayyan

Your laptop does not host the cluster. You build and test Parts A and D with fakes,
push to `dev2`, and the real runs happen on Moez's laptop with you on a call (you must
be able to run and explain them at the demo).

## Before anything

- [ ] `git fetch && git checkout dev2`, `make install`, `make test`, `make lint`.
- [ ] Read Moez's Part B, C, E and F3 code in his pull request line by line.

## Part A (runs on Moez's laptop, you drive)

- [ ] Before the first real run: the verify-only Job, read the "closest cosine" of each
      real document; decide `NEAR_DUP_THRESHOLD` with Moez (the 2026 handbook and the
      2026 prospectus describe the same rules) and write the measured margin down.
- [ ] Ingestion on the unchanged corpus twice: the second log must show 0 chunks
      embedded (screenshot A).
- [ ] Batch B: transfer, add to `INCOMING_DIRS`, run; the verification report for Batch B
      (screenshot A).
- [ ] Changed document, deleted document (counts by document id), rollback and unpin.
- [ ] Copy the reports from the PVC into `eval/results/ingest/` and commit them.

## Part D (runs on Moez's laptop)

- [ ] One full trace record (screenshot D); the trace tool rebuilding a prompt (screenshot D).
- [ ] D4: the question that retrieves the injected Batch B document; its trace shows the
      guardrail action.
- [ ] D3: metrics through `kubectl port-forward`, the trace summary over a window.
- [ ] D5: take one wrong or abstained answer from Moez's Part B results (the row has its
      `trace_id`), find the cause from the trace only, write the 5 lines.
- [ ] Copy 20 to 50 trace lines into `traces/` and commit them.

## Part F (ingestion side)

- [ ] Data lake survives pod restarts (list, delete pods, list again).
- [ ] Logs of a completed ingestion Job (screenshot F); the CronJob listed.

## Hand work for Moez's parts

- [ ] Write at least 4 of the 8+ hand-written golden questions (`origin: human`), with the
      physical PDF page you checked.
- [ ] Review half of the synthetic question candidates (`reviewed: true` only after
      checking the page).
- [ ] Hand-label half of the 8+ answers for judge agreement, before seeing the judge's label.
- [ ] Write about half of the 40 live queries (Part E1).

## Report and demo

- [ ] Sections A and D; short answers (a), (c), (e); G1 rows for ingest, verify, update
      data lake, update retrieval sources; G2 rows for observability and traceability.
- [ ] Contribution table and AI statement together.
- [ ] Demo: ingest an unseen batch on Moez's laptop, open a trace with the trace tool.
