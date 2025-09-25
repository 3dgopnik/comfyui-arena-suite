from .arena_auto_cache_simple import ArenaAutoCache, NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
from dataclasses import dataclass
from pathlib import Path

@dataclass
class CacheSettings:
    cache_dir: Path

class ArenaAutoCacheSimple:
    """Simple wrapper for compatibility."""
    def __init__(self, settings: CacheSettings):
        self.settings = settings

__all__ = [
    "ArenaAutoCache",
    "ArenaAutoCacheSimple", 
    "CacheSettings",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]

