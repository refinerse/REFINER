import pytest

from frappe.database.query import func_is
from frappe.query_builder import Field


def test_func_is_accepts_string_key_and_returns_criterion():
	"""
	Regression test for `("is", "set")` / `("is", "not set")` filters passed with string keys.

	Before fix: func_is("name", "set") raised AttributeError because "name" is a str.
	After fix: func_is wraps the key with Field(key) and returns a Criterion-like object.
	"""
	# Ensure the key is a plain string (this matches how dict_query passes it in)
	key = "name"

	# It should not raise, and should produce a query-builder object (Criterion)
	try:
		crit_set = func_is(key, "set")
		crit_not_set = func_is(key, "not set")
	except AttributeError as e:
		pytest.fail(
			"func_is must accept string fieldnames (e.g. 'name') without raising; "
			"it should internally wrap the key with Field(key). "
			f"Raised: {e!r}"
		)

	# Sanity: result should behave like a query-builder criterion (must have get_sql)
	assert hasattr(
		crit_set, "get_sql"
	), "func_is('name','set') should return a query-builder criterion object with .get_sql()."
	assert hasattr(
		crit_not_set, "get_sql"
	), "func_is('name','not set') should return a query-builder criterion object with .get_sql()."

	# Stronger check: output SQL should match what Field('name').isnotnull()/isnull() produce.
	assert (
		crit_set.get_sql() == Field(key).isnotnull().get_sql()
	), "func_is('name','set') should be equivalent to Field('name').isnotnull()."
	assert (
		crit_not_set.get_sql() == Field(key).isnull().get_sql()
	), "func_is('name','not set') should be equivalent to Field('name').isnull()."