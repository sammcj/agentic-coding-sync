"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def tmp_path(tmp_path_factory):
    """Create a temporary directory for testing."""
    return tmp_path_factory.mktemp("test")
