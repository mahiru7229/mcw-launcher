from pathlib import Path

import pytest

from src.core.java.java_provisioner import JavaProvisioner
from src.core.java.java_resolver import JavaResolver
from src.core.java.java_selector import JavaSelector


def test_resolve_returns_selected_java_without_provisioning(monkeypatch: pytest.MonkeyPatch):
    selected = Path("java21/javaw.exe")
    provision_calls = []

    monkeypatch.setattr(JavaSelector, "select_java", lambda major: selected)
    monkeypatch.setattr(JavaProvisioner, "ensure", lambda major, reporter=None: provision_calls.append((major, reporter)))

    result = JavaResolver.resolve(21)

    assert result == selected
    assert provision_calls == []


def test_resolve_provisions_java_when_selection_fails(monkeypatch: pytest.MonkeyPatch):
    installed = Path("runtimes/java-25/bin/javaw.exe")
    reporter = object()
    calls = []

    def fail_selection(major):
        calls.append(("select", major))
        raise RuntimeError("Java 21 was not found.")

    def provision(major, received_reporter=None):
        calls.append(("provision", major, received_reporter))
        return installed

    monkeypatch.setattr(JavaSelector, "select_java", fail_selection)
    monkeypatch.setattr(JavaProvisioner, "ensure", provision)

    result = JavaResolver.resolve(21, reporter)

    assert result == installed
    assert calls == [("select", 21), ("provision", 21, reporter)]
