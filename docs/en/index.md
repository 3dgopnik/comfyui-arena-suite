---
title: "ComfyUI Arena Suite - Documentation"
description: "Complete documentation for ComfyUI Arena Suite"
order: 1
---

# ComfyUI Arena Suite

🚀 **Modern ComfyUI Custom Node Suite** - Automatic model caching and workflow optimization for ComfyUI.

## ✨ Features

- **Arena AutoCache Simple v4.5.0** - Production-ready automatic model caching with OnDemand mode
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

4. **Restart ComfyUI** and find "Arena AutoCache (simple) v4.5.0" in the node menu.

### Usage

1. Add **Arena AutoCache (simple) v4.5.0** node to your workflow
2. Configure cache settings (optional)
3. Run your workflow - models will be automatically cached
4. Subsequent runs will use cached models for faster execution

## 📚 Documentation

- [Quick Start Guide](quickstart.md) - Get up and running quickly
- [Node Reference](nodes.md) - Detailed node documentation
- [Configuration](config.md) - Configuration options
- [User Manual](manual.md) - Complete user guide
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
- [CLI Tools](cli.md) - Command line tools

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