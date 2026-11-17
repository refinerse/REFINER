import re

SEARCHBAR_TEMPLATE_PATH = "/workspace/netbox/utilities/templates/search/searchbar.html"


def test_searchbar_populates_value_from_query_param():
    """
    The search bar should render the current query in the input's `value` attribute
    using proper escaping. It should not rely on autofocus/onfocus JS to populate it.
    """
    source = open(SEARCHBAR_TEMPLATE_PATH, encoding="utf-8").read()

    # Must render value from request.GET.q (escaped) directly in the HTML attribute
    assert (
        'value="{{ request.GET.q|escape }}"' in source
    ), "Search input must render the query directly via value=\"{{ request.GET.q|escape }}\" so it is populated on page load."

    # Must not leave value empty (which requires JS/onfocus to populate later)
    assert (
        'value=""' not in source
    ), 'Search input must not have an empty value="" attribute; it should be populated from request.GET.q.'

    # Must not use onfocus JS to set the value (cursor/UX workaround moved elsewhere)
    assert (
        "onfocus=" not in source
    ), "Search input must not rely on an onfocus handler to set the value; it should be rendered directly in the template."