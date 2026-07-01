import pytest

import scripts.surface_high_engagement_issues as mod


def test_get_issue_id_no_keyerror_when_graphql_response_missing_data(monkeypatch):
    """
    Before: get_issue_id() raises KeyError when GraphQL JSON lacks "data".
    After: get_issue_id() no longer raises KeyError in this scenario (it may still
    raise a different exception due to current implementation details).
    """

    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            # Simulate an unexpected GraphQL response shape (no "data" key)
            return {"message": "something went wrong"}

    def fake_post(url, headers=None, json=None):
        return DummyResponse()

    monkeypatch.setattr(mod.httpx, "post", fake_post)

    # The key behavior change: do not crash with KeyError on missing "data"
    with pytest.raises(Exception) as excinfo:
        mod.get_issue_id(123, headers={"Authorization": "Bearer x"})

    assert not isinstance(excinfo.value, KeyError), (
        "get_issue_id() should not raise KeyError when the GraphQL response is missing "
        "the 'data' key; it should handle/report the unexpected response instead."
    )