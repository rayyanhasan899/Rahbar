"""Create owned synthetic review drafts; never invent human provenance or results."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "academic-rules-handbook-jun-2026.pdf"
EXPECTED_SOURCE_SHA256 = (
    "4cfee3e191b84aeb9168f17656c7642212ff52b90f2780d028b33c154aa74b62"
)

# Labels come from visual inspection of physical PDF pages 7, 8 and 10, not retrieval.
ORDINARY = [
    (
        "What language is used for instruction and examinations, and which subjects are excepted?",
        "1.1",
        7,
        "English",
    ),
    ("When does the academic year begin and end?", "1.2", 7, "August/September"),
    (
        "Which two regular semesters make up an academic year?",
        "1.3",
        7,
        "Fall and Spring",
    ),
    (
        "When does the Fall semester normally start and finish?",
        "1.4",
        7,
        "December/January",
    ),
    (
        "When does the Spring semester normally start and finish?",
        "1.5",
        7,
        "January/February",
    ),
    (
        "How many teaching, makeup and final-exam weeks does a regular semester have?",
        "1.6",
        7,
        "16",
    ),
    (
        "What weekly classroom teaching does one theory credit hour represent?",
        "1.7",
        7,
        "one",
    ),
    ("How long is one classroom teaching period?", "1.8", 7, "50 to 60"),
    (
        "What credit-hour range is normally assigned to a theory course?",
        "1.9",
        8,
        "2 to 4",
    ),
    (
        "What credit-hour range is normally assigned to a lab or workshop?",
        "1.10",
        8,
        "1 or 2",
    ),
    (
        "How many weekly practical hours correspond to one lab credit hour?",
        "1.11",
        8,
        "3",
    ),
    ("What does the (3+1) credit-hour designation mean?", "1.12", 8, "theory"),
    (
        "Which office communicates the class timetable to students?",
        "1.13",
        8,
        "Academic Office",
    ),
    (
        "Who must approve class rescheduling, and may faculty reschedule on their own?",
        "1.14",
        8,
        "Head",
    ),
    ("What minimum cumulative GPA is required to graduate?", "1.25", 10, "2.00"),
]
HARD = [
    (
        "Does a one-credit lab require the same weekly contact time as a one-credit theory course?",
        [("1.7", 7), ("1.11", 8)],
        "3",
    ),
    (
        "Can a lecturer independently move a cancelled class if students agree?",
        [("1.14", 8)],
        "Academic Office",
    ),
    (
        "Is permitted absence an automatic entitlement, or does it require a genuine reason and approval?",
        [("1.21", 10)],
        "HoD",
    ),
    (
        "What happens to final-exam eligibility and the course grade when attendance is insufficient?",
        [("1.22", 10)],
        "F/A",
    ),
    (
        "How do the ordinary maximum degree duration and a possible further extension differ?",
        [("1.23", 10)],
        "6",
    ),
]
OUTSIDE = [
    "How do I configure campus Wi-Fi on an Android phone?",
    "How do I reset my campus Wi-Fi password?",
    "Which DNS server should my home router use?",
    "How do I replace a laptop battery?",
    "What is the forecast for tomorrow in Islamabad?",
    "How do I cook a vegetable curry?",
    "Which engine oil does my car require?",
    "How do I configure a Kubernetes ingress certificate?",
    "How do I restore deleted photographs from my phone?",
    "What are the rules of a chess tournament?",
    "How do I configure two-factor authentication for my personal email?",
    "What are the entry requirements for a tourist visa to Japan?",
]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
        encoding="utf-8",
    )


def main() -> None:
    targets = [
        ROOT / "eval" / name
        for name in (
            "golden.synthetic-draft.jsonl",
            "live_queries.jsonl",
            "coverage-expansion-candidates.jsonl",
        )
    ]
    if any(p.exists() for p in targets):
        raise SystemExit(
            "Refusing to overwrite existing draft or user data; use a separate scratch checkout."
        )
    raw = ROOT / "corpus/raw" / SOURCE
    if not raw.is_file():
        raise SystemExit(
            "Fetch the selected corpus first; no source availability is invented."
        )
    sha = hashlib.sha256(raw.read_bytes()).hexdigest()
    if sha != EXPECTED_SOURCE_SHA256:
        raise SystemExit(
            "Source PDF changed: inspect physical pages and update labels before generating drafts."
        )
    rows = []
    for question, section, page, expect in ORDINARY:
        rows.append(
            {
                "question": question,
                "kind": "answerable",
                "hard_reason": None,
                "relevant": [{"source": SOURCE, "section": section, "page": page}],
                "expect": expect,
            }
        )
    for question, labels, expect in HARD:
        rows.append(
            {
                "question": question,
                "kind": "hard",
                "hard_reason": "paraphrase",
                "relevant": [
                    {"source": SOURCE, "section": s, "page": p} for s, p in labels
                ],
                "expect": expect,
            }
        )
    for question in OUTSIDE[:5]:
        rows.append(
            {
                "question": question,
                "kind": "unanswerable",
                "hard_reason": None,
                "relevant": [],
                "expect": None,
            }
        )
    for i, row in enumerate(rows, 1):
        row.update(
            id=f"draft-{i:02}",
            origin="synthetic",
            reviewed=False,
            source_sha256=sha,
            label_method="automated source/visual inspection; human review pending",
        )
    write_jsonl(ROOT / "eval/golden.synthetic-draft.jsonl", rows)
    questions = [
        "Is my Islamiat paper necessarily written in English?",
        "Do Fall classes begin around August or January?",
        "When does Spring normally wrap up?",
        "Are final exam weeks included in the sixteen teaching weeks?",
        "My timetable says one theory credit. How much contact time is that?",
        "Does a lab credit usually take three contact hours?",
        "Who can approve moving a cancelled lecture?",
        "Can a teacher change our timetable without the academic office?",
        "What does a course listed as three plus one mean?",
        "How much absence may the department excuse if I am ill?",
        "Could lack of attendance stop me sitting the final?",
        "Can a 1.9 cumulative GPA satisfy graduation?",
        "How many regular semesters is a bachelor degree planned for?",
        "Who can authorize extending a degree after six years?",
        "I cleared theory but failed the lab. Must I retake theory again?",
        "Theory and lab are linked but only theory failed. What must I retake?",
        "Can I sign up for a course while its prerequisite is still failed?",
        "How many lab courses can I resit during the summer?",
        "What cumulative GPA leads to an academic warning?",
        "I need to leave a course. How late may I withdraw under the 2026 rules?",
        "Did the withdrawal cutoff differ in the 2023 handbook?",
        "Can I adjust registration after the first week of term?",
        "Is semester GPA the same as cumulative GPA?",
        "What do the letter grades FA and W mean?",
        "Which office publishes our official class schedule?",
        "Where do the rules describe acceptable use of generative AI?",
        "How are academic dishonesty violations handled?",
        "What are the ordinary credit ranges for theory classes and labs?",
    ]
    live = [
        {
            "id": f"live-{i:02}",
            "query": q,
            "origin": "synthetic",
            "expected_topic": "academic policy",
            "intended_domain": "in_domain",
        }
        for i, q in enumerate(questions, 1)
    ]
    live += [
        {
            "id": f"live-{i + 29:02}",
            "query": q,
            "origin": "synthetic",
            "expected_topic": "outside selected academic corpus",
            "intended_domain": "uncovered",
        }
        for i, q in enumerate(
            [
                "My Android phone cannot join campus Wi-Fi; which settings should I enter?",
                "Where is the IT portal option for a forgotten wireless-network password?",
                "Which DNS address belongs in my home router configuration?",
                "What are the safe steps for replacing my laptop battery?",
                "Will it rain in Islamabad tomorrow?",
                "Can you give me a vegetable curry recipe?",
                "Which viscosity of engine oil should I buy for my car?",
                "How can I install an HTTPS certificate in Kubernetes Ingress?",
                "Can I recover photos I deleted from my mobile phone?",
                "How are tie-breaks calculated in chess tournaments?",
                "How can I enable two-factor login on my private email account?",
                "Which documents do I need for a Japanese tourist visa?",
            ]
        )
    ]
    if (ROOT / "eval/live_queries.jsonl").exists():
        raise SystemExit(
            "Preserve existing live_queries.jsonl; review this generator before replacing user work."
        )
    write_jsonl(ROOT / "eval/live_queries.jsonl", live)
    # Candidates only: actual E2 results must select real uncovered topics before E4.
    write_jsonl(
        ROOT / "eval/coverage-expansion-candidates.jsonl",
        [
            {
                "id": f"expansion-{i + 1:02}",
                "question": q,
                "origin": "synthetic",
                "reviewed": False,
                "kind": "unanswerable",
                "relevant": [],
                "expect": None,
                "status": "candidate only; select after real coverage analysis",
            }
            for i, q in enumerate(OUTSIDE[5:11])
        ],
    )
    print(
        "Prepared 25 synthetic golden drafts, 40 synthetic user-style queries (28/12), 6 expansion candidates."
    )
    print("No human provenance, measured coverage or final golden pass is claimed.")


if __name__ == "__main__":
    main()
