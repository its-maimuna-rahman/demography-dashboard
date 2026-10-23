"""Smoke tests: every page renders without an exception or an st.error, with default and alternative bundled data."""
import glob
import os
from pathlib import Path

import pytest

st_testing = pytest.importorskip("streamlit.testing.v1")
ROOT = Path(__file__).resolve().parent.parent
PAGES = ["home.py"] + sorted(glob.glob(str(ROOT / "pages" / "*.py")), key=lambda p: int(Path(p).name.split("_")[0]))


def _run(path):
    full = path if os.path.isabs(path) else str(ROOT / path)
    return st_testing.AppTest.from_file(full, default_timeout=180).run()


@pytest.mark.parametrize("path", PAGES)
def test_page_renders(path):
    at = _run(path)
    assert not at.exception, [str(e.value) for e in at.exception]
    assert not at.error, [str(e.value) for e in at.error]


@pytest.mark.parametrize("path", [p for p in PAGES if "pages" in p])
def test_page_renders_with_every_bundled_dataset(path):
    at = _run(path)
    preset = [s for s in at.selectbox if s.key and s.key.endswith("_preset")]
    if not preset:
        pytest.skip("page has no dataset selector")
    for opt in preset[0].options:
        at = _run(path)
        [s for s in at.selectbox if s.key == preset[0].key][0].select(opt).run()
        assert not at.exception, (opt, [str(e.value) for e in at.exception])
        assert not at.error, (opt, [str(e.value) for e in at.error])


def test_navigation_entrypoint_loads():
    at = _run("app.py")
    assert not at.exception


def test_page_files_have_no_emoji():
    for p in PAGES:
        assert Path(p).name.isascii()
