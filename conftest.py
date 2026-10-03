"""Provide unittest-style assertions to plain pytest test classes."""


def _assert_is_not_none(self, value, msg=None):
    assert value is not None, msg or "expected a non-None result"


def pytest_collection_modifyitems(items):
    for item in items:
        cls = getattr(item, "cls", None)
        if cls is not None and not hasattr(cls, "assertIsNotNone"):
            cls.assertIsNotNone = _assert_is_not_none
