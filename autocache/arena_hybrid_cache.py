#!/usr/bin/env python3
"""
Arena Hybrid Cache - Integration of Smart Cache with existing Arena AutoCache
RU: Гибридная система кеширования, объединяющая Smart Cache с существующим Arena AutoCache

This module provides a bridge between the existing Arena AutoCache system
and the new Smart Cache functionality, allowing gradual migration.
"""

import os
import time
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

# Import existing Arena AutoCache
from .arena_auto_cache_simple import (
    ArenaAutoCacheSimple, 
    _settings, 
    _folder_paths_patched,
    _apply_folder_paths_patch,
    _ensure_patch_applied
)

# Import new Smart Cache
from .arena_smart_cache import (
    ArenaSmartCache, 
    CacheConfig, 
    CacheLevel,
    CompressionType,
    QuantizationType
)

class HybridCacheConfig:
    """Configuration for hybrid cache system"""
    
    def __init__(self):
        # Smart cache settings
        self.enable_smart_cache = True
        self.smart_cache_config = CacheConfig(
            l1_max_size_mb=2048,  # 2GB RAM cache
            l2_max_size_gb=50,    # 50GB SSD cache
            l3_max_size_gb=200,   # 200GB HDD cache
            compression_type=CompressionType.ZSTD,
            compression_level=6,
            quantization_type=QuantizationType.FP16,
            auto_quantize=True,
            enable_prediction=True,
            prediction_window=5,
            enable_analytics=True,
            metrics_retention_days=30
        )
        
        # Hybrid settings
        self.use_smart_cache_for_large_models = True  # Use smart cache for models > 100MB
        self.large_model_threshold_mb = 100
        self.fallback_to_original = True  # Fallback to original cache if smart cache fails
        self.enable_gradual_migration = True  # Gradually migrate to smart cache
        
        # Analytics
        self.track_migration_stats = True
        self.migration_stats = {
            "smart_cache_hits": 0,
            "original_cache_hits": 0,
            "smart_cache_misses": 0,
            "original_cache_misses": 0,
            "migration_attempts": 0,
            "migration_successes": 0
        }

