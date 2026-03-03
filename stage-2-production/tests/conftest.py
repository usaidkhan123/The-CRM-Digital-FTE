"""
Shared pytest configuration and fixtures.
"""

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")


def pytest_collection_modifyitems(config, items):
    """Auto-mark end-to-end tests as slow."""
    for item in items:
        if "end_to_end" in item.nodeid:
            item.add_marker(pytest.mark.slow)
