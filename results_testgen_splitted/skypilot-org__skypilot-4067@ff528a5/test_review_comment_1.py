import os
import tempfile

import pytest

import sky.utils.dag_utils as dag_utils


def _write_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def test_load_dag_from_yaml_empty_file_error_is_wrapped_by_ux_utils():
    # Create a truly empty YAML file so common_utils.read_yaml_all() returns []
    # and load_dag_from_yaml() triggers its "Empty YAML file." ValueError branch.
    fd, path = tempfile.mkstemp(suffix=".yaml")
    os.close(fd)
    try:
        _write_file(path, "")

        with pytest.raises(ValueError) as e:
            dag_utils.load_dag_from_yaml(path)

        assert "Empty YAML file" in str(e.value), (
            "Expected load_dag_from_yaml() to raise ValueError('Empty YAML file.') "
            "for an empty YAML file."
        )

        # Review comment asks to add ux_utils.print_exception_no_traceback() to
        # these errors. In the fixed code, the error is raised inside the context
        # manager; thus ux_utils.__exit__ appears in the exception traceback.
        tb = e.value.__traceback__
        found_ux_exit = False
        while tb is not None:
            code = tb.tb_frame.f_code
            if code.co_name == "__exit__" and "ux_utils" in code.co_filename:
                found_ux_exit = True
                break
            tb = tb.tb_next

        assert found_ux_exit, (
            "Expected the ValueError to be raised under ux_utils.print_exception_no_traceback() "
            "(i.e., ux_utils.__exit__ should appear in the traceback)."
        )
    finally:
        os.remove(path)