import hashlib

from laya_harness import codex_resources as resources


def test_catalog_exact_recommendation_subset():
    rows = resources.catalog()["models"]
    expected = [
        ("gpt-6-luna", "GPT-6 Luna", "luna", "6", 0.1, 0.5, False),
        ("gpt-6.1-sol", "GPT-6.1 Sol", "sol", "6.1", 2, 10, True),
        ("gpt-6-astra", "GPT-6 Astra", "astra", "6", 10, 50, True),
    ]
    assert len(rows) == 3
    for row, (model, display, family, version, price_in, price_out, ultra) in zip(rows, expected):
        assert row == {"id": model, "display": display, "family": family, "version": version,
                       "price": {"input": price_in, "output": price_out}, "in_picker": True,
                       "allowed": True, "effort_levels": ["low", "medium", "high", "xhigh", "max"] + (["ultra"] if ultra else [])}
    assert "2026-10-10" in resources.catalog()["source"]


def test_fit_exact_provisional_options():
    assert resources.fit()["classes"] == {
        "quick": [{"family": "luna", "effort": "low"}, {"family": "sol", "effort": "low"}],
        "routine": [{"family": "sol", "effort": "medium"}],
        "multi_file": [{"family": "sol", "effort": "high"}],
        "architecture": [{"family": "astra", "effort": "xhigh"}],
    }


def test_hash_includes_both_raw_files(tmp_path, monkeypatch):
    before = resources.catalog_sha256()
    assert before == hashlib.sha256(resources.CATALOG.read_bytes() + resources.FIT.read_bytes()).hexdigest()
    for attr in ("CATALOG", "FIT"):
        with monkeypatch.context() as change:
            edited = tmp_path / attr
            edited.write_bytes(getattr(resources, attr).read_bytes() + b' ')
            change.setattr(resources, attr, edited)
            assert resources.catalog_sha256() != before
