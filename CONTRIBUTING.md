# Contributing Guidelines

Thank you for contributing to the jetson-hardware project! This document outlines the standards and practices for contributing to this robotics/embedded systems codebase.

## Development Environment

Before contributing, set up the recommended development environment:

1. **Read**: `docs/Development_Environment_Setup.md` for complete setup instructions
2. **Install**: Ruff extension for VS Code (primary linter)
3. **Remove**: Pylance and Pylint extensions to prevent conflicts
4. **Verify**: Files appear white (clean) in VS Code file explorer after setup

## Code Standards

### Formatting & Linting
- **Auto-formatting**: Code is automatically formatted with Ruff on save
- **Import organization**: Imports are auto-sorted following hardware development patterns
- **Line length**: 88-100 characters (configurable in pyproject.toml)
- **No manual formatting needed**: Ruff handles all formatting automatically

### Hardware-Specific Code Patterns

This project allows hardware-friendly patterns that strict linters often reject:

#### ✅ **Acceptable Patterns:**
```python
# Bare except for hardware error handling
try:
    device.read_sensor()
except:
    # Hardware can fail unpredictably - broad exception is OK
    return default_value

# Module-level imports after hardware initialization
import os
gi.require_version('Gst', '1.0') 
from gi.repository import Gst  # OK after gi setup

# Hardware placeholder variables
buf = sample.get_buffer()  # May be used conditionally based on hardware
caps = sample.get_caps()   # Runtime hardware determines usage

# Direct hardware memory access
GPIO_BASE = 0x7E200000
register = ctypes.c_uint32.from_address(GPIO_BASE + offset)
```

#### ❌ **Avoid These Patterns:**
```python
# Don't use contextlib.suppress for hardware (prefer explicit)
with contextlib.suppress(Exception):  # ❌ Too implicit for hardware debugging
    hardware_operation()

# Don't use auto-context managers for file locking
with open(lock_file) as f:  # ❌ Hardware locking needs explicit control
    fcntl.lockf(f, fcntl.LOCK_EX)
```

## Architecture Guidelines

### Manager Pattern
All hardware access follows the acquire/release pattern:

```python
class HardwareManager:
    def acquire(self):
        """Acquire exclusive access to hardware resource."""
        # Thread lock + file lock for process safety
        
    def release(self):
        """Release hardware resource."""
        # Always cleanup, even on exceptions
        
    def operation(self):
        """Hardware operation requiring acquired access."""
        if not self._acquired:
            raise RuntimeError("Must acquire before use")
```

### Thread Safety
- **All hardware managers must be thread-safe**
- Use `threading.Lock()` for thread safety
- Use `fcntl.lockf()` for process-level safety
- Always provide acquire/release methods

### Error Handling
- **Hardware reliability over strict typing**
- Use explicit try/except with logging
- Prefer returning error states over raising exceptions
- Log hardware errors with context information

## Testing

### Hardware Testing
- Test on actual Jetson hardware when possible
- Provide mock testing for CI environments
- Include performance benchmarks for hardware operations

### Test Categories
```bash
# Unit tests for individual components
python3 SimpleTests/test_display_manager.py

# Integration tests for complete systems  
python3 SimpleTests/demo_display_manager.py

# Interactive tests for manual verification
python3 SimpleTests/interactive_chat.py
```

## Documentation

### Code Documentation
- **Docstrings**: Use Google-style docstrings for public methods
- **Inline comments**: Explain hardware-specific operations
- **Type hints**: Optional, hardware code often requires dynamic typing

### Documentation Updates
When adding new features:
1. Update relevant README.md sections
2. Add documentation to `docs/` folder if creating new subsystems
3. Update `docs/README.md` with new documentation references
4. Include usage examples in docstrings

## Git Workflow

### Branch Management
- **Main branch**: `master` (stable, deployable)
- **Feature branches**: `feature/description` or `fix/issue-description`
- **Testing**: Test on hardware before merging to master

### Commit Standards
```bash
# Good commit messages
feat: add Display_Manager with hardware-accelerated graphics
fix: resolve I2C communication timeout in OLED_Manager  
docs: update development environment setup guide
refactor: optimize memory usage in StreamingMicManager

# Include scope when relevant
feat(display): add GStreamer camera integration
fix(audio): handle USB microphone disconnection gracefully
```

### Pre-Commit Checklist
- [ ] Code automatically formatted by Ruff (should happen on save)
- [ ] All files appear white (clean) in VS Code
- [ ] Hardware tested on actual Jetson (when applicable)
- [ ] Documentation updated for new features
- [ ] No merge conflicts with master

## Hardware Considerations

### Performance
- **Memory efficiency**: Important on embedded systems
- **GPU utilization**: Leverage Jetson's AI capabilities appropriately  
- **Real-time constraints**: Consider timing requirements for robotics

### Compatibility
- **JetPack versions**: Test compatibility with current JetPack
- **Hardware variants**: Consider different Jetson models when possible
- **Dependencies**: Minimize external dependencies for embedded deployment

## Review Process

### Code Review Focus
1. **Hardware safety**: No operations that could damage hardware
2. **Thread safety**: Proper acquire/release patterns
3. **Error handling**: Appropriate for hardware reliability
4. **Performance**: Efficient for embedded constraints
5. **Documentation**: Clear usage examples

### Review Checklist
- [ ] Follows hardware-friendly coding patterns
- [ ] Includes appropriate error handling
- [ ] Maintains thread safety for hardware access  
- [ ] Documentation is clear and includes examples
- [ ] Performance is acceptable for embedded use

## Getting Help

### Resources
- **Hardware docs**: See `docs/` folder for hardware-specific guides
- **Development setup**: `docs/Development_Environment_Setup.md`
- **Architecture patterns**: Study existing managers for patterns
- **Community**: Open issues for hardware-specific questions

### Common Issues
- **VS Code file colors**: Usually indicates git status, not code errors
- **Linting conflicts**: Ensure Pylance is uninstalled
- **Hardware access errors**: Check acquire/release patterns
- **Performance issues**: Profile on actual Jetson hardware

---

**Thank you for helping build reliable, efficient robotics software for the Jetson platform!**