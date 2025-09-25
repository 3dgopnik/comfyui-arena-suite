from pathlib import Path

from custom_nodes.ComfyUI_Arena.autocache import ArenaAutoCacheSimple, CacheSettings


def test_place_creates_target(tmp_path: Path):
    settings = CacheSettings(cache_dir=tmp_path / "cache")
    ac = ArenaAutoCacheSimple(settings)

    src = tmp_path / "models" / "foo.bin"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.touch()

    out = ac.place(src, subdir="text-encoders")
    assert out.exists()
    assert out.parent.name == "text-encoders"