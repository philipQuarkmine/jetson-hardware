# Autonomous Operation Architecture

## Overview

The Jetson Orin Nano serves as an autonomous robot brain that must function independently of development connections (SSH). This document defines the architectural principles for ensuring robust, autonomous operation.

**Date Created**: October 28, 2025  
**Last Updated**: October 28, 2025

---

## The Discovery: SSH Dependency Issue

**Problem Identified**: The `heartbeat_screensaver.py` ran for 18+ hours successfully, but stopped when SSH connection was lost due to desktop sleep mode. No error occurred - the process simply received SIGHUP (hangup) signal when the terminal session ended.

**Implication**: Any long-running program attached to an SSH session will terminate when:
- SSH connection is lost
- Network interruption occurs
- Development computer goes to sleep
- Terminal window is closed

**Critical Realization**: For autonomous robot operation, we must distinguish between:
1. Programs that *should* stop when developer disconnects (development tools)
2. Programs that *must* continue running (robot control)
3. Programs that *should* continue but aren't critical (monitoring)

---

## Three-Layer Architecture

### Layer 1: Development Tools (SSH-Dependent)

**Purpose**: Interactive development, testing, debugging, and human supervision

**Characteristics**:
- Require human interaction or supervision
- Output to console for developer feedback
- Can be safely terminated at any time
- Used during development and testing phases
- Located in `SimpleTests/` directory

**Execution Context**: SSH-attached terminal session

**Expected Behavior**: Terminates when SSH disconnects (this is correct behavior)

**Examples**:
```python
# Hardware testing
SimpleTests/test_display_manager.py
SimpleTests/test_arduino_motor_manager.py
SimpleTests/test_camera_display_integration.py

# Interactive interfaces
SimpleTests/interactive_chat.py
SimpleTests/demo_camera_manager.py

# Development utilities
SimpleTests/screensaver_launcher.py (the launcher itself)
```

**Usage Pattern**:
```bash
# Direct execution during development
python3 SimpleTests/test_hardware.py

# Expected: Stops when SSH disconnects
# This is CORRECT behavior for development tools
```

---

### Layer 2: Critical Robot Services (SSH-Independent)

**Purpose**: Core autonomous operation that enables robot to function independently

**Characteristics**:
- Autonomous control loops
- Safety-critical monitoring
- Sensor fusion and decision making
- Must survive system disconnections
- Auto-restart on failure
- Managed by systemd

**Execution Context**: System service (survives SSH, reboots, crashes)

**Expected Behavior**: Runs continuously, independent of any user sessions

**Current Examples**:
```python
# LocalLLM_Manager already implements this pattern correctly!
# It spawns ollama as independent subprocess that survives parent death
Managers/LocalLLM_Manager.py  # ✅ Good example of service pattern
```

**Future Examples**:
```python
Services/robot_control_service.py      # Main autonomous control loop
Services/sensor_fusion_service.py      # Combines all sensor inputs
Services/emergency_monitor_service.py  # Safety watchdog
Services/navigation_service.py         # Path planning and execution
Services/obstacle_avoidance_service.py # Real-time collision prevention
```

**Usage Pattern**:
```bash
# Install as systemd service
sudo cp Services/robot-control.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable robot-control
sudo systemctl start robot-control

# Check status
sudo systemctl status robot-control
sudo journalctl -u robot-control -f

# Service survives:
# - SSH disconnection ✅
# - Network interruption ✅  
# - Terminal closure ✅
# - System reboot (with enable) ✅
# - Process crash (with Restart=always) ✅
```

**Implementation Requirements**:

1. **Signal Handling**:
```python
import signal
import sys

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down...")
    
    # Release all hardware managers
    motor_manager.release()
    display_manager.release()
    camera_manager.release()
    
    # Close data files
    data_logger.close()
    
    # Exit cleanly
    sys.exit(0)

# Register handlers
signal.signal(signal.SIGTERM, signal_handler)  # systemctl stop
signal.signal(signal.SIGHUP, signal_handler)   # systemctl reload
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C (for manual testing)
```

2. **Logging to System Journal**:
```python
import logging
import systemd.journal

# Log to systemd journal instead of console
logger = logging.getLogger(__name__)
logger.addHandler(systemd.journal.JournalHandler())
logger.setLevel(logging.INFO)

# Don't print to stdout/stderr in service mode
```

3. **PID File Management**:
```python
import os
import fcntl

PID_FILE = '/var/run/robot_control.pid'

def create_pid_file():
    """Create PID file to prevent multiple instances."""
    pid_file = open(PID_FILE, 'w')
    try:
        fcntl.lockf(pid_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        pid_file.write(str(os.getpid()))
        pid_file.flush()
        return pid_file
    except IOError:
        raise RuntimeError("Service already running")

def remove_pid_file():
    """Clean up PID file on exit."""
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
```

