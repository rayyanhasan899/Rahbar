# Day 3 security review

This records concrete findings from Trivy and the repository's SonarCloud check.
No scanner, webhook, network policy or required review has been disabled.

## Changes

- Fixable HIGH/CRITICAL image findings in the old OS packages, Starlette,
  pdfminer.six and pypdf were patched. The scan gate now fails on either HIGH
  or CRITICAL when a fix exists. Initial reports are retained as negative evidence.
- Manifest filenames are confined to the selected corpus directory, including
  resolved symlinks. The transfer helper accepts plain supported filenames and
  checks hashes before copying. The indexer rejects paths that escape its corpus.
- Generated audit artifacts use a private directory under the project. The manifest
  renderer cannot overwrite arbitrary paths. Measurement input is confined to the
  project. A deployment image must match a safe OCI-reference character set before
  it can be inserted into the deliberately generated rollout-demo Dockerfile.
- Actions are resolved to full commit SHAs from their official repositories.
  Dependency locks include the complete validated Python 3.12 dependency closure
  and official PyPI wheel hashes. Installs require hashes and binary wheels.
- A failed wheel hash check was never bypassed. The successful retry retained
  integrity checking. The exact failed wheel was not identified by pip's message.
- The hosted provider rejects non-HTTPS endpoints before any API key is sent.

## HTTP findings requiring contextual review

The assignment and supplied Chroma 1.0.12 deployment use HTTP internally. The
remaining local-protocol findings must be reviewed on their actual scope:

| Path | Destination and scope | Existing controls and residual risk |
|---|---|---|
| API Chroma readiness/startup/query | Chroma ClusterIP on port 8000 inside the application namespace | Default deny; only API/indexer can connect. No key or student records are needed. Traffic is not encrypted against a compromised node/network administrator. |
| Cluster acceptance/socket probes | The four application Services and the selected model IP | Verifies enforced allow/deny paths; does not change them. Public/owned fixtures only. |
| Browser screenshot and evaluator | A runner-loopback Ingress port-forward and `rahbar.local` mapped to loopback | No Internet HTTP request or authentication credential. The screenshot is the actual app, with real API output. |
| Host/integration model HTTP | The explicitly selected Ollama host or isolated Docker-network model container | Only API/indexer provider egress is allowed, to one IP/port. Public-policy questions and excerpts; no hosted key. A shared/untrusted network would require TLS or a trusted tunnel. |

These are documented architecture limitations, not proof of Internet-safe
unencrypted production hosting. A future external deployment needs TLS on
Ingress and protected backend/provider transport. Do not suppress arbitrary
HTTP findings or close issues without checking the destination and payload.
The eight explicitly authorized HTTP decisions below are the only accepted issues.

## Approved scoped risk decisions — 7 November 2026

The owner approved only the eight HTTP findings listed in
`docs/evidence/day3-sonar-accepted-findings.json`. Codex applied Accept in the
signed-in SonarCloud account with the exact private/loopback scope above and a
three-day reopening date of **10 November 2026**. Optional analyzer-training
sharing of the comment was unchecked. The original finding list and actual UI
screenshot are retained. No other issue was accepted and no scan, policy or
approval requirement was disabled. The automatic analysis must still rerun and
pass; the acceptance operation alone is not a green CI claim.
