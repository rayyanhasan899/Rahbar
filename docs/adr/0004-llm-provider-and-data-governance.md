# ADR 0004: Local Ollama and public policy data

Date: 6 November 2026. Status: accepted design; runtime verification is recorded
separately in the Day 3 report.

We support Ollama through the same `LLMProvider` interface as the optional hosted
adapter. The laptop uses the installed `llama3.2:3b` model, and both ingestion and
retrieval use `nomic-embed-text`, dimension 768. An immutable publication records
the embedding pin. A different configured model blocks readiness and queries.
The installed model digests are recorded in evidence; a tag alone cannot prove
identical model bytes on another machine.

The local provider avoids sending questions and policy excerpts to a hosted
service. Only public FAST-NUCES policy material is selected. Documents are
downloaded serially and hashed; third-party PDFs and extracted full text stay
out of Git and application images. A project PVC delivers verified documents
read-only to the indexer. Fixtures are owned fictional Markdown delivered by
ConfigMap in the ephemeral CI/CD cluster. They are explicitly a different corpus.

Ollama receives fenced evidence, the constrained Answer schema and temperature
0.2. Validation and a single feedback retry reject malformed responses and
citations outside the retrieved passages. Exhaustion returns a safe decline.
The laptop bounds each generation to a 4096-token context and 512 output tokens.
These limits reduce memory pressure; long answers may be truncated and rejected
rather than returned as unverified text. A configured timeout also bounds calls.

Prompt instructions and a passage guard are defense layers, not a proof against
all prompt injection. Conversation history is explicitly not documentary evidence.
Browser output uses `textContent`. We do not execute text from users or models.
Cache hits retain citations and are scoped to index generation, provider/model
and quality settings; history, flagged instructions and declines bypass storage.
Numbers and directional Theory/Lab outcomes guard observed semantic false hits.

Application logs contain identifiers, retrieved chunk IDs/scores and token counts,
not full question/evidence/answer bodies or credentials. Logs and stored evaluation
outputs still deserve review before sharing. The real golden set contains public
policy questions; no private student records or credentials are required.

Hosted mode remains optional and must be configured using an out-of-Git Secret.
Enabling it requires a deliberate provider-egress rule and review of its data
retention terms. The committed placeholder is never applied automatically. The
indexer has no Redis egress or Kubernetes token; publication invalidates cache
entries through the generation the API reads from Chroma.

Tradeoff: a 3B local model has limited reasoning quality and the small laptop
serializes expensive work. Citation membership does not establish that every
claim follows from its citation. Human correctness review remains distinct from
the automated citation, recall and must-abstain gate.
