from sqlglot import exp
from sqlglot.generator import Generator


def test_describe_sql_partition_uses_keyed_sql_generation_not_self_sql_on_node():
    """
    The change in the diff is specifically:
      BEFORE: partition = expression.args.get("partition"); self.sql(partition)
      AFTER:  partition = self.sql(expression, "partition")  (keyed lookup)

    These two are NOT equivalent when the partition node is an exp.Partition, because:
      - exp.Partition SQL is "PARTITION(...)" (via Generator.partition_sql / key dispatch)
      - calling Generator.sql(exp.Partition) without a key returns its TRANSFORM output,
        which is exp.PartitionedByProperty (a different "PARTITIONED BY ..." construct)

    So: exp.Describe(partition=exp.Partition([...])) must render "PARTITION(...)".
    This FAILS on the before code (it incorrectly renders "PARTITIONED BY ..."),
    and PASSES on the after code.
    """
    g = Generator(pretty=False)

    describe = exp.Describe(
        this=exp.to_identifier("t"),
        partition=exp.Partition(expressions=[exp.Literal.number(1)]),
    )

    sql = g.generate(describe)

    assert (
        sql == "DESCRIBE t PARTITION(1)"
    ), (
        "Generator.describe_sql must render Describe.partition using Generator.sql(expression, 'partition') "
        "so that exp.Partition is generated as PARTITION(...). "
        "If it instead calls self.sql(partition_node) directly, exp.Partition is incorrectly transformed "
        "as a property (e.g., PARTITIONED BY ...). "
        f"Got: {sql!r}"
    )