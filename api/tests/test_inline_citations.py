from app.schemas import Citation
from app.services.citations import inline_problem

C = Citation(source="handbook.pdf", section="1.21", page=7)


def test_every_sentence_requires_attribution_and_decimals_are_not_boundaries():
    assert inline_problem("CGPA is 2.00 [handbook.pdf / 1.21].", [C]) is None
    assert inline_problem("Required. [handbook.pdf / 1.21]", [C]) is None
    assert inline_problem("Required [handbook.pdf / 1.21]. Another unsupported claim.", [C])
    assert inline_problem("Required [invented.pdf / 1.21].", [C])
    assert inline_problem("No citation.", [C])
