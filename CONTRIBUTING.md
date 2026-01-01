# Contributing to Distributed Robot System

Thank you for your interest in contributing to the Distributed Robot System! This document provides guidelines and instructions for contributing.

## 🤝 How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:

1. **Clear title** describing the bug
2. **Steps to reproduce** the issue
3. **Expected behavior** vs **actual behavior**
4. **System information**:
   - OS version (Ubuntu/Raspbian)
   - Python version
   - Hardware specifications
   - Relevant configuration
5. **Error logs** or screenshots if applicable

### Suggesting Enhancements

For feature requests or enhancements:

1. Check if the feature is already requested in Issues
2. Create a new issue with:
   - Clear description of the feature
   - Use case and benefits
   - Potential implementation approach
   - Any relevant examples or references

### Pull Requests

We welcome pull requests! Here's the process:

#### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/distributed-robot-system.git
cd distributed-robot-system
```

#### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Adding or updating tests

#### 3. Make Your Changes

- Write clean, readable code
- Follow the existing code style
- Add comments for complex logic
- Update documentation if needed
- Write tests for new features

#### 4. Test Your Changes

```bash
# Run verification script
python scripts/verify_setup.py

# Test PC server
cd pc_server
python -m pytest tests/

# Test Pi client (on Raspberry Pi)
cd pi_client
python -m pytest tests/
```

#### 5. Commit Your Changes

Follow conventional commit format:

```bash
git commit -m "feat: add autonomous navigation mode"
git commit -m "fix: motor controller GPIO cleanup issue"
git commit -m "docs: update SLAM configuration guide"
```

Commit types:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Formatting, missing semicolons, etc.
- `refactor:` - Code restructuring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

#### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear description of changes
- Reference to related issues
- Screenshots/videos if applicable
- Test results

## 📝 Code Style Guidelines

### Python Style

We follow PEP 8 with some additional guidelines:

```python
# Use descriptive variable names
robot_speed = 0.5  # Good
s = 0.5  # Bad

# Add docstrings to all functions
def move_forward(duration: float) -> bool:
    """
    Move robot forward for specified duration.
    
    Args:
        duration: Movement duration in seconds
        
    Returns:
        True if movement successful, False otherwise
    """
    pass

# Use type hints
def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
    pass

# Keep functions focused and small
# If a function does more than one thing, split it

# Use constants for magic numbers
OBSTACLE_THRESHOLD = 30  # cm
MAX_SPEED = 100  # %
```

### File Organization

```python
# Import order:
# 1. Standard library
import os
import sys
from typing import Dict, List

# 2. Third-party packages
import numpy as np
import cv2

# 3. Local modules
from modules.motor_controller import MotorController
```

### Documentation

- Add docstrings to all public functions and classes
- Use inline comments for complex logic
- Update README.md for major changes
- Add examples for new features

## 🧪 Testing Guidelines

### Writing Tests

```python
import pytest
from modules.motor_controller import MotorController

def test_motor_initialization():
    """Test motor controller initialization"""
    config = {...}
    motors = MotorController(config)
    assert motors.is_moving == False

def test_motor_movement():
    """Test motor movement command"""
    motors = MotorController(config)
    motors.move('forward', 2.0)
    assert motors.is_moving == True
    assert motors.current_direction == 'forward'
```

### Test Coverage

- Unit tests for individual modules
- Integration tests for component interaction
- Hardware tests (mock GPIO for CI/CD)
- End-to-end tests for complete workflows

## 🏗️ Project Structure

```
distributed-robot-system/
├── pc_server/           # PC processing server
│   ├── modules/        # Processing modules
│   ├── templates/      # Web templates
│   └── static/         # Static assets
├── pi_client/          # Raspberry Pi client
│   ├── hardware/       # Hardware interfaces
│   └── display/        # Face display
├── config/             # Configuration files
├── scripts/            # Setup scripts
├── tests/              # Test suites
└── docs/               # Documentation
```

## 🐛 Debugging Tips

### Enable Debug Logging

```python
# In main.py
logging.basicConfig(level=logging.DEBUG)
```

### Test Individual Modules

```bash
# Test motor controller
python -m pi_client.hardware.motor_controller

# Test AI brain
python -m pc_server.modules.ai_brain

# Test TTS engine
python -m pc_server.modules.tts_engine
```

### Hardware Testing

```python
# Test GPIO pins
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(33, GPIO.OUT)
GPIO.output(33, GPIO.HIGH)
# Check with multimeter
```

## 🔐 Security Considerations

- Never commit API keys or secrets
- Use environment variables for sensitive data
- Sanitize user inputs
- Validate all data from network
- Implement proper authentication for web interfaces

## 📋 Checklist Before Submitting PR

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] No sensitive data in commits
- [ ] Commit messages follow conventions
- [ ] Branch is up to date with main
- [ ] PR description is clear and complete

## 🎯 Areas for Contribution

We especially welcome contributions in these areas:

### High Priority
- Advanced SLAM algorithms (Cartographer, ORB-SLAM)
- Object detection integration (YOLO, TensorFlow)
- Mobile app interface (React Native/Flutter)
- Path planning algorithms
- Unit test coverage

### Medium Priority
- Vision processing enhancements
- Face animation improvements
- Voice recognition alternatives
- Multi-robot coordination
- Performance optimization

### Good First Issues
- Documentation improvements
- Example scripts and tutorials
- Bug fixes
- Code cleanup and refactoring
- Additional sensor support

## 📞 Getting Help

- **GitHub Issues**: For bugs and features
- **GitHub Discussions**: For questions and ideas
- **Wiki**: For detailed documentation
- **Discord/Slack**: (Coming soon)

## 📜 Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behaviors:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards others

**Unacceptable behaviors:**
- Harassment, trolling, or derogatory comments
- Public or private harassment
- Publishing others' private information
- Other conduct inappropriate in a professional setting

### Enforcement

Project maintainers are responsible for clarifying standards and will take appropriate and fair corrective action in response to any unacceptable behavior.

## 🙏 Acknowledgments

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project website (when available)

Thank you for contributing to making robotics more accessible!

---

**Questions?** Open an issue or discussion on GitHub.

**Happy Coding!** 🤖