4. **Systemd Service File Template**:
```ini
[Unit]
Description=Robot Control Service
After=network.target

[Service]
Type=simple
User=phiip
WorkingDirectory=/home/phiip/workspace/jetson-hardware
ExecStart=/home/phiip/workspace/jetson-hardware/.venv/bin/python Services/robot_control_service.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

---

### Layer 3: Background Monitoring (Should Survive SSH)

**Purpose**: System health visualization, data logging, ambient displays

**Characteristics**:
- Provides visual feedback and monitoring
- Enhances operation but not critical for safety
- Can be restarted without data loss
- Robot remains functional if stopped
- Useful for debugging and status awareness

**Execution Context**: Background daemon (nohup, screen, or tmux)

**Expected Behavior**: Persists after SSH disconnect, but not auto-restarted on failure

**Current Examples**:
```python
SimpleTests/heartbeat_screensaver.py   # Ambient heart animation (18+ hrs proven)
SimpleTests/jetson_screensaver.py      # Wave animation display
SimpleTests/simple_screensaver.py      # Breathing color display
```

**Future Examples**:
```python
Monitors/system_health_display.py      # CPU/GPU/Memory visualization
Monitors/sensor_status_monitor.py      # Real-time sensor health
Monitors/training_data_collector.py    # Background data logging
Monitors/network_status_display.py     # Connectivity monitoring
```

**Usage Pattern**:

**Option A: nohup** (Simplest, recommended for most monitoring)
```bash
# Start with nohup to survive SSH disconnection
nohup python3 SimpleTests/heartbeat_screensaver.py > /tmp/heartbeat.log 2>&1 &

# Get the process ID
echo $!  # Save this PID

# Check if running
ps aux | grep heartbeat_screensaver

# View logs
tail -f /tmp/heartbeat.log

# Stop when needed
pkill -f heartbeat_screensaver.py
```

**Option B: screen** (When you need to reattach interactively)
```bash
# Start in screen session
screen -S heartbeat
python3 SimpleTests/heartbeat_screensaver.py

# Detach: Ctrl+A, then D
# Session continues running

# List sessions
screen -ls

# Reattach later
screen -r heartbeat

# Kill session
screen -X -S heartbeat quit
```

**Option C: tmux** (Similar to screen, more modern)
```bash
# Start in tmux session  
tmux new -s heartbeat
python3 SimpleTests/heartbeat_screensaver.py

# Detach: Ctrl+B, then D

# Reattach
tmux attach -t heartbeat

# Kill session
tmux kill-session -t heartbeat
```

**Implementation Requirements**:

1. **File-Based Logging**:
```python
import logging

