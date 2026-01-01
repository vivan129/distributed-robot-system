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

from modules.voice_input import VoiceInput
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
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'robot_secret_key_change_me')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize modules
voice = VoiceInput(config)
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
            text = voice.recognize_from_audio_data(audio_data)
            if not text:
                logger.warning("No speech recognized")
                return
                
            logger.info(f"Recognized: {text}")
            
            # 2. AI processing
            response, movement_cmd = ai_brain.process(text)
            
            # 3. Execute movement if needed
            if movement_cmd:
                await robot.send_movement(movement_cmd)
            
            # 4. Generate TTS with phoneme timing
            audio_path, phoneme_timings = await asyncio.to_thread(tts.synthesize, response)
            
            # 5. Generate face animation keyframes
            total_duration = phoneme_timings[-1]['offset'] + phoneme_timings[-1]['duration'] if phoneme_timings else 2.0
            face_animation = face.generate_lipsync(phoneme_timings, total_duration)
            
            # 6. Send face animation to Pi display
            await robot.send_face_animation(face_animation, total_duration)
            
            # 7. Send audio to Pi speakers
            await robot.send_audio(audio_path)
            
            # 8. Update PC dashboard
            socketio.emit('bot_response', {'text': response}, namespace='/pc')
            
        except Exception as e:
            logger.error(f"Error processing voice command: {e}", exc_info=True)


server = RobotServer()


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def dashboard():
    """PC control dashboard"""
    return render_template('dashboard.html')


# ============================================================================
# WEBSOCKET EVENTS - PC NAMESPACE
# ============================================================================

@socketio.on('connect', namespace='/pc')
def pc_connect():
    """PC dashboard connected"""
    logger.info("PC Dashboard connected")
    emit('status', {'connected': True, 'pi_connected': server.pi_connected})


@socketio.on('disconnect', namespace='/pc')
def pc_disconnect():
    """PC dashboard disconnected"""
    logger.info("PC Dashboard disconnected")


@socketio.on('voice_data', namespace='/pc')
def handle_voice(data):
    """Receive voice from PC mic"""
    asyncio.run(server.process_voice_command(data['audio']))


@socketio.on('manual_command', namespace='/pc')
def manual_cmd(data):
    """Manual text command from dashboard"""
    asyncio.run(server.process_voice_command(data['text'].encode()))


@socketio.on('movement_command', namespace='/pc')
def manual_movement(data):
    """Manual movement command from dashboard"""
    asyncio.run(robot.send_movement(data))


@socketio.on('stop_command', namespace='/pc')
def manual_stop(data):
    """Manual stop command"""
    asyncio.run(robot.send_stop())


# ============================================================================
# WEBSOCKET EVENTS - PI NAMESPACE
# ============================================================================

@socketio.on('connect', namespace='/pi')
def pi_connect():
    """Raspberry Pi connected"""
    logger.info("Raspberry Pi connected")
    server.pi_connected = True
    robot.set_pi_connection(request.sid, True)
    
    # Notify PC dashboard
    socketio.emit('pi_status', {'connected': True}, namespace='/pc')


@socketio.on('disconnect', namespace='/pi')
def pi_disconnect():
    """Pi disconnected"""
    logger.info("Raspberry Pi disconnected")
    server.pi_connected = False
    robot.set_pi_connection(None, False)
    
    # Notify PC dashboard
    socketio.emit('pi_status', {'connected': False}, namespace='/pc')


@socketio.on('pi_connected', namespace='/pi')
def pi_ready(data):
    """Pi reports ready status"""
    logger.info(f"Pi ready: {data}")


@socketio.on('camera_frame', namespace='/pi')
def handle_camera(data):
    """Receive camera frame from Pi"""
    try:
        # Process with vision module
        processed = vision.process_frame(data['frame'])
        
        # Send to SLAM if needed
        if processed:
            slam.add_visual_odometry(processed)
        
        # Broadcast to dashboard
        socketio.emit('camera_view', {'frame': data['frame']}, namespace='/pc')
        
    except Exception as e:
        logger.error(f"Camera frame processing error: {e}")


@socketio.on('lidar_scan', namespace='/pi')
def handle_lidar(data):
    """Receive LiDAR scan from Pi"""
    try:
        slam.add_scan(data['ranges'], data['angles'])
        
        # Send updated map to dashboard
        map_data = slam.get_current_map()
        
        # Convert numpy array to list for JSON serialization
        import base64
        import cv2
        _, buffer = cv2.imencode('.png', map_data)
        map_base64 = base64.b64encode(buffer).decode('utf-8')
        
        socketio.emit('slam_map', {'map': map_base64}, namespace='/pc')
        
    except Exception as e:
        logger.error(f"LiDAR processing error: {e}")


@socketio.on('ultrasonic_data', namespace='/pi')
def handle_ultrasonic(data):
    """Obstacle detection"""
    try:
        distance = data['distance']
        
        # Broadcast to dashboard
        socketio.emit('ultrasonic_data', {'distance': distance}, namespace='/pc')
        
        # Check safety threshold
        safety_config = config.get('safety', {})
        threshold = safety_config.get('obstacle_threshold', 30)
        
        if distance < threshold:
            # Emergency stop
            asyncio.run(robot.send_stop())
            socketio.emit('obstacle_alert', {'distance': distance}, namespace='/pc')
            logger.warning(f"Obstacle detected at {distance}cm - emergency stop triggered")
            
    except Exception as e:
        logger.error(f"Ultrasonic data processing error: {e}")


@socketio.on('movement_complete', namespace='/pi')
def handle_movement_complete(data):
    """Pi reports movement completed"""
    logger.info(f"Movement complete: {data}")
    socketio.emit('movement_status', {'status': 'complete', 'data': data}, namespace='/pc')


@socketio.on('stop_complete', namespace='/pi')
def handle_stop_complete(data):
    """Pi reports stop completed"""
    logger.info("Stop complete")
    socketio.emit('movement_status', {'status': 'stopped'}, namespace='/pc')


if __name__ == '__main__':
    from flask import request
    
    logger.info("="*60)
    logger.info("🖥️  ROBOT PC SERVER STARTING")
    logger.info("="*60)
    
    # Get network config
    network_config = config.get('network', {})
    pc_ip = network_config.get('pc_ip', '0.0.0.0')
    pc_port = network_config.get('pc_port', 5000)
    pi_ip = network_config.get('pi_ip', 'unknown')
    
    logger.info(f"✓ Gemini AI: {os.getenv('GEMINI_API_KEY', 'NOT SET')[:20]}...")
    logger.info(f"✓ TTS engine: Edge TTS")
    logger.info(f"✓ Face animator: Ready")
    logger.info(f"✓ SLAM processor: Initialized")
    logger.info(f"🌐 Dashboard: http://{pc_ip}:{pc_port}")
    logger.info(f"🤖 Waiting for Raspberry Pi at {pi_ip}...")
    logger.info("="*60)
    
    socketio.run(app, 
                 host='0.0.0.0', 
                 port=pc_port, 
                 debug=False,
                 allow_unsafe_werkzeug=True)