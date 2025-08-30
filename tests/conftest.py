"""
Pytest configuration and shared fixtures for SCLI tests
"""

import pytest
from typer.testing import CliRunner
from unittest.mock import Mock


@pytest.fixture
def cli_runner():
    """Fixture para testing de comandos CLI con typer."""
    return CliRunner()


@pytest.fixture
def mock_console():
    """Fixture para mock del console de rich."""
    return Mock()


@pytest.fixture
def sample_args():
    """Fixture con argumentos de ejemplo para testing."""
    return ["--help"]


@pytest.fixture
def empty_args():
    """Fixture con argumentos vacíos para testing."""
    return []