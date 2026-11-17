import inspect

import Tools.build.generate_opcode_h as gen


def test_intrinsic_footer_variable_exists_and_is_used_in_main():
    # Style requirement: move the intrinsic footer text into a module-level variable,
    # analogous to the header, and have main() write that variable.
    assert hasattr(gen, "intrinsic_footer"), (
        "Expected module-level variable 'intrinsic_footer' to exist, so the intrinsic "
        "footer text isn't assembled via many nobj.write(...) calls inside main()."
    )

    src = inspect.getsource(gen.main)
    assert "nobj.write(intrinsic_footer)" in src, (
        "Expected main() to write the footer via nobj.write(intrinsic_footer). "
        "This confirms the footer was moved to a variable and is used consistently."
    )