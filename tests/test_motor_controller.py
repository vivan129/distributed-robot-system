#!/usr/bin/env python3

"""

Unit tests for Motor Controller

Uses mock GPIO to allow testing without hardware

"""

import pytest

import sys

from unittest.mock import Mock, patch, MagicMock

import time

# Mock RPi.GPIO before importing motor_controller

sys.modules['RPi'] = MagicMock()

sys.modules['RPi.GPIO'] = MagicMock()

# Now we can import

from pi_client.hardware.motor_controller import MotorController

@pytest.fixture

def config():

"""Test configuration"""

return {

'motors': {

'pin_mode': 'BOARD',

'pins': {

'L1': 33,

'L2': 38,

'R1': 35,

'R2': 40

},

'pwm_frequency': 100,

'default_speed': 50,

'turn_speed': 40,

'timeout': 10

}

}

@pytest.fixture

def mock_gpio():

"""Mock GPIO module"""

with patch('pi_client.hardware.motor_controller.GPIO') as mock:

mock.BOARD = 10

mock.BCM = 11

mock.OUT = 0

mock.IN = 1

mock.HIGH = 1

mock.LOW = 0

yield mock

class TestMotorController:

"""Test suite for MotorController"""

def test_initialization(self, config, mock_gpio):

"""Test motor controller initialization"""

motors = MotorController(config)

# Check GPIO mode was set

mock_gpio.setmode.assert_called_once()

# Check pins were setup

assert mock_gpio.setup.call_count >= 4

# Check initial state

assert motors.is_moving == False

assert motors.current_direction is None

def test_move_forward(self, config, mock_gpio):

"""Test forward movement"""

motors = MotorController(config)

motors.move('forward', 2.0)

# Check motor state

assert motors.is_moving == True

assert motors.current_direction == 'forward'

# Verify GPIO outputs were set

assert mock_gpio.output.called

def test_move_backward(self, config, mock_gpio):

"""Test backward movement"""

motors = MotorController(config)

motors.move('backward', 2.0)

assert motors.is_moving == True

assert motors.current_direction == 'backward'

def test_turn_left(self, config, mock_gpio):

"""Test left turn"""

motors = MotorController(config)

motors.move('left', 1.0)

assert motors.is_moving == True

assert motors.current_direction == 'left'

def test_turn_right(self, config, mock_gpio):

"""Test right turn"""

motors = MotorController(config)

motors.move('right', 1.0)

assert motors.is_moving == True

assert motors.current_direction == 'right'

def test_stop(self, config, mock_gpio):

"""Test stop command"""

motors = MotorController(config)

# Start moving

motors.move('forward', 5.0)

assert motors.is_moving == True

# Stop

motors.stop()

assert motors.is_moving == False

assert motors.current_direction is None

# Verify all pins set to LOW

calls = mock_gpio.output.call_args_list

assert any(call[0][1] == mock_gpio.LOW for call in calls)

def test_movement_with_duration(self, config, mock_gpio):

"""Test timed movement"""

motors = MotorController(config)

motors.move('forward', 0.5)

assert motors.is_moving == True

# Wait for timer

time.sleep(0.6)

# Should have stopped

assert motors.is_moving == False

def test_invalid_direction(self, config, mock_gpio):

"""Test invalid direction handling"""

motors = MotorController(config)

motors.move('invalid_direction', 1.0)

# Should not be moving

assert motors.is_moving == False

def test_cleanup(self, config, mock_gpio):

"""Test GPIO cleanup"""

motors = MotorController(config)

motors.move('forward', 1.0)

motors.cleanup()

# Verify cleanup was called

mock_gpio.cleanup.assert_called()

# Verify motors stopped

assert motors.is_moving == False

def test_sequential_movements(self, config, mock_gpio):

"""Test multiple movements in sequence"""

motors = MotorController(config)

# First movement

motors.move('forward', 1.0)

assert motors.current_direction == 'forward'

# Second movement should cancel first

motors.move('backward', 1.0)

assert motors.current_direction == 'backward'

# Stop

motors.stop()

assert motors.current_direction is None

def test_get_status(self, config, mock_gpio):

"""Test status reporting"""

motors = MotorController(config)

# Initial status

status = motors.get_status()

assert status['is_moving'] == False

assert status['direction'] is None

# Moving status

motors.move('forward', 2.0)

status = motors.get_status()

assert status['is_moving'] == True

assert status['direction'] == 'forward'

class TestMotorControllerEdgeCases:

"""Test edge cases and error conditions"""

def test_zero_duration(self, config, mock_gpio):

"""Test movement with zero duration (indefinite)"""

motors = MotorController(config)

motors.move('forward', 0)

assert motors.is_moving == True

# Should not auto-stop

time.sleep(0.2)

assert motors.is_moving == True

# Manual stop required

motors.stop()

assert motors.is_moving == False

def test_negative_duration(self, config, mock_gpio):

"""Test negative duration handling"""

motors = MotorController(config)

motors.move('forward', -1.0)

# Should handle gracefully (treat as 0 or ignore)

# Implementation dependent

def test_rapid_commands(self, config, mock_gpio):

"""Test rapid successive commands"""

motors = MotorController(config)

for _ in range(10):

motors.move('forward', 0.1)

motors.move('backward', 0.1)

# Should handle without crashing

motors.stop()

def test_stop_without_movement(self, config, mock_gpio):

"""Test stop when not moving"""

motors = MotorController(config)

motors.stop()  # Should not crash

assert motors.is_moving == False

# Integration-style tests

class TestMotorControllerIntegration:

"""Integration tests simulating real usage patterns"""

def test_navigation_sequence(self, config, mock_gpio):

"""Test typical navigation sequence"""

motors = MotorController(config)

# Move forward

motors.move('forward', 0.2)

time.sleep(0.25)

# Turn right

motors.move('right', 0.1)

time.sleep(0.15)

# Move forward again

motors.move('forward', 0.2)

time.sleep(0.25)

# Stop

motors.stop()

assert motors.is_moving == False

def test_obstacle_avoidance_pattern(self, config, mock_gpio):

"""Test obstacle avoidance movement pattern"""

motors = MotorController(config)

# Forward until obstacle

motors.move('forward', 1.0)

time.sleep(0.3)

# Emergency stop (obstacle detected)

motors.stop()

assert motors.is_moving == False

# Back up

motors.move('backward', 0.5)

time.sleep(0.6)

# Turn

motors.move('left', 0.5)

time.sleep(0.6)

motors.stop()

if __name__ == '__main__':

pytest.main([__file__, '-v'])