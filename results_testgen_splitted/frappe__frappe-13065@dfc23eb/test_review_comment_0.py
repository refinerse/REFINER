import types

import frappe
import frappe.api


class _Req:
	def __init__(self, path="/api/resource/Test", method="GET"):
		self.path = path
		self.method = method
		self.url = "http://localhost" + path
		self.headers = {}
		self.content_type = None

	def get_data(self):
		return b""


def test_api_resource_get_does_not_convert_arbitrary_params_to_bool(monkeypatch):
	"""
	When hitting GET /api/resource/<doctype>, only specific params (as_dict, debug)
	should be converted using sbool. Arbitrary params like "order_by" must not be
	converted, otherwise values such as "true"/"false"/"y"/"n" become booleans.
	"""

	# Ensure frappe.local exists even without full frappe app initialization.
	if not hasattr(frappe, "local") or frappe.local is None:
		frappe.local = types.SimpleNamespace()

	class FormDict(dict):
		__getattr__ = dict.get
		__setattr__ = dict.__setitem__

	frappe.local.request = _Req(path="/api/resource/Test", method="GET")
	frappe.request = frappe.local.request  # api.handle uses frappe.request.path
	frappe.local.response = {}
	frappe.local.form_dict = FormDict(
		{
			"order_by": "true",  # must remain string
			"debug": "1",  # allowed bool conversion
			"as_dict": "0",  # allowed bool conversion
		}
	)

	# Intercept frappe.call to avoid DB and to inspect the kwargs passed to get_list.
	captured = {}

	def _fake_call(fn, doctype, **kwargs):
		captured["doctype"] = doctype
		captured["kwargs"] = kwargs
		return []

	monkeypatch.setattr(frappe, "call", _fake_call, raising=True)

	# build_response("json") requires a response object; stub it to avoid framework setup.
	monkeypatch.setattr(frappe.api, "build_response", lambda _fmt: frappe.local.response, raising=True)

	# Execute handler.
	frappe.api.handle()

	assert "kwargs" in captured, "Expected GET /api/resource/<doctype> to call frappe.call(..., **form_dict)"

	assert captured["kwargs"]["order_by"] == "true", (
		"frappe.api.handle() must not apply sbool conversion to arbitrary GET list parameters like 'order_by'. "
		"Only known boolean params (as_dict, debug) should be converted."
	)

	assert captured["kwargs"]["debug"] is True and isinstance(captured["kwargs"]["debug"], bool), (
		"Expected 'debug' query param to be converted to native bool via sbool"
	)
	assert captured["kwargs"]["as_dict"] is False and isinstance(captured["kwargs"]["as_dict"], bool), (
		"Expected 'as_dict' query param to be converted to native bool via sbool"
	)