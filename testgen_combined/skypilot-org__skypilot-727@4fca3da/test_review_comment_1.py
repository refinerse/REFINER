def test_exec_doc_examples_do_not_use_double_dash_separator_anymore():
    """The exec() help examples should show direct command passing.

    After the change, the documented usage is:
      sky exec mycluster python train_cpu.py
    (i.e., no '--' separator). Before the change, it still showed:
      sky exec mycluster -- python train.py
    """
    source = open('/workspace/sky/cli.py', 'r', encoding='utf-8').read()

    assert 'sky exec mycluster python train_cpu.py' in source, (
        "Expected the updated sky exec documentation example to be present: "
        "`sky exec mycluster python train_cpu.py`."
    )

    assert 'sky exec mycluster -- python train.py' not in source, (
        "Did not expect the old sky exec documentation example with a '--' "
        "separator to remain: `sky exec mycluster -- python train.py`."
    )