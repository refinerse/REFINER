import re


FANCYSETS_PATH = "/workspace/sympy/sets/fancysets.py"


def test_complexregion_union_coerces_real_via_from_real_before_complexregion_logic():
    source = open(FANCYSETS_PATH, "r", encoding="utf-8").read()

    # Required API addition from the review: a public coercion helper.
    assert "def from_real" in source, (
        "Expected ComplexRegion.from_real to exist (review requested a clearer coercion "
        "mechanism rather than relying on internal representation)."
    )

    # Extract ComplexRegion class body (simple, robust-enough text search).
    m_cls = re.search(r"^class\s+ComplexRegion\b.*?:\n(?P<body>.*?)(?=^\s*class\s|\Z)", source, re.S | re.M)
    assert m_cls, "Could not locate ComplexRegion class in source."
    cls_body = m_cls.group("body")

    # Extract _union method body.
    m_union = re.search(r"^\s*def\s+_union\(self,\s*other\):\n(?P<body>.*?)(?=^\s*def\s|\Z)", cls_body, re.S | re.M)
    assert m_union, "Could not locate ComplexRegion._union method in source."
    union_body = m_union.group("body")

    # After-code behavior: real subsets are coerced via ComplexRegion.from_real(other)
    # before entering ComplexRegion-specific union handling.
    assert "ComplexRegion.from_real(other)" in union_body, (
        "Expected ComplexRegion._union to coerce real subsets using ComplexRegion.from_real(other)."
    )

    # Before-code anti-pattern: relies on internal representation (self.sets) with a subset check.
    assert "as_complex.is_subset(self.sets)" not in union_body, (
        "ComplexRegion._union should not rely on internal representation via "
        "`as_complex.is_subset(self.sets)`; it should coerce via from_real."
    )

    # Control-flow check: coercion should occur before checking `if other.is_ComplexRegion:`.
    pos_coerce = union_body.find("ComplexRegion.from_real(other)")
    pos_is_cr = union_body.find("if other.is_ComplexRegion")
    assert pos_is_cr != -1, "Expected `if other.is_ComplexRegion` inside ComplexRegion._union."
    assert pos_coerce < pos_is_cr, (
        "Expected ComplexRegion._union to coerce real subsets to ComplexRegion "
        "before checking `if other.is_ComplexRegion`."
    )