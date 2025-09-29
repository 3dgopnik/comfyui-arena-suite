"""Pytest configuration and fixtures for ComfyUI Arena Suite."""

import os
import sys
from collections.abc import Generator
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def mock_comfyui_environment() -> Generator[dict[str, str], None, None]:
    """Mock ComfyUI environment variables."""
    env_vars = {
        "COMFYUI_ROOT": "/tmp/comfyui",
        "ARENA_CACHE_DIR": "/tmp/arena_cache",
        "ARENA_CACHE_ENABLE": "true",
        "ARENA_CACHE_MIN_SIZE_MB": "100",
        "ARENA_CACHE_CATEGORIES": "checkpoints,loras,vaes",
    }

    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def mock_torch() -> Generator[Mock, None, None]:
    """Mock torch module for testing."""
    mock_torch = Mock()
    mock_torch.cuda.is_available.return_value = True
    mock_torch.cuda.device_count.return_value = 1
    mock_torch.cuda.current_device.return_value = 0

    # Mock tensor operations
    mock_tensor = Mock()
    mock_tensor.shape = (1, 3, 512, 512)
    mock_tensor.dtype = "float32"
    mock_tensor.device = "cuda:0"

    mock_torch.tensor.return_value = mock_tensor
    mock_torch.zeros.return_value = mock_tensor
    mock_torch.ones.return_value = mock_tensor

    with patch("torch", mock_torch):
        yield mock_torch


@pytest.fixture
def mock_comfyui_modules() -> Generator[dict[str, Mock], None, None]:
    """Mock ComfyUI internal modules."""
    mock_modules = {
        "folder_paths": Mock(),
        "execution": Mock(),
        "server": Mock(),
    }

    # Mock folder_paths
    mock_modules["folder_paths"].get_folder_paths.return_value = {
        "checkpoints": ["/models/checkpoints"],
        "loras": ["/models/loras"],
        "vaes": ["/models/vaes"],
        "clips": ["/models/clips"],
    }
    mock_modules["folder_paths"].get_full_path.return_value = "/models/checkpoints/model.safetensors"

    # Mock execution
    mock_modules["execution"].graph = Mock()
    mock_modules["execution"].graph.nodes = []

    with patch.dict("sys.modules", mock_modules):
        yield mock_modules


@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    """Create temporary cache directory for testing."""
    cache_dir = tmp_path / "arena_cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir


@pytest.fixture
def sample_model_files(tmp_path: Path) -> list[Path]:
    """Create sample model files for testing."""
    model_files = []

    # Create sample checkpoint
    checkpoint = tmp_path / "checkpoint.safetensors"
    checkpoint.write_bytes(b"fake checkpoint data" * 1000)  # ~18KB
    model_files.append(checkpoint)

    # Create sample LoRA
    lora = tmp_path / "lora.safetensors"
    lora.write_bytes(b"fake lora data" * 500)  # ~9KB
    model_files.append(lora)

    # Create sample VAE
    vae = tmp_path / "vae.safetensors"
    vae.write_bytes(b"fake vae data" * 200)  # ~3.6KB
    model_files.append(vae)

    return model_files


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test."""
    # Ensure clean environment
    os.environ.pop("ARENA_CACHE_ENABLE", None)
    os.environ.pop("ARENA_CACHE_DIR", None)

    yield

    # Cleanup after test
    pass


# Test markers
def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "requires_gpu: mark test as requiring GPU")
    config.addinivalue_line("markers", "requires_network: mark test as requiring network access")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add slow marker to tests with 'slow' in name
        if "slow" in item.name:
            item.add_marker(pytest.mark.slow)

        # Add integration marker to tests in integration directory
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Add unit marker to tests in unit directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
