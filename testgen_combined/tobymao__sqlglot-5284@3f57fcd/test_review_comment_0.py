import inspect

from sqlglot.dialects.databricks import Databricks
from sqlglot.dialects.dialect import groupconcat_sql
from sqlglot import exp


def test_databricks_generator_uses_groupconcat_sql_transform_directly():
    """
    The Databricks generator should map exp.GroupConcat directly to the shared
    groupconcat_sql transform function (not wrap it in a lambda).
    """
    transform = Databricks.Generator.TRANSFORMS.get(exp.GroupConcat)

    assert (
        transform is groupconcat_sql
    ), "Databricks.Generator.TRANSFORMS[exp.GroupConcat] should be the groupconcat_sql function object"

    # Extra guard to ensure it's not an equivalent wrapper (e.g., lambda self,e: groupconcat_sql(self,e))
    assert (
        not inspect.isfunction(transform) or transform.__name__ == "groupconcat_sql"
    ), "GroupConcat transform should not be a wrapper/lambda; it should be the named groupconcat_sql function"