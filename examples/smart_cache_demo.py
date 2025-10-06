#!/usr/bin/env python3
"""
Arena Smart Cache Demo - Demonstration of advanced caching capabilities
RU: Демонстрация возможностей продвинутого кеширования Arena Smart Cache

This script demonstrates the new smart caching features including:
- Multi-level caching
- Model compression and quantization
- Intelligent prediction
- Analytics and monitoring
- Hybrid cache integration
"""

import os
import time
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any

# Import smart cache components
import sys
sys.path.append(str(Path(__file__).parent.parent))

from autocache.arena_smart_cache import (
    ArenaSmartCache, 
    CacheConfig, 
    CacheLevel,
    CompressionType,
    QuantizationType
)
from autocache.arena_hybrid_cache import ArenaHybridCache, HybridCacheConfig

def create_demo_models():
    """Create demo model files for testing"""
    demo_dir = Path("demo_models")
    demo_dir.mkdir(exist_ok=True)
    
    # Create different sized model files
    models = {
        "small_model.pt": 1024 * 1024,      # 1MB
        "medium_model.pt": 50 * 1024 * 1024,  # 50MB
        "large_model.pt": 200 * 1024 * 1024,  # 200MB
        "huge_model.pt": 500 * 1024 * 1024,   # 500MB
    }
    
    for filename, size in models.items():
        file_path = demo_dir / filename
        with open(file_path, 'wb') as f:
            f.write(b'0' * size)
        print(f"Created {filename} ({size / 1024 / 1024:.1f}MB)")
    
    return demo_dir

def demo_basic_smart_cache():
    """Demonstrate basic smart cache functionality"""
    print("\n" + "="*60)
    print("DEMO: Basic Smart Cache Functionality")
    print("="*60)
    
    # Create demo models
    demo_dir = create_demo_models()
    
    # Configure smart cache
    config = CacheConfig(
        l1_max_size_mb=100,  # 100MB RAM cache
        l2_max_size_gb=1,     # 1GB SSD cache
        l3_max_size_gb=2,     # 2GB HDD cache
        compression_type=CompressionType.ZSTD,
        compression_level=6,
        quantization_type=QuantizationType.FP16,
        auto_quantize=True,
        enable_prediction=True,
        prediction_window=3,
        enable_analytics=True
    )
    
    # Initialize smart cache
    cache = ArenaSmartCache(config)
    
    # Test caching different sized models
    test_models = [
        ("checkpoints", "small_model.pt", demo_dir / "small_model.pt"),
        ("loras", "medium_model.pt", demo_dir / "medium_model.pt"),
        ("vae", "large_model.pt", demo_dir / "large_model.pt"),
        ("controlnet", "huge_model.pt", demo_dir / "huge_model.pt"),
    ]
    
    print("\n1. Testing model caching...")
    for category, filename, file_path in test_models:
        print(f"   Caching {category}/{filename}...")
        
        # Read model data
        with open(file_path, 'rb') as f:
            model_data = f.read()
        
        # Cache model
        success = cache.cache_model(category, filename, model_data)
        print(f"   {'✓' if success else '✗'} Cached {filename} ({len(model_data) / 1024 / 1024:.1f}MB)")
    
    # Test cache retrieval
    print("\n2. Testing cache retrieval...")
    for category, filename, _ in test_models:
        cached_data = cache.get_model(category, filename)
        if cached_data:
            print(f"   ✓ Retrieved {filename} from cache ({len(cached_data) / 1024 / 1024:.1f}MB)")
        else:
            print(f"   ✗ Failed to retrieve {filename}")
    
    # Get metrics
    print("\n3. Cache metrics:")
    metrics = cache.get_metrics()
    for key, value in metrics.items():
        print(f"   {key}: {value}")
    
    # Cleanup
    import shutil
    shutil.rmtree(demo_dir)
    
    return cache

