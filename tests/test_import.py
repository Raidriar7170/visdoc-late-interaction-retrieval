"""Smoke tests for the Phase 0 package skeleton."""

from importlib import import_module


def test_package_imports_without_external_resources() -> None:
    """The package imports without data, network, GPU, or model setup."""
    module = import_module("visdoc_retrieve")

    assert module.__version__ == "0.0.0"
