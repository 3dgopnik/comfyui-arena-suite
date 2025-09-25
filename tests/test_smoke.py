def test_smoke_version():
    try:
        from custom_nodes.ComfyUI_Arena import VERSION
    except Exception as exc:  # pragma: no cover
        raise AssertionError(f"Import failed: {exc}")
    assert isinstance(VERSION, str) and len(VERSION) > 0