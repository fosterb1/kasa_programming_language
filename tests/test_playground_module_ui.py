"""Hosting-neutral playground experimental-module UI contract regression."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_experimental_module_control_and_help_are_explicit():
    html = (ROOT / "playground/index.html").read_text(encoding="utf-8")
    assert 'id="experimental-modules"' in html
    assert 'type="checkbox"' in html
    assert 'aria-describedby="module-experiment-help"' in html
    assert 'value="moduleMarket"' in html
    assert "provisional pending community language review" in html


def test_ui_sends_opt_in_flag_to_worker_and_preserves_normal_mode():
    js = (ROOT / "playground/app.js").read_text(encoding="utf-8")
    assert 'const experimentalModulesInput = $("experimental-modules");' in js
    assert 'experimentalModulesInput.checked = exampleSelect.value === "moduleMarket";' in js
    assert 'experimentalModulesInput.checked = false;' in js
    assert 'const experimentalModules = experimentalModulesInput.checked;' in js
    assert 'experimentalModules ? "javascript" : engineSelect.value' in js
    assert 'engine, experimentalModules });' in js
    assert 'fa math firi stdlib: m' in js and 'kasa_sum(nneɛma)' in js


def test_worker_only_accepts_explicit_true_and_fails_without_package():
    js = (ROOT / "playground/worker.js").read_text(encoding="utf-8")
    assert 'experimentalModules === true' in js
    assert 'KASA_HAS_PINNED_MODULES = false;' in js
    assert 'experimentalModules: modules' in js
    assert 'This deployment has no pinned Kasa module bundle' in js
    assert 'engine === "native"' in js


def test_no_hosting_provider_added_to_new_module_ui():
    html = (ROOT / "playground/index.html").read_text(encoding="utf-8")
    assert "Netlify" not in html