def demo_workflow_analysis():
    """Demonstrate workflow analysis and prediction"""
    print("\n" + "="*60)
    print("DEMO: Workflow Analysis and Prediction")
    print("="*60)
    
    # Create sample workflows
    workflows = [
        {
            "id": "workflow_1",
            "nodes": {
                "1": {"inputs": {"model": "checkpoint1.pt"}},
                "2": {"inputs": {"model": "lora1.pt"}},
                "3": {"inputs": {"model": "vae1.pt"}}
            }
        },
        {
            "id": "workflow_2", 
            "nodes": {
                "1": {"inputs": {"model": "checkpoint1.pt"}},
                "2": {"inputs": {"model": "lora2.pt"}},
                "3": {"inputs": {"model": "controlnet1.pt"}}
            }
        },
        {
            "id": "workflow_3",
            "nodes": {
                "1": {"inputs": {"model": "checkpoint2.pt"}},
                "2": {"inputs": {"model": "lora1.pt"}},
                "3": {"inputs": {"model": "upscale1.pt"}}
            }
        }
    ]
    
    # Initialize cache
    config = CacheConfig(enable_prediction=True, prediction_window=3)
    cache = ArenaSmartCache(config)
    
    print("1. Analyzing workflows...")
    for i, workflow in enumerate(workflows, 1):
        models = cache.analyze_workflow(workflow)
        print(f"   Workflow {i}: {len(models)} models detected")
        print(f"   Models: {models}")
    
    print("\n2. Predicting next models...")
    current_models = ["checkpoint1.pt", "lora1.pt"]
    predicted = cache.cache.predict_and_preload(current_models)
    print(f"   Current models: {current_models}")
    print(f"   Predicted next: {predicted}")

def demo_compression_and_quantization():
    """Demonstrate compression and quantization features"""
    print("\n" + "="*60)
    print("DEMO: Compression and Quantization")
    print("="*60)
    
    # Create a large demo model
    demo_dir = Path("demo_compression")
    demo_dir.mkdir(exist_ok=True)
    
    large_model_path = demo_dir / "large_model.pt"
    model_size = 100 * 1024 * 1024  # 100MB
    with open(large_model_path, 'wb') as f:
        f.write(b'0' * model_size)
    
    print(f"Created demo model: {model_size / 1024 / 1024:.1f}MB")
    
    # Test different compression settings
    compression_configs = [
        (CompressionType.NONE, "No compression"),
        (CompressionType.GZIP, "GZIP compression"),
        (CompressionType.ZSTD, "ZSTD compression"),
    ]
    
    for compression_type, description in compression_configs:
        print(f"\n1. Testing {description}...")
        
        config = CacheConfig(
            compression_type=compression_type,
            compression_level=6,
            l1_max_size_mb=200
        )
        
        cache = ArenaSmartCache(config)
        
        # Read and cache model
        with open(large_model_path, 'rb') as f:
            model_data = f.read()
        
        start_time = time.time()
        success = cache.cache_model("checkpoints", "large_model.pt", model_data)
        cache_time = time.time() - start_time
        
        # Retrieve model
        start_time = time.time()
        cached_data = cache.get_model("checkpoints", "large_model.pt")
        retrieve_time = time.time() - start_time
        
        if cached_data:
            compression_ratio = len(cached_data) / len(model_data)
            print(f"   ✓ Cached successfully")
            print(f"   ✓ Compression ratio: {compression_ratio:.2f}")
            print(f"   ✓ Cache time: {cache_time:.3f}s")
            print(f"   ✓ Retrieve time: {retrieve_time:.3f}s")
        else:
            print(f"   ✗ Failed to cache/retrieve")
    
    # Cleanup
    import shutil
    shutil.rmtree(demo_dir)

def demo_hybrid_cache():
    """Demonstrate hybrid cache system"""
    print("\n" + "="*60)
    print("DEMO: Hybrid Cache System")
    print("="*60)
    
    # Configure hybrid cache
    hybrid_config = HybridCacheConfig()
    hybrid_config.enable_smart_cache = True
    hybrid_config.use_smart_cache_for_large_models = True
    hybrid_config.large_model_threshold_mb = 50
    hybrid_config.track_migration_stats = True
    
    # Initialize hybrid cache
    hybrid_cache = ArenaHybridCache(hybrid_config)
    
    print("1. Hybrid cache configuration:")
    print(f"   Smart cache enabled: {hybrid_config.enable_smart_cache}")
    print(f"   Large model threshold: {hybrid_config.large_model_threshold_mb}MB")
    print(f"   Fallback to original: {hybrid_config.fallback_to_original}")
    
    # Test workflow analysis
    print("\n2. Testing workflow analysis...")
    workflow = {
        "nodes": {
            "1": {"inputs": {"model": "large_model.pt"}},
            "2": {"inputs": {"model": "small_model.pt"}}
        }
    }
    
    models = hybrid_cache.analyze_workflow(workflow)
    print(f"   Detected models: {models}")
    
    # Get comprehensive metrics
    print("\n3. Hybrid cache metrics:")
    metrics = hybrid_cache.get_metrics()
    for key, value in metrics.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for sub_key, sub_value in value.items():
                print(f"     {sub_key}: {sub_value}")
        else:
            print(f"   {key}: {value}")
    
    # Test migration
    print("\n4. Testing migration to smart cache...")
    migration_results = hybrid_cache.migrate_to_smart_cache()
    print(f"   Migration results: {migration_results}")

