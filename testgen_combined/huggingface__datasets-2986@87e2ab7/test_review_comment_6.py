import re


def _get_class_block(source: str, class_name: str) -> str:
    # Extract "class <class_name> ...:" block up to the next top-level "class " or EOF
    m = re.search(rf"^class\s+{re.escape(class_name)}\b.*?:\n", source, flags=re.M)
    assert m, f"Could not find class {class_name} definition in /workspace/src/datasets/data_files.py"
    start = m.start()
    m2 = re.search(r"^class\s+\w+\b.*?:\n", source[m.end() :], flags=re.M)
    end = (m.end() + m2.start()) if m2 else len(source)
    return source[start:end]


def test_datafileslist_constructors_use_classmethod_and_return_cls():
    source = open("/workspace/src/datasets/data_files.py", "r", encoding="utf-8").read()
    block = _get_class_block(source, "DataFilesList")

    # Ensure the constructors are classmethods (subclass-friendly)
    assert (
        re.search(r"^\s+@classmethod\s*\n\s+def\s+from_hf_repo\b", block, flags=re.M) is not None
    ), "Expected DataFilesList.from_hf_repo to be decorated with @classmethod (not @staticmethod)."

    assert (
        re.search(r"^\s+@classmethod\s*\n\s+def\s+from_local_or_remote\b", block, flags=re.M) is not None
    ), "Expected DataFilesList.from_local_or_remote to be decorated with @classmethod (not @staticmethod)."

    # Ensure they return cls(...) (not hard-coded DataFilesList(...))
    assert (
        re.search(r"^\s+return\s+cls\(\s*data_files\s*,\s*origin_metadata\s*\)", block, flags=re.M) is not None
    ), "Expected DataFilesList constructors to return cls(data_files, origin_metadata) to support subclassing."

    assert (
        re.search(r"^\s+return\s+DataFilesList\(", block, flags=re.M) is None
    ), "Did not expect DataFilesList constructors to hard-code DataFilesList(...); they should return cls(...)."