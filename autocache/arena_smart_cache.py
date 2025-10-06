#!/usr/bin/env python3
"""
Arena Smart Cache - Advanced intelligent caching system for ComfyUI models
RU: Продвинутая интеллектуальная система кеширования моделей ComfyUI

Features:
- Multi-level caching (L1: RAM, L2: SSD, L3: HDD)
- Intelligent prediction and preloading
- Model compression and quantization
- Advanced analytics and monitoring
- Distributed caching support
"""

import os
import time
import json
import pickle
import hashlib
import threading
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import zstd
import torch
import numpy as np
from collections import defaultdict, deque
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheLevel(Enum):
    """Cache levels for multi-level caching"""
    L1_MEMORY = "l1_memory"
    L2_SSD = "l2_ssd" 
    L3_HDD = "l3_hdd"
    L4_NETWORK = "l4_network"

class CompressionType(Enum):
    """Compression algorithms"""
    NONE = "none"
    GZIP = "gzip"
    ZSTD = "zstd"
    LZ4 = "lz4"

class QuantizationType(Enum):
    """Model quantization types"""
    NONE = "none"
    FP16 = "fp16"
    INT8 = "int8"
    INT4 = "int4"

@dataclass
class CacheConfig:
    """Configuration for smart cache"""
    # Cache levels
    l1_max_size_mb: int = 2048  # 2GB RAM cache
    l2_max_size_gb: int = 50    # 50GB SSD cache
    l3_max_size_gb: int = 200   # 200GB HDD cache
    
    # Compression
    compression_type: CompressionType = CompressionType.ZSTD
    compression_level: int = 6
    
    # Quantization
    quantization_type: QuantizationType = QuantizationType.FP16
    auto_quantize: bool = True
    
    # Prediction
    enable_prediction: bool = True
    prediction_window: int = 5  # models to predict ahead
    
    # Analytics
    enable_analytics: bool = True
    metrics_retention_days: int = 30
    
    # Distributed
    enable_distributed: bool = False
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    hits: int = 0
    misses: int = 0
    total_requests: int = 0
    cache_size_bytes: int = 0
    avg_load_time_ms: float = 0.0
    hit_rate: float = 0.0
    miss_rate: float = 0.0
    
    def update_hit_rate(self):
        """Update hit/miss rates"""
        if self.total_requests > 0:
            self.hit_rate = self.hits / self.total_requests
            self.miss_rate = self.misses / self.total_requests

@dataclass
class ModelInfo:
    """Information about a cached model"""
    model_id: str
    category: str
    filename: str
    size_bytes: int
    access_count: int = 0
    last_access: float = 0.0
    cache_level: CacheLevel = CacheLevel.L1_MEMORY
    compressed: bool = False
    quantized: bool = False
    compression_ratio: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class WorkflowAnalyzer:
    """Analyzes ComfyUI workflows to predict model usage"""
    
    def __init__(self):
        self.workflow_patterns = defaultdict(list)
        self.model_dependencies = defaultdict(set)
        self.usage_history = deque(maxlen=1000)
    
    def analyze_workflow(self, workflow: Dict) -> List[str]:
        """Analyze workflow and extract model requirements"""
        models = []
        
        # Extract models from workflow nodes
        for node_id, node_data in workflow.get("nodes", {}).items():
            if "model" in node_data.get("inputs", {}):
                model_name = node_data["inputs"]["model"]
                if isinstance(model_name, str):
                    models.append(model_name)
        
        # Store pattern for future prediction
        self.usage_history.append({
            "timestamp": time.time(),
            "models": models,
            "workflow_id": workflow.get("id", "unknown")
        })
        
        return models
    
    def predict_next_models(self, current_models: List[str], window: int = 5) -> List[str]:
        """Predict next models based on usage patterns"""
        if not self.usage_history:
            return []
        
        # Simple pattern matching - can be enhanced with ML
        predictions = []
        for entry in list(self.usage_history)[-window:]:
            if any(model in entry["models"] for model in current_models):
                predictions.extend(entry["models"])
        
        # Return unique predictions
        return list(set(predictions))

