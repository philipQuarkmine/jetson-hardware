# Development Environment Setup

This document outlines the recommended development environment for the jetson-hardware project, optimized for robotics and embedded development on NVIDIA Jetson platforms.

## VS Code Configuration

### Required Extensions

Install these extensions for optimal development experience:

```bash
# Install via command line
code --install-extension charliermarsh.ruff
code --install-extension ms-python.python
code --install-extension ms-python.debugpy
```

**Or manually via VS Code Extensions panel:**
- ✅ **Ruff** (charliermarsh.ruff) - Primary linter and formatter
- ✅ **Python** (ms-python.python) - Core Python support  
- ✅ **Python Debugger** (ms-python.debugpy) - Debugging capabilities

### Extensions to Remove

Remove these extensions to prevent conflicts:
- ❌ **Pylance** - Too strict for hardware code patterns
- ❌ **Pylint** - Conflicts with Ruff configuration

### Auto-Configuration Files

The repository includes pre-configured development settings:

#### `.vscode/settings.json`
- Ruff as primary linter/formatter
- Disabled Pylance strict checking
- Hardware-friendly file handling
- Performance optimized for Jetson

#### `pyproject.toml` 
- Ruff rules optimized for robotics development
- Ignores hardware-specific patterns (bare except, direct imports, etc.)
- Allows flexibility needed for embedded programming

#### `pyrightconfig.json`
- Type checking configuration
- Relaxed rules for hardware libraries

## Code Standards

### Formatting Rules
- **Line Length**: 88-100 characters (configurable)
- **Import Organization**: Automatic sorting with Ruff
- **Quote Style**: Double quotes preferred
- **Indentation**: 4 spaces (tabs converted automatically)

### Hardware-Specific Patterns

The Ruff configuration allows patterns common in hardware programming:

```python
# ✅ Bare except for hardware error handling
try:
    device.read_register()
except:
    # Hardware can fail unpredictably
    pass

# ✅ Module-level imports after initialization  
import os
gi.require_version('Gst', '1.0')
from gi.repository import Gst  # OK after gi setup

# ✅ Direct hardware address access
GPIO_BASE = 0x7E200000
register = ctypes.c_uint32.from_address(GPIO_BASE)

# ✅ Hardware placeholder variables
buf = sample.get_buffer()  # May be used conditionally
caps = sample.get_caps()   # Based on runtime hardware
```

### Ignored Rules (Hardware-Friendly)

The configuration ignores these strict rules that conflict with embedded development:

- `E402` - Module level imports (hardware init patterns)
- `E722` - Bare except (needed for hardware reliability) 
- `F841` - Unused variables (hardware placeholders)
- `SIM105` - Contextlib.suppress (prefer explicit for hardware)
- `SIM115` - Context managers (file locking needs explicit control)

## Python Environment Setup

### Recommended Python Version
- **Python 3.8+** (compatible with Jetson JetPack)
- **Virtual Environment**: Recommended for dependency isolation

### Virtual Environment Setup
```bash
cd /home/phiip/workspace/jetson-hardware
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Install Ruff (if not in requirements.txt)
```bash
pip install ruff
```

## Development Workflow

### 1. File Editing
- Open project in VS Code
- Files auto-format on save
- Imports auto-organize
- Ruff provides real-time linting

### 2. Code Quality
```bash
# Manual linting check
ruff check .

# Manual formatting
ruff format .

# Fix auto-fixable issues
ruff check --fix .
```

### 3. Git Workflow
- All files should appear **white** in VS Code file explorer when clean
- **Orange** files indicate uncommitted changes (normal)
- **Red** files indicate actual errors needing attention

## Hardware Development Guidelines

### Thread Safety
Always use acquire/release pattern for hardware:
```python
manager = HardwareManager()
manager.acquire()
try:
    # Hardware operations
    manager.some_operation()
finally:
    manager.release()
```

### Error Handling
Prefer explicit error handling for hardware reliability:
```python
# ✅ Hardware-friendly
try:
    result = hardware_operation()
    if not result:
        logger.error("Hardware operation failed")
        return False
except Exception as e:
    logger.error(f"Hardware error: {e}")
    return False
```

### Performance Considerations
- Use appropriate data types for memory efficiency on Jetson
- Consider GPU vs CPU operations for AI workloads
- Profile memory usage for embedded constraints

## Troubleshooting

### VS Code File Colors
- **White**: Clean, committed files
- **Orange**: Modified files (normal during development) 
- **Red**: Files with errors or conflicts
- **Green**: New, untracked files

### Ruff Issues
```bash
# Check Ruff status
ruff --version

# Validate configuration
ruff check --show-source

# Clear cache if needed
ruff clean
```

### Extension Conflicts
If experiencing linting conflicts:
1. Ensure Pylance is uninstalled
2. Reload VS Code window: Ctrl+Shift+P → "Developer: Reload Window"
3. Check installed extensions for conflicts

## Contributing

When contributing code:
1. Follow the existing code style (auto-enforced by Ruff)
2. Test hardware code on actual Jetson hardware when possible
3. Update documentation for new hardware interfaces
4. Use hardware-appropriate error handling patterns
5. Maintain thread safety for hardware access

---

**This setup optimizes for the unique needs of robotics development: hardware reliability, performance on embedded systems, and practical coding patterns for real-world hardware interaction.**