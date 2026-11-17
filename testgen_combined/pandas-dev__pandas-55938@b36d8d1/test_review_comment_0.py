def test_setitem_object_dtype_setup_does_not_overwrite_df_assignment():
    path = "/workspace/asv_bench/benchmarks/indexing.py"
    source = open(path, encoding="utf-8").read()

    cls_marker = "class SetitemObjectDtype:"
    assert cls_marker in source, "Expected SetitemObjectDtype benchmark class to exist in indexing.py"

    # Only inspect the SetitemObjectDtype class body, not the whole file (other
    # benchmarks legitimately create random float DataFrames with the same text).
    start = source.index(cls_marker)
    next_class = source.find("\nclass ", start + len(cls_marker))
    class_block = source[start:] if next_class == -1 else source[start:next_class]

    bad_line = "self.df = DataFrame(np.random.rand(N, cols))"
    assert (
        bad_line not in class_block
    ), "SetitemObjectDtype.setup() must not overwrite the object-dtype DataFrame with a float DataFrame"