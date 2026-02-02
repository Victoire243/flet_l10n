"""Tests configuration and fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory for testing."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def sample_arb_content():
    """Sample ARB file content for testing."""
    return {
        "@@locale": "en",
        "appTitle": "Test App",
        "@appTitle": {"description": "The title of the test application"},
        "welcome": "Welcome, {name}!",
        "@welcome": {
            "description": "Welcome message",
            "placeholders": {"name": {"type": "String"}},
        },
        "itemCount": "{count, plural, =0{No items} one{One item} other{{count} items}}",
        "@itemCount": {
            "description": "Item count with pluralization",
            "placeholders": {"count": {"type": "int"}},
        },
    }
