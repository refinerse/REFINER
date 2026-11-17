import re

import pytest


def test_jpeg_tests_freeze_rng_state_context_used():
    source = open("/workspace/test/test_transforms_v2.py").read()

    # We specifically check that the RNG-sensitive JPEG transform correctness test
    # is wrapped in `with freeze_rng_state():` to avoid leaking RNG state to other tests.
    #
    # This must be present in the "after" version and absent in the "before" version.
    pattern = re.compile(
        r"def test_transform_image_correctness\(self,\s*quality,\s*color_space,\s*seed\):"
        r".*?"
        r"with freeze_rng_state\(\):"
        r".*?"
        r"torch\.manual_seed\(seed\)"
        r".*?"
        r"actual\s*=\s*transform\(image\)"
        r".*?"
        r"torch\.manual_seed\(seed\)"
        r".*?"
        r"expected\s*=\s*F\.to_image\(transform\(F\.to_pil_image\(image\)\)\)",
        flags=re.DOTALL,
    )

    assert pattern.search(source), (
        "Expected TestJPEG.test_transform_image_correctness to wrap the manual seeding and transform calls in "
        "`with freeze_rng_state():` to prevent RNG state leakage to other tests."
    )


def test_jpeg_get_params_bounds_freeze_rng_state_context_used():
    source = open("/workspace/test/test_transforms_v2.py").read()

    # Same safety measure should be applied to the JPEG params sampling test.
    pattern = re.compile(
        r"def test_transform_get_params_bounds\(self,\s*quality,\s*seed\):"
        r".*?"
        r"with freeze_rng_state\(\):"
        r".*?"
        r"torch\.manual_seed\(seed\)"
        r".*?"
        r"params\s*=\s*transform\._get_params\(\[\]\)",
        flags=re.DOTALL,
    )

    assert pattern.search(source), (
        "Expected TestJPEG.test_transform_get_params_bounds to wrap manual seeding and `_get_params` in "
        "`with freeze_rng_state():` to prevent RNG state leakage to other tests."
    )