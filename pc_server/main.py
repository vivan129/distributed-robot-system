"""
PC Server - Main Orchestrator
Handles all processing and sends commands to Pi
"""

import asyncio
import logging
import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import yaml
from dotenv import load_dotenv

from modules.voice_input import VoiceRecognizer
from modules.ai_brain import AIBrain
from modules.tts_engine import TTSEngine
from modules.face_animator import FaceAnimator
from modules.slam_processor import SLAMProcessor
from modules.vision_processor import VisionProcessor
from modules.robot_controller import RobotController

# Load environment variables
load_dotenv()

# Load config
with open('../config/robot_config.yaml') as f:
    config = yaml.safe_load(f)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize modules
voice = VoiceRecognizer(config)
ai_brain = AIBrain(config)
tts = TTSEngine(config)
face = FaceAnimator(config)
slam = SLAMProcessor(config)
vision = VisionProcessor(config)
robot = RobotController(config, socketio)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RobotServer:
    def __init__(self):
        self.pi_connected = False
        self.is_talking = False
        self.is_moving = False
        
    async def process_voice_command(self, audio_data):
        """Main processing pipeline"""
        try:
            # 1. Speech to text
            text = await voice.recognize(audio_data)
            logger.info(f"Recognized: {text}")
            
            # 2. AI processing
            response, movement_cmd = await ai_brain.process(text)
            
            # 3. Execute movement if needed
            if movement_cmd:
                await robot.send_movement(movement_cmd)
            
            # 4. Generate TTS with phoneme timing
            audio_path, phoneme_timings = await tts.synthesize(response)
            
            # 5. Generate face animation keyframes
            face_animation = face.generate_lipsync(phoneme_timings)
            
            # 6. Send face animation to Pi display
            socketio.emit('face_animation', face_animation, room='pi_display')
            
            # 7. Send audio to Pi speakers
            await robot.send_audio(audio_path)
            
            # 8. Update PC dashboard
            socketio.emit('bot_response', {'text': response}, room='pc_dashboard')
            
        except Exception as e:
            logger.error(f"Error: {e}")


server = RobotServer()


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def dashboard():
    """PC control dashboard"""
    return render_template('dashboard.html')


# ============================================================================
# WEBSOCKET EVENTS
# ============================================================================

@socketio.on('connect', namespace='/pc')
def pc_connect():
    """PC dashboard connected"""
    logger.info("PC Dashboard connected")
    emit('status', {'connected': True}, room='pc_dashboard')


@socketio.on('connect', namespace='/pi')
def pi_connect():
    """Raspberry Pi connected"""
    logger.info("Raspberry Pi connected")
    server.pi_connected = True
    emit('status', {'connected': True}, broadcast=True)


@socketio.on('disconnect', namespace='/pi')
def pi_disconnect():
    """Pi disconnected"""
    logger.info("Raspberry Pi disconnected")
    server.pi_connected = False


@socketio.on('voice_data', namespace='/pc')
def handle_voice(data):
    """Receive voice from PC mic (or Pi mic forwarded)"""
    asyncio.create_task(server.process_voice_command(data['audio']))


@socketio.on('manual_command', namespace='/pc')
def manual_cmd(data):
    """Manual text command from dashboard"""
    asyncio.create_task(server.process_voice_command(data['text']))


@socketio.on('camera_frame', namespace='/pi')
def handle_camera(data):
    """Receive camera frame from Pi"""
    # Process with vision module
    processed = vision.process_frame(data['frame'])
    # Send to SLAM
    slam.add_visual_odometry(processed)
    # Broadcast to dashboard
    emit('camera_view', {'frame': data['frame']}, room='pc_dashboard')


@socketio.on('lidar_scan', namespace='/pi')
def handle_lidar(data):
    """Receive LiDAR scan from Pi"""
    slam.add_scan(data['ranges'], data['angles'])
    # Send updated map to dashboard
    map_data = slam.get_current_map()
    emit('slam_map', map_data, room='pc_dashboard')


@socketio.on('ultrasonic_data', namespace='/pi')
def handle_ultrasonic(data):
    """Obstacle detection"""
    distance = data['distance']
    if distance < config['obstacle_threshold']:
        # Emergency stop
        robot.send_stop()
        emit('obstacle_alert', {'distance': distance}, room='pc_dashboard')


if __name__ == '__main__':
    logger.info("="*60)
    logger.info("🖥️  ROBOT PC SERVER STARTING")
    logger.info("="*60)
    logger.info(f"🌐 Dashboard: http://localhost:{config['pc_port']}")
    logger.info(f"🤖 Waiting for Raspberry Pi at {config['pi_ip']}...")
    logger.info("="*60)
    
    socketio.run(app, 
                 host='0.0.0.0', 
                 port=config['pc_port'], 
                 debug=False)