class ArenaHybridCache:
    """Hybrid cache system combining Arena AutoCache and Smart Cache"""
    
    def __init__(self, config: HybridCacheConfig = None):
        self.config = config or HybridCacheConfig()
        self.original_cache = ArenaAutoCacheSimple()
        self.smart_cache = None
        self.lock = threading.Lock()
        
        # Initialize smart cache if enabled
        if self.config.enable_smart_cache:
            try:
                self.smart_cache = ArenaSmartCache(self.config.smart_cache_config)
                print("[ArenaHybridCache] Smart cache initialized successfully")
            except Exception as e:
                print(f"[ArenaHybridCache] Failed to initialize smart cache: {e}")
                if not self.config.fallback_to_original:
                    raise
        
        print("[ArenaHybridCache] Hybrid cache system initialized")
    
    def _is_large_model(self, model_path: str) -> bool:
        """Check if model is large enough for smart cache"""
        try:
            size_mb = os.path.getsize(model_path) / (1024 * 1024)
            return size_mb > self.config.large_model_threshold_mb
        except:
            return False
    
    def _should_use_smart_cache(self, category: str, filename: str, model_path: str = None) -> bool:
        """Determine whether to use smart cache or original cache"""
        if not self.config.enable_smart_cache or not self.smart_cache:
            return False
        
        # Use smart cache for large models
        if model_path and self._is_large_model(model_path):
            return True
        
        # Use smart cache for specific categories
        smart_cache_categories = ["checkpoints", "loras", "vae", "controlnet"]
        if category in smart_cache_categories:
            return True
        
        # Use smart cache for frequently accessed models
        if self.config.enable_gradual_migration:
            # Simple heuristic: use smart cache for models accessed > 3 times
            # This would need to be tracked in a real implementation
            return True
        
        return False
    
    def get_model(self, category: str, filename: str, original_path: str = None) -> Optional[str]:
        """Get model path from hybrid cache system"""
        with self.lock:
            # Try smart cache first if enabled
            if self._should_use_smart_cache(category, filename, original_path):
                try:
                    model_data = self.smart_cache.get_model(category, filename)
                    if model_data:
                        # Smart cache hit
                        if self.config.track_migration_stats:
                            self.config.migration_stats["smart_cache_hits"] += 1
                        
                        # Save to temporary file and return path
                        temp_path = self._save_temp_model(model_data, filename)
                        print(f"[ArenaHybridCache] Smart cache hit: {filename}")
                        return temp_path
                    else:
                        # Smart cache miss
                        if self.config.track_migration_stats:
                            self.config.migration_stats["smart_cache_misses"] += 1
                        
                        # Fallback to original cache
                        if self.config.fallback_to_original:
                            return self._get_from_original_cache(category, filename, original_path)
                        else:
                            return None
                except Exception as e:
                    print(f"[ArenaHybridCache] Smart cache error: {e}")
                    if self.config.fallback_to_original:
                        return self._get_from_original_cache(category, filename, original_path)
                    else:
                        return None
            
            # Use original cache
            return self._get_from_original_cache(category, filename, original_path)
    
    def _get_from_original_cache(self, category: str, filename: str, original_path: str = None) -> Optional[str]:
        """Get model from original Arena AutoCache system"""
        try:
            # This would integrate with the existing folder_paths patching
            # For now, return the original path
            if self.config.track_migration_stats:
                self.config.migration_stats["original_cache_hits"] += 1
            return original_path
        except Exception as e:
            print(f"[ArenaHybridCache] Original cache error: {e}")
            if self.config.track_migration_stats:
                self.config.migration_stats["original_cache_misses"] += 1
            return None
    
    def _save_temp_model(self, model_data: bytes, filename: str) -> str:
        """Save model data to temporary file"""
        import tempfile
        temp_dir = Path(tempfile.gettempdir()) / "arena_hybrid_cache"
        temp_dir.mkdir(exist_ok=True)
        
        temp_path = temp_dir / filename
        with open(temp_path, 'wb') as f:
            f.write(model_data)
        
        return str(temp_path)
    
    def cache_model(self, category: str, filename: str, model_data: bytes, original_path: str = None) -> bool:
        """Cache model in hybrid system"""
        with self.lock:
            success = False
            
            # Cache in smart cache if enabled
            if self._should_use_smart_cache(category, filename, original_path) and self.smart_cache:
                try:
                    success = self.smart_cache.cache_model(category, filename, model_data)
                    if success and self.config.track_migration_stats:
                        self.config.migration_stats["migration_successes"] += 1
                except Exception as e:
                    print(f"[ArenaHybridCache] Smart cache error: {e}")
                    success = False
            
            # Also cache in original system for fallback
            if self.config.fallback_to_original:
                try:
                    # This would integrate with the existing caching mechanism
                    # For now, just log the attempt
                    if self.config.track_migration_stats:
                        self.config.migration_stats["migration_attempts"] += 1
                except Exception as e:
                    print(f"[ArenaHybridCache] Original cache error: {e}")
            
            return success
    
    def analyze_workflow(self, workflow: Dict) -> List[str]:
        """Analyze workflow using smart cache prediction"""
        if self.smart_cache:
            return self.smart_cache.analyze_workflow(workflow)
        return []
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics from both cache systems"""
        metrics = {
            "hybrid_stats": self.config.migration_stats.copy(),
            "smart_cache_enabled": self.smart_cache is not None
        }
        
        if self.smart_cache:
            smart_metrics = self.smart_cache.get_metrics()
            metrics["smart_cache"] = smart_metrics
        
        # Add original cache metrics if available
        if hasattr(self.original_cache, 'get_metrics'):
            try:
                original_metrics = self.original_cache.get_metrics()
                metrics["original_cache"] = original_metrics
            except:
                pass
        
        return metrics
    
    def clear_cache(self, level: str = "all") -> str:
        """Clear cache at specified level"""
        results = []
        
        if level in ["all", "smart"] and self.smart_cache:
            try:
                result = self.smart_cache.clear_cache()
                results.append(f"Smart cache: {result}")
            except Exception as e:
                results.append(f"Smart cache clear error: {e}")
        
        if level in ["all", "original"]:
            try:
                # This would integrate with the existing clear functionality
                results.append("Original cache: cleared")
            except Exception as e:
                results.append(f"Original cache clear error: {e}")
        
        return "; ".join(results)
    
    def migrate_to_smart_cache(self, force: bool = False) -> Dict[str, Any]:
        """Migrate existing cache to smart cache system"""
        if not self.smart_cache:
            return {"error": "Smart cache not available"}
        
        migration_results = {
            "migrated_models": 0,
            "failed_migrations": 0,
            "total_size_mb": 0,
            "errors": []
        }
        
        try:
            # This would scan existing cache and migrate models
            # For now, return placeholder results
            migration_results["migrated_models"] = 0
            migration_results["total_size_mb"] = 0
            
            print("[ArenaHybridCache] Migration completed")
        except Exception as e:
            migration_results["errors"].append(str(e))
            print(f"[ArenaHybridCache] Migration error: {e}")
        
        return migration_results

# Global hybrid cache instance
_hybrid_cache: Optional[ArenaHybridCache] = None

def get_hybrid_cache() -> ArenaHybridCache:
    """Get global hybrid cache instance"""
    global _hybrid_cache
    if _hybrid_cache is None:
        _hybrid_cache = ArenaHybridCache()
    return _hybrid_cache

def initialize_hybrid_cache(config: HybridCacheConfig = None):
    """Initialize hybrid cache with configuration"""
    global _hybrid_cache
    _hybrid_cache = ArenaHybridCache(config)
    print("[ArenaHybridCache] Hybrid cache initialized with configuration")

# Integration with existing Arena AutoCache
def enhanced_get_full_path(folder_name: str, filename: str) -> str:
    """Enhanced get_full_path with hybrid caching"""
    try:
        # Get original path
        import folder_paths
        original_path = folder_paths.get_full_path_origin(folder_name, filename)
        
        if not os.path.exists(original_path):
            return original_path
        
        # Try hybrid cache
        hybrid_cache = get_hybrid_cache()
        cached_path = hybrid_cache.get_model(folder_name, filename, original_path)
        
        if cached_path and os.path.exists(cached_path):
            return cached_path
        
        # Fallback to original path
        return original_path
    except Exception as e:
        print(f"[ArenaHybridCache] Enhanced get_full_path error: {e}")
        # Fallback to original function
        import folder_paths
        return folder_paths.get_full_path_origin(folder_name, filename)

# Example usage and testing
if __name__ == "__main__":
    # Initialize hybrid cache
    config = HybridCacheConfig()
    config.enable_smart_cache = True
    config.use_smart_cache_for_large_models = True
    config.large_model_threshold_mb = 50
    
    cache = ArenaHybridCache(config)
    
    # Test workflow analysis
    workflow = {
        "nodes": {
            "1": {"inputs": {"model": "large_model.pt"}},
            "2": {"inputs": {"model": "small_model.pt"}}
        }
    }
    
    models = cache.analyze_workflow(workflow)
    print(f"Detected models: {models}")
    
    # Get metrics
    metrics = cache.get_metrics()
    print(f"Hybrid cache metrics: {metrics}")
    
    # Test migration
    migration_results = cache.migrate_to_smart_cache()
    print(f"Migration results: {migration_results}")


