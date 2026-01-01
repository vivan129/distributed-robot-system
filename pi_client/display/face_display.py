"""Face display server for animated robot face."""

import logging
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import threading

logger = logging.getLogger(__name__)


class FaceDisplay:
    """Web server for displaying animated robot face."""
    
    def __init__(self, config: dict):
        """Initialize face display server.
        
        Args:
            config: Configuration dict with display settings
        """
        self.config = config
        self.display_config = config['display']
        self.port = config['network']['pi_display_port']
        
        # Create Flask app
        self.app = Flask(__name__,
                         template_folder='templates',
                         static_folder='static')
        self.app.config['SECRET_KEY'] = 'robot_face_display'
        
        # Initialize SocketIO
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Current animation state
        self.current_animation = None
        self.is_speaking = False
        
        self._setup_routes()
        self._setup_socketio_events()
        
        logger.info(f"Face display server initialized on port {self.port}")
    
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            """Render main face display page."""
            return render_template('face.html',
                                 width=self.display_config['width'],
                                 height=self.display_config['height'],
                                 fullscreen=self.display_config['fullscreen'])
        
        @self.app.route('/status')
        def status():
            """Get display status."""
            return jsonify({
                'running': True,
                'is_speaking': self.is_speaking,
                'config': self.display_config
            })
    
    def _setup_socketio_events(self):
        """Setup SocketIO event handlers."""
        
        @self.socketio.on('connect')
        def handle_connect():
            logger.info('Display client connected')
            emit('config', {
                'width': self.display_config['width'],
                'height': self.display_config['height'],
                'face': self.display_config['face']
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info('Display client disconnected')
    
    def update_animation(self, animation_data: dict):
        """Send animation update to display.
        
        Args:
            animation_data: Animation keyframes and parameters
        """
        self.current_animation = animation_data
        self.socketio.emit('animate', animation_data)
        logger.debug(f"Animation update sent: {animation_data.get('type', 'unknown')}")
    
    def start_speaking(self, phonemes: list):
        """Start lip-sync animation.
        
        Args:
            phonemes: List of phoneme timings for lip-sync
        """
        self.is_speaking = True
        self.socketio.emit('start_speaking', {'phonemes': phonemes})
        logger.info("Started lip-sync animation")
    
    def stop_speaking(self):
        """Stop lip-sync animation."""
        self.is_speaking = False
        self.socketio.emit('stop_speaking', {})
        logger.info("Stopped lip-sync animation")
    
    def set_expression(self, expression: str):
        """Set facial expression.
        
        Args:
            expression: Expression name (happy, sad, surprised, neutral, etc.)
        """
        self.socketio.emit('set_expression', {'expression': expression})
        logger.info(f"Expression set to: {expression}")
    
    def run(self, host: str = '0.0.0.0'):
        """Run the display server.
        
        Args:
            host: Host to bind to (default: all interfaces)
        """
        logger.info(f"Starting face display server on {host}:{self.port}")
        self.socketio.run(self.app, host=host, port=self.port, debug=False)
    
    def run_in_thread(self, host: str = '0.0.0.0'):
        """Run server in background thread.
        
        Args:
            host: Host to bind to
        """
        thread = threading.Thread(
            target=self.run,
            args=(host,),
            daemon=True
        )
        thread.start()
        logger.info(f"✓ Face display server running in background")
        return thread
