# ADR 0003: Answer pipeline, providers and the request contract

## Status
Accepted; real runtime verified 7 November 2026. Relevance floor 0.65 and
cache threshold 0.75 follow committed measurements. Temperature 0.2 is a
deliberate low-variance setting, not a measured claim of superiority over zero.

## Context
Sections 3.2 to 3.5 ask for a production query path: a pluggable provider, honest
abstention, validated structured output with a retry and a safe fallback,
citations that match retrieved passages, resistance to instructions planted in
documents, follow-up questions and a semantic cache shared by three API replicas.
A small local model (llama3.2:3b on Ollama) is the default, so the design has to
hold up when the model is weak.

## Decision
- **Steps live in separate modules** under `api/app/services/`: `guard.py`
  (injection), `citations.py`, `cache.py`, orchestrated by `answer.py`. Each step
  has offline tests with fakes.
- **Providers** share one prompt builder (`providers/llm/prompt.py`). Ollama gets
  the `Answer` JSON schema as `format`; the hosted provider uses OpenAI-compatible
  JSON mode with the schema in the system message. Both raise `ProviderOutputError`
  for an unparseable reply and `ProviderUnavailable` for timeouts and HTTP errors.
- **Relevance floor before generation.** Below `RELEVANCE_FLOOR` the API declines
  without a model call, so must-abstain questions cannot be talked into an answer.
- **One retry, then a fallback.** Invalid JSON, a missing citation or a citation
  that matches no retrieved passage (source, section, and page when given) triggers
  one retry that tells the model what was wrong. A second failure returns a
  declined answer. An unreachable model falls back at once, without a retry.
- **Two layers against injection.** The prompt marks passages and the question as
  data, inside BEGIN/END markers. Sentences in passages that read like instructions
  to an assistant are replaced before the model sees them. The patterns are kept
  narrow so real policy sentences survive.
- **Temperature 0.2.** Factual JSON needs little variation, within the assignment
  range of 0–0.3. This value was exercised by the real golden gate; no unperformed
  temperature-zero comparison or claim that temperature fixes hallucination is made.
- **Contract changes.** `AskRequest` gains an optional `history` (at most 10 turns,
  the API uses the last `MAX_HISTORY_TURNS`). Existing clients that send only
  `question` are unaffected. Cache state travels in the `X-Cache` response header
  (HIT or MISS, absent when the cache was bypassed), which the UI already reads, so
  `AskResponse` is unchanged. Retrieval failures return 503 instead of 500.
- **Follow-ups** add the previous question to the retrieval query and send earlier
  turns to the model labelled as "not evidence". The UI sends history only when
  the user ticks "Follow-up to the previous answer".
- **Cache** in Redis, namespaced by index generation, embedding model, provider and
  LLM model. A hit needs cosine similarity at or above `CACHE_THRESHOLD` and the
  same numbers (years, clause numbers) in both questions. Follow-ups, declined
  answers, fallbacks and instruction-like questions are never stored. Redis errors
  are treated as misses.

## Options considered
- Letting the model decide every abstention: fails exactly when the model is weak.
- Dropping invalid citations silently instead of retrying: hides fabrication and
  can leave an answer with no support.
- A second LLM call to rewrite follow-ups into standalone questions: better recall
  on vague follow-ups, but doubles latency on a CPU laptop. Revisit if follow-up
  recall is poor.
- An in-process cache: three replicas would each keep their own and miss each
  other's answers.
- Adding `cached` to `AskResponse`: works, but changes the contract the evaluator
  and tests rely on, when a header carries the same information.

## Consequences
- Must-abstain behaviour depends on the floor, so the floor must be measured:
  `scripts/score_margins.py` on a real evaluation run.
- The cache threshold must be measured: `scripts/cache_threshold_experiment.py`
  over `eval/cache-pairs.yaml`, shipping the lowest value with zero false hits.
- CI's `e2e-eval` uses real embeddings and Chroma with the stub LLM. It gates
  retrieval, citation and abstention mechanics, not answer wording.
- Watch `rahbar_fallbacks_total` and `rahbar_generation_retries_total`: a rising
  rate means the model or prompt is struggling.

Day 3 adds canonical model refusals, contradiction retry, sentence citation tags,
per-entry expiry, directional intent guards and prompt/schema-sensitive cache
namespaces. The real poisoned-index probe safely refused the planted instruction.
The corrected audit proved generation-based invalidation and serialized writers
without granting indexer-to-Redis access. See PIPELINE.md for measured tradeoffs.