# Log to file, not console
logging.basicConfig(
    filename='/tmp/heartbeat_screensaver.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

2. **Graceful Exit on SIGTERM**:
```python
import signal

def cleanup_and_exit(signum, frame):
    """Handle termination signal."""
    logger.info("Received SIGTERM, cleaning up...")
    display_manager.release()
    logger.info("Shutdown complete")
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup_and_exit)
```

3. **Docstring Documentation**:
```python
"""
heartbeat_screensaver.py

Ambient heartbeat visualization for Jetson display.

Execution for persistent operation:
    nohup python3 SimpleTests/heartbeat_screensaver.py > /tmp/heartbeat.log 2>&1 &

Status check:
    ps aux | grep heartbeat_screensaver
    tail -f /tmp/heartbeat.log

Stop:
    pkill -f heartbeat_screensaver.py
"""
```

---

## Program Naming Conventions

Use consistent naming to make program classification immediately clear:

```
Class 1: Development Tools
├── test_*.py           # Unit and integration tests
├── demo_*.py           # Interactive demonstrations
└── interactive_*.py    # Human-in-the-loop interfaces

Class 2: Critical Services
├── *_service.py        # Systemd services
├── *_control.py        # Autonomous control loops
└── *_monitor.py        # Safety monitoring (when critical)

Class 3: Background Monitoring
├── *_screensaver.py    # Ambient displays
├── *_monitor.py        # Non-critical system monitoring
└── *_logger.py         # Background data collection
```

---

## Decision Tree for New Programs

```
New Program Needed
        ↓
Does it interact with humans during operation?
    YES → Class 1 (Development Tool)
        - Place in SimpleTests/
        - Name with test_* or demo_* prefix
        - Execute via SSH
        - OK to terminate with SSH
        
    NO → Continue ↓
        
Is it critical for robot safety/operation?
    YES → Class 2 (Critical Service)
        - Place in Services/ (future directory)
        - Name with *_service.py suffix
        - Implement signal handling
        - Create systemd service file
        - Auto-restart on failure
        
    NO → Continue ↓
        
Does it enhance operation but isn't critical?
    YES → Class 3 (Background Monitor)
        - Can be in SimpleTests/ or Monitors/
        - Name with *_monitor.py or *_screensaver.py
        - Document nohup usage in docstring
        - Implement SIGTERM handler
        - Robot functions without it
```

---

## Migration Strategy

### Immediate (Completed)
- ✅ Document architecture in CONTRIBUTING.md
- ✅ Document architecture in README.md
- ✅ Create this detailed architecture guide
- ✅ Classify all current programs

### Near-Term (When Robot Control Development Starts)
1. Create `Services/` directory for Class 2 programs
2. Create `systemd/` directory for service files
3. Develop `RobotService` base class with common patterns
4. Create service installation scripts
5. Update managers to support graceful shutdown

### Long-Term (Ongoing)
1. Migrate critical functions to systemd services
2. Add service status dashboard
3. Implement health monitoring for all services
4. Create deployment automation
5. Document service dependencies and startup order

---

## Testing Against Architecture

### For Any New Program, Verify:

**Class 1 Programs (Development Tools)**:
- [ ] Located in `SimpleTests/`
- [ ] Has `test_*`, `demo_*`, or `interactive_*` prefix
- [ ] Outputs to console for developer
- [ ] Can be safely interrupted (Ctrl+C)
- [ ] No critical robot functions

**Class 2 Programs (Critical Services)**:
- [ ] Handles SIGTERM, SIGHUP, SIGINT
- [ ] Logs to journal or file (not console)
- [ ] Creates PID file
- [ ] Has systemd service file
- [ ] Releases all hardware on exit
- [ ] Tested with `systemctl start/stop/restart`
- [ ] Auto-restarts on failure
- [ ] Safe failure modes defined

**Class 3 Programs (Background Monitors)**:
- [ ] Documents nohup usage in docstring
- [ ] Logs to file
- [ ] Handles SIGTERM gracefully
- [ ] Releases hardware on exit
- [ ] Tested with nohup execution
- [ ] Verified persistence after SSH disconnect
- [ ] Robot functional without it

---

## Real-World Examples

### Example 1: Heartbeat Screensaver (Class 3)
**Discovery**: Ran for 18 hours successfully, stopped when SSH died (power outage)

**Solution**: Execute with nohup
```bash
nohup python3 SimpleTests/heartbeat_screensaver.py > /tmp/heartbeat.log 2>&1 &
```

**Verification**: Tested and confirmed continuous operation after SSH disconnect

**Status**: ✅ Working correctly with nohup

### Example 2: LocalLLM Manager (Class 2 Pattern)
**Implementation**: Spawns Ollama as independent subprocess

```python
self._ollama_process = subprocess.Popen(
    ["ollama", "serve"],
    env=env,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
```

**Result**: Ollama service survives even if LocalLLM_Manager exits

**Status**: ✅ Excellent example of service pattern

### Example 3: Future Robot Control (Class 2)
**Requirement**: Must run autonomously, survive all disconnections

**Implementation Plan**:
```python
# Services/robot_control_service.py
class RobotControlService:
    def __init__(self):
        self.setup_signal_handlers()
        self.create_pid_file()
        self.initialize_hardware()
        
    def run(self):
        """Main control loop"""
        while self.running:
            self.read_sensors()
            self.make_decisions()
            self.control_actuators()
            
    def shutdown(self):
        """Graceful shutdown"""
        self.motors.release()
        self.sensors.release()
        self.remove_pid_file()
```

**Deployment**:
```bash
sudo systemctl enable robot-control
sudo systemctl start robot-control
```

**Status**: 🔮 Future implementation

---

## Appendix: Systemd Best Practices

### Service File Sections

**[Unit]**: Metadata and dependencies
```ini
[Unit]
Description=Clear description of service
Documentation=file:///path/to/docs
After=network.target  # Start after network
Wants=ollama.service  # Optional dependency
```

**[Service]**: Execution configuration
```ini
[Service]
Type=simple              # Process doesn't fork
User=phiip              # Run as specific user
WorkingDirectory=/path  # Set working directory
ExecStart=/full/path    # Full path to executable
Restart=always          # Always restart on failure
RestartSec=10          # Wait 10s before restart
StandardOutput=journal  # Log to systemd journal
StandardError=journal
```

**[Install]**: Installation behavior
```ini
[Install]
WantedBy=multi-user.target  # Enable for multi-user mode
```

### Service Management Commands

```bash
# Install and enable
sudo cp service-file.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable service-name
sudo systemctl start service-name

# Status and logs
sudo systemctl status service-name
sudo journalctl -u service-name -f
sudo journalctl -u service-name --since "1 hour ago"

# Control
sudo systemctl stop service-name
sudo systemctl restart service-name
sudo systemctl reload service-name  # Sends SIGHUP

# Disable
sudo systemctl stop service-name
sudo systemctl disable service-name
```

---

## Summary

This architecture ensures the Jetson Orin Nano can function as a truly autonomous robot brain:

1. **Development tools** remain convenient and interactive
2. **Critical services** run reliably and independently  
3. **Background monitors** enhance operation without being critical

The key insight: **Not all programs should behave the same way.** Each class has different operational requirements that should be reflected in its implementation and deployment.

**Next Steps**: As robot control development progresses, migrate critical functions to systemd services following the patterns documented here.

---

**Document Maintenance**: Update this document as new architectural patterns emerge or requirements change.