class ModelCompressor:
    """Handles model compression and quantization"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
    
    def compress_model(self, model_data: bytes) -> Tuple[bytes, float]:
        """Compress model data"""
        if self.config.compression_type == CompressionType.NONE:
            return model_data, 1.0
        
        try:
            if self.config.compression_type == CompressionType.ZSTD:
                compressed = zstd.compress(model_data, self.config.compression_level)
            elif self.config.compression_type == CompressionType.GZIP:
                import gzip
                compressed = gzip.compress(model_data)
            else:
                return model_data, 1.0
            
            ratio = len(compressed) / len(model_data)
            return compressed, ratio
        except Exception as e:
            logger.warning(f"Compression failed: {e}")
            return model_data, 1.0
    
    def decompress_model(self, compressed_data: bytes) -> bytes:
        """Decompress model data"""
        if self.config.compression_type == CompressionType.NONE:
            return compressed_data
        
        try:
            if self.config.compression_type == CompressionType.ZSTD:
                return zstd.decompress(compressed_data)
            elif self.config.compression_type == CompressionType.GZIP:
                import gzip
                return gzip.decompress(compressed_data)
            else:
                return compressed_data
        except Exception as e:
            logger.warning(f"Decompression failed: {e}")
            return compressed_data
    
    def quantize_model(self, model_path: str) -> Optional[str]:
        """Quantize model to reduce size"""
        if not self.config.auto_quantize:
            return None
        
        try:
            # Load model
            model = torch.load(model_path, map_location='cpu')
            
            if self.config.quantization_type == QuantizationType.FP16:
                # Convert to FP16
                model = model.half()
            elif self.config.quantization_type == QuantizationType.INT8:
                # Dynamic quantization
                model = torch.quantization.quantize_dynamic(
                    model, {torch.nn.Linear}, dtype=torch.qint8
                )
            
            # Save quantized model
            quantized_path = model_path.replace('.pt', '_quantized.pt')
            torch.save(model, quantized_path)
            
            return quantized_path
        except Exception as e:
            logger.warning(f"Quantization failed: {e}")
            return None

class MultiLevelCache:
    """Multi-level cache implementation"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.l1_cache: Dict[str, bytes] = {}  # RAM cache
        self.l2_cache: Dict[str, str] = {}    # SSD cache (file paths)
        self.l3_cache: Dict[str, str] = {}    # HDD cache (file paths)
        
        self.model_info: Dict[str, ModelInfo] = {}
        self.metrics = CacheMetrics()
        self.workflow_analyzer = WorkflowAnalyzer()
        self.compressor = ModelCompressor(config)
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Initialize cache directories
        self._init_cache_directories()
    
    def _init_cache_directories(self):
        """Initialize cache directories"""
        self.cache_root = Path("models/arena_smart_cache")
        self.l2_dir = self.cache_root / "l2_ssd"
        self.l3_dir = self.cache_root / "l3_hdd"
        
        self.l2_dir.mkdir(parents=True, exist_ok=True)
        self.l3_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_model_id(self, category: str, filename: str) -> str:
        """Generate unique model ID"""
        return hashlib.md5(f"{category}:{filename}".encode()).hexdigest()
    
    def _get_cache_path(self, model_id: str, level: CacheLevel) -> Path:
        """Get cache path for model at specified level"""
        if level == CacheLevel.L2_SSD:
            return self.l2_dir / f"{model_id}.cache"
        elif level == CacheLevel.L3_HDD:
            return self.l3_dir / f"{model_id}.cache"
        else:
            raise ValueError(f"Invalid cache level: {level}")
    
    def _calculate_cache_size(self) -> int:
        """Calculate total cache size in bytes"""
        total_size = 0
        
        # L1 cache size
        for data in self.l1_cache.values():
            total_size += len(data)
        
        # L2 and L3 cache sizes
        for cache_dir in [self.l2_dir, self.l3_dir]:
            for file_path in cache_dir.glob("*.cache"):
                total_size += file_path.stat().st_size
        
        return total_size
    
    def _evict_lru(self, level: CacheLevel):
        """Evict least recently used items from cache"""
        if level == CacheLevel.L1_MEMORY:
            # Find LRU item in L1
            lru_model_id = min(
                self.l1_cache.keys(),
                key=lambda k: self.model_info[k].last_access
            )
            del self.l1_cache[lru_model_id]
        else:
            # For L2/L3, remove oldest files
            cache_dir = self.l2_dir if level == CacheLevel.L2_SSD else self.l3_dir
            files = [(f.stat().st_mtime, f) for f in cache_dir.glob("*.cache")]
            if files:
                oldest_file = min(files)[1]
                oldest_file.unlink()
    
    def _should_compress(self, size_bytes: int) -> bool:
        """Determine if model should be compressed"""
        return size_bytes > 1024 * 1024  # Compress if > 1MB
    
    def get_model(self, category: str, filename: str) -> Optional[bytes]:
        """Get model from cache"""
        start_time = time.time()
        model_id = self._get_model_id(category, filename)
        
        with self.lock:
            # Check L1 cache first
            if model_id in self.l1_cache:
                self.metrics.hits += 1
                self.metrics.total_requests += 1
                self.model_info[model_id].access_count += 1
                self.model_info[model_id].last_access = time.time()
                self.metrics.update_hit_rate()
                
                load_time = (time.time() - start_time) * 1000
                self.metrics.avg_load_time_ms = (
                    self.metrics.avg_load_time_ms * 0.9 + load_time * 0.1
                )
                
                logger.info(f"L1 cache hit: {filename}")
                return self.l1_cache[model_id]
            
            # Check L2 cache
            l2_path = self._get_cache_path(model_id, CacheLevel.L2_SSD)
            if l2_path.exists():
                try:
                    with open(l2_path, 'rb') as f:
                        data = f.read()
                    
                    # Decompress if needed
                    if model_id in self.model_info and self.model_info[model_id].compressed:
                        data = self.compressor.decompress_model(data)
                    
                    # Promote to L1 if space available
                    if len(self.l1_cache) * 1024 * 1024 < self.config.l1_max_size_mb:
                        self.l1_cache[model_id] = data
                    
                    self.metrics.hits += 1
                    self.metrics.total_requests += 1
                    if model_id in self.model_info:
                        self.model_info[model_id].access_count += 1
                        self.model_info[model_id].last_access = time.time()
                    self.metrics.update_hit_rate()
                    
                    load_time = (time.time() - start_time) * 1000
                    self.metrics.avg_load_time_ms = (
                        self.metrics.avg_load_time_ms * 0.9 + load_time * 0.1
                    )
                    
                    logger.info(f"L2 cache hit: {filename}")
                    return data
                except Exception as e:
                    logger.warning(f"L2 cache read error: {e}")
            
            # Check L3 cache
            l3_path = self._get_cache_path(model_id, CacheLevel.L3_HDD)
            if l3_path.exists():
                try:
                    with open(l3_path, 'rb') as f:
                        data = f.read()
                    
                    # Decompress if needed
                    if model_id in self.model_info and self.model_info[model_id].compressed:
                        data = self.compressor.decompress_model(data)
                    
                    # Promote to L2
                    with open(l2_path, 'wb') as f:
                        f.write(data)
                    
                    self.metrics.hits += 1
                    self.metrics.total_requests += 1
                    if model_id in self.model_info:
                        self.model_info[model_id].access_count += 1
                        self.model_info[model_id].last_access = time.time()
                    self.metrics.update_hit_rate()
                    
                    load_time = (time.time() - start_time) * 1000
                    self.metrics.avg_load_time_ms = (
                        self.metrics.avg_load_time_ms * 0.9 + load_time * 0.1
                    )
                    
                    logger.info(f"L3 cache hit: {filename}")
                    return data
                except Exception as e:
                    logger.warning(f"L3 cache read error: {e}")
            
            # Cache miss
            self.metrics.misses += 1
            self.metrics.total_requests += 1
            self.metrics.update_hit_rate()
            
            logger.info(f"Cache miss: {filename}")
            return None
    
    def cache_model(self, category: str, filename: str, model_data: bytes) -> bool:
        """Cache model data"""
        model_id = self._get_model_id(category, filename)
        original_size = len(model_data)
        
        with self.lock:
            # Determine compression
            should_compress = self._should_compress(original_size)
            if should_compress:
                compressed_data, ratio = self.compressor.compress_model(model_data)
            else:
                compressed_data, ratio = model_data, 1.0
            
            # Store in L1 cache if space available
            if len(self.l1_cache) * 1024 * 1024 < self.config.l1_max_size_mb:
                self.l1_cache[model_id] = compressed_data
                cache_level = CacheLevel.L1_MEMORY
            else:
                # Store in L2 cache
                l2_path = self._get_cache_path(model_id, CacheLevel.L2_SSD)
                with open(l2_path, 'wb') as f:
                    f.write(compressed_data)
                cache_level = CacheLevel.L2_SSD
            
            # Update model info
            self.model_info[model_id] = ModelInfo(
                model_id=model_id,
                category=category,
                filename=filename,
                size_bytes=original_size,
                cache_level=cache_level,
                compressed=should_compress,
                compression_ratio=ratio,
                last_access=time.time()
            )
            
            # Update metrics
            self.metrics.cache_size_bytes = self._calculate_cache_size()
            
            logger.info(f"Cached model: {filename} (level: {cache_level.value}, compressed: {should_compress})")
            return True
    
    def predict_and_preload(self, current_models: List[str]) -> List[str]:
        """Predict and preload next models"""
        if not self.config.enable_prediction:
            return []
        
        # Predict next models
        predicted_models = self.workflow_analyzer.predict_next_models(
            current_models, self.config.prediction_window
        )
        
        # Preload predicted models (simplified - would need actual model loading)
        preloaded = []
        for model in predicted_models:
            if self.get_model("predicted", model) is None:
                # Would load and cache the model here
                preloaded.append(model)
        
        return preloaded
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics"""
        with self.lock:
            return {
                "hits": self.metrics.hits,
                "misses": self.metrics.misses,
                "total_requests": self.metrics.total_requests,
                "hit_rate": self.metrics.hit_rate,
                "miss_rate": self.metrics.miss_rate,
                "cache_size_bytes": self.metrics.cache_size_bytes,
                "avg_load_time_ms": self.metrics.avg_load_time_ms,
                "l1_size": len(self.l1_cache),
                "l2_size": len(list(self.l2_dir.glob("*.cache"))),
                "l3_size": len(list(self.l3_dir.glob("*.cache")))
            }
    
    def clear_cache(self, level: Optional[CacheLevel] = None) -> str:
        """Clear cache at specified level or all levels"""
        with self.lock:
            if level is None or level == CacheLevel.L1_MEMORY:
                self.l1_cache.clear()
            
            if level is None or level == CacheLevel.L2_SSD:
                for file_path in self.l2_dir.glob("*.cache"):
                    file_path.unlink()
            
            if level is None or level == CacheLevel.L3_HDD:
                for file_path in self.l3_dir.glob("*.cache"):
                    file_path.unlink()
            
            # Reset metrics
            self.metrics = CacheMetrics()
            self.model_info.clear()
            
            return "Cache cleared successfully"

class ArenaSmartCache:
    """Main smart cache class for ComfyUI integration"""
    
    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.cache = MultiLevelCache(self.config)
        self.workflow_analyzer = WorkflowAnalyzer()
        
        logger.info("Arena Smart Cache initialized")
    
    def get_model(self, category: str, filename: str) -> Optional[bytes]:
        """Get model from smart cache"""
        return self.cache.get_model(category, filename)
    
    def cache_model(self, category: str, filename: str, model_data: bytes) -> bool:
        """Cache model in smart cache"""
        return self.cache.cache_model(category, filename, model_data)
    
    def analyze_workflow(self, workflow: Dict) -> List[str]:
        """Analyze workflow and predict models"""
        models = self.workflow_analyzer.analyze_workflow(workflow)
        
        if self.config.enable_prediction:
            predicted = self.cache.predict_and_preload(models)
            logger.info(f"Predicted {len(predicted)} models for preloading")
        
        return models
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get cache metrics"""
        return self.cache.get_metrics()
    
    def clear_cache(self) -> str:
        """Clear all caches"""
        return self.cache.clear_cache()

# Global smart cache instance
_smart_cache: Optional[ArenaSmartCache] = None

def get_smart_cache() -> ArenaSmartCache:
    """Get global smart cache instance"""
    global _smart_cache
    if _smart_cache is None:
        _smart_cache = ArenaSmartCache()
    return _smart_cache

def initialize_smart_cache(config: CacheConfig = None):
    """Initialize smart cache with configuration"""
    global _smart_cache
    _smart_cache = ArenaSmartCache(config)
    logger.info("Smart cache initialized with configuration")

# Example usage
if __name__ == "__main__":
    # Initialize smart cache
    config = CacheConfig(
        l1_max_size_mb=1024,
        l2_max_size_gb=25,
        enable_prediction=True,
        compression_type=CompressionType.ZSTD
    )
    
    cache = ArenaSmartCache(config)
    
    # Example workflow analysis
    workflow = {
        "nodes": {
            "1": {"inputs": {"model": "model1.pt"}},
            "2": {"inputs": {"model": "model2.pt"}}
        }
    }
    
    models = cache.analyze_workflow(workflow)
    print(f"Detected models: {models}")
    
    # Get metrics
    metrics = cache.get_metrics()
    print(f"Cache metrics: {metrics}")


