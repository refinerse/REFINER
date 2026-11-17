import re


def test_bookmarks_widget_defines_base_queryset_once_and_reuses_it():
    source = open("/workspace/netbox/extras/dashboard/widgets.py", "r", encoding="utf-8").read()

    # The style change requested: define the base queryset once, then apply ordering.
    assert "user_bookmarks = Bookmark.objects.filter(user=request.user)" in source, (
        "BookmarksWidget.render() should define the base queryset once as "
        "`user_bookmarks = Bookmark.objects.filter(user=request.user)` and then apply ordering to it."
    )

    # Ensure subsequent ordering uses the base queryset variable rather than duplicating the filter call.
    assert "bookmarks = user_bookmarks.order_by(self.config['order_by'])" in source, (
        "BookmarksWidget.render() should apply `.order_by(...)` to the shared `user_bookmarks` queryset "
        "instead of repeating `Bookmark.objects.filter(user=request.user)`."
    )

    # Negative check: the old pattern repeats the filter call in multiple branches.
    assert "Bookmark.objects.filter(user=request.user).order_by(self.config['order_by'])" not in source, (
        "BookmarksWidget.render() should not repeat the base queryset expression "
        "`Bookmark.objects.filter(user=request.user).order_by(...)`; it should reuse `user_bookmarks`."
    )

    # Also ensure the alphabetical branch reuses the base queryset variable.
    assert re.search(r"sorted\(\s*user_bookmarks\s*,", source), (
        "Alphabetical sorting should operate on `user_bookmarks` (the shared base queryset), "
        "not on a duplicated `Bookmark.objects.filter(user=request.user)` expression."
    )