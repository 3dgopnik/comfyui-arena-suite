# ComfyUI Arena Suite v5.0.0

🚀 **Modern ComfyUI Custom Node Suite** - Automatic model caching and workflow optimization for ComfyUI.

## ✨ Features

- **🅰️ Arena AutoCache v5.0.0** - Settings UI with "💾 Save to .env", OnDemand caching, safer defaults
- **Web Extensions** - Seamless ComfyUI integration
- **Modern Architecture** - Clean, maintainable codebase
- **CI/CD Ready** - GitHub Actions workflow included

## 🚀 Quick Start

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/3dgopnik/comfyui-arena-suite.git
   cd comfyui-arena-suite
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Copy to ComfyUI custom_nodes:**
   ```bash
   cp -r custom_nodes/ComfyUI_Arena /path/to/ComfyUI/custom_nodes/
   cp -r web /path/to/ComfyUI/
   ```

4. **Sync JavaScript files** (if using ComfyUI Desktop):
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/sync_js_files.ps1
   ```

5. **Restart ComfyUI** and find "🅰️ Arena AutoCache v5.0.0" in the node menu.

### Usage

#### Quick Start (Global Toggle)

1. **Look for 🅰️ indicator** in ComfyUI header
2. **Click to enable** - one-click caching activation
3. **Configure settings** - Right-click → Settings → Arena section
4. **Run workflows** - automatic model caching without canvas nodes

#### Advanced (Canvas Node)

1. Add **🅰️ Arena AutoCache v5.0.0** node to your workflow
2. Configure cache settings (optional)
3. Run your workflow - models will be automatically cached
4. Subsequent runs will use cached models for faster execution

## 📁 Project Structure

```
comfyui-arena-suite/
├── custom_nodes/ComfyUI_Arena/    # Main custom node
│   ├── autocache/                 # Autocache functionality
│   └── __init__.py               # Node registration
├── web/                          # ComfyUI web extensions
│   ├── arena/                    # Core JS functionality
│   └── extensions/               # ComfyUI integration
├── scripts/                      # Installation scripts
├── docs/                         # Documentation
├── .github/workflows/            # CI/CD
├── requirements.txt              # Production dependencies
└── requirements-dev.txt          # Development dependencies
```

## 🛠️ Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/3dgopnik/comfyui-arena-suite.git
cd comfyui-arena-suite

# Install development dependencies (optional)
pip install -r requirements-dev.txt

# Run linting (optional)
ruff check .
mypy custom_nodes/
```

### Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/your-feature`
3. **Make your changes**
4. **Run linting:** `ruff check .` (optional)
5. **Commit changes:** `git commit -m "Add your feature"`
6. **Push to branch:** `git push origin feature/your-feature`
7. **Create a Pull Request**

### Code Style

- **Python:** Follow PEP 8, use type hints
- **JavaScript:** Use modern ES6+ syntax
- **Documentation:** Write clear, concise docstrings

### Pull Request Guidelines

Before submitting a PR, ensure:

- ✅ Code is linted (`ruff check .`) - optional
- ✅ Type checking passes (`mypy`) - optional
- ✅ Documentation is updated
- ✅ CHANGELOG.md is updated
- ✅ Commit messages are clear and descriptive

### Issue Reporting

When reporting issues, please include:

- **ComfyUI version**
- **Python version**
- **Error logs** (if any)
- **Steps to reproduce**
- **Expected vs actual behavior**

## 📚 Documentation

- **[Quick Start Guide](docs/ru/quickstart.md)** - Get up and running quickly
- **[Node Reference](docs/ru/nodes.md)** - Detailed node documentation
- **[Configuration](docs/ru/config.md)** - Configuration options
- **[Troubleshooting](docs/ru/troubleshooting.md)** - Common issues and solutions

## 📦 Scripts

- **`scripts/arena_bootstrap_cache_v2.bat`** - Windows batch installer
- **`scripts/arena_bootstrap_cache_v2.ps1`** - PowerShell installer
- **`scripts/arena_set_cache.bat`** - Cache configuration script

## 🔧 Configuration

### Environment Variables

- `ARENA_CACHE_DIR` - Custom cache directory path
- `ARENA_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

### Node Settings

- **Cache Directory** - Where to store cached models
- **Cache Size Limit** - Maximum cache size in GB
- **Auto Cleanup** - Automatically clean old cache files

## 🐛 Troubleshooting

### Common Issues

1. **Node not appearing in ComfyUI:**
   - Ensure files are in correct `custom_nodes/` directory
   - Restart ComfyUI completely
   - Check console for error messages

2. **Cache not working:**
   - Verify cache directory permissions
   - Check available disk space
   - Review log files for errors

3. **Performance issues:**
   - Monitor cache directory size
   - Check disk I/O performance
   - Consider SSD storage for cache

### Getting Help

- **GitHub Issues:** [Report bugs and request features](https://github.com/3dgopnik/comfyui-arena-suite/issues)
- **Discussions:** [Community discussions](https://github.com/3dgopnik/comfyui-arena-suite/discussions)
- **Documentation:** Check the [docs/](docs/) folder for detailed guides

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **ComfyUI** - The amazing workflow system
- **Community** - All contributors and users
- **Open Source** - Built on the shoulders of giants

---

**Made with ❤️ for the ComfyUI community**