def demo_analytics_and_monitoring():
    """Demonstrate analytics and monitoring features"""
    print("\n" + "="*60)
    print("DEMO: Analytics and Monitoring")
    print("="*60)
    
    # Configure cache with analytics
    config = CacheConfig(
        enable_analytics=True,
        metrics_retention_days=30,
        l1_max_size_mb=200
    )
    
    cache = ArenaSmartCache(config)
    
    # Simulate cache operations
    print("1. Simulating cache operations...")
    
    # Create demo models
    demo_dir = Path("demo_analytics")
    demo_dir.mkdir(exist_ok=True)
    
    models = [
        ("checkpoints", "model1.pt", 10 * 1024 * 1024),  # 10MB
        ("loras", "model2.pt", 5 * 1024 * 1024),         # 5MB
        ("vae", "model3.pt", 20 * 1024 * 1024),          # 20MB
    ]
    
    for category, filename, size in models:
        file_path = demo_dir / filename
        with open(file_path, 'wb') as f:
            f.write(b'0' * size)
        
        # Cache model
        with open(file_path, 'rb') as f:
            model_data = f.read()
        
        cache.cache_model(category, filename, model_data)
        print(f"   Cached {filename} ({size / 1024 / 1024:.1f}MB)")
    
    # Simulate cache hits and misses
    print("\n2. Simulating cache access patterns...")
    
    # Test cache hits
    for category, filename, _ in models:
        cached_data = cache.get_model(category, filename)
        if cached_data:
            print(f"   ✓ Cache hit: {filename}")
        else:
            print(f"   ✗ Cache miss: {filename}")
    
    # Test cache miss
    cached_data = cache.get_model("unknown", "nonexistent.pt")
    if not cached_data:
        print(f"   ✓ Expected cache miss: nonexistent.pt")
    
    # Get detailed metrics
    print("\n3. Detailed cache metrics:")
    metrics = cache.get_metrics()
    
    print(f"   Performance:")
    print(f"     Hit rate: {metrics.get('hit_rate', 0):.2%}")
    print(f"     Miss rate: {metrics.get('miss_rate', 0):.2%}")
    print(f"     Total requests: {metrics.get('total_requests', 0)}")
    print(f"     Average load time: {metrics.get('avg_load_time_ms', 0):.2f}ms")
    
    print(f"   Cache size:")
    print(f"     Total size: {metrics.get('cache_size_bytes', 0) / 1024 / 1024:.1f}MB")
    print(f"     L1 cache items: {metrics.get('l1_size', 0)}")
    print(f"     L2 cache items: {metrics.get('l2_size', 0)}")
    print(f"     L3 cache items: {metrics.get('l3_size', 0)}")
    
    # Cleanup
    import shutil
    shutil.rmtree(demo_dir)

def main():
    """Run all demonstrations"""
    print("Arena Smart Cache Demonstration")
    print("=" * 60)
    print("This demo showcases the advanced caching capabilities")
    print("of the new Arena Smart Cache system for ComfyUI.")
    
    try:
        # Run all demos
        demo_basic_smart_cache()
        demo_workflow_analysis()
        demo_compression_and_quantization()
        demo_hybrid_cache()
        demo_analytics_and_monitoring()
        
        print("\n" + "="*60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("="*60)
        print("All demonstrations completed successfully!")
        print("The Arena Smart Cache system is ready for integration.")
        
    except Exception as e:
        print(f"\nDemo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()


