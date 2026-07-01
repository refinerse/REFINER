import os
import tempfile

from Tools.build import generate_opcode_h


def test_generated_intrinsics_header_ends_with_newline():
    # Generate the intrinsics header into a temp file.
    with tempfile.TemporaryDirectory() as td:
        opcode_py = "/workspace/Lib/opcode.py"
        out_opcode_h = os.path.join(td, "opcode.h")
        out_internal_h = os.path.join(td, "pycore_opcode.h")
        out_intrinsics_h = os.path.join(td, "pycore_intrinsics.h")

        generate_opcode_h.main(
            opcode_py,
            outfile=out_opcode_h,
            internaloutfile=out_internal_h,
            intrinsicoutfile=out_intrinsics_h,
        )

        with open(out_intrinsics_h, "rb") as f:
            data = f.read()

    # The review comment adds a missing newline after the final extern declaration.
    # Enforce that the generated file ends with '\n' to avoid concatenation issues
    # when included or appended to other generated content.
    assert data.endswith(b"\n"), (
        "Generated pycore_intrinsics.h must end with a newline; "
        "the last extern declaration should be followed by '\\n'."
    )