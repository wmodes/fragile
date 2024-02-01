from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import time
import config

class DisplayWeb:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'secret!'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        # route for serving the index.html file
        @self.app.route('/')
        def index():
            return render_template('index.html', config=config.WEB)
        
        # route for detecting client connection
        @self.socketio.on('connect')
        def handle_connect():
            print("Client connected")
            self.send_test()
            # You can also emit messages back to the client if needed
            # emit('message', {'data': 'Connected to server'})

    def start(self):
        # Run the Flask app in a separate thread
        threading.Thread(target=self.socketio.run, args=(self.app,)).start()

    # Define methods for rendering commands
    def frame_start(self):
        """
        Emit a signal to start a new frame on the frontend.
        """
        self.socketio.emit('message', {'command': 'frameStart'})
        # print("Frame start emitted")

    def frame_end(self):
        # Implementation for ending a frame
        self.socketio.emit('message', {'command': 'frameEnd'})
        # print("Frame end emitted")

    def draw_point(self, p0):
        # Emit the draw_point command with point coordinates and size
        point = {'x': p0[0], 'y': p0[1]}
        self.socketio.emit('message', {'command': 'drawPoint', 'params': {'point': point}})
        # print(f"Draw point at {p0}")

    def draw_line(self, p0, p1):
        # Emit the draw_line command with start and end points
        points = [{'x': p0[0], 'y': p0[1]}, {'x': p1[0], 'y': p1[1]}]
        self.socketio.emit('message', {'command': 'drawLine', 'params': {'points': points}})
        # print(f"Draw line from {p0} to {p1}")

    def draw_cubic_bezier(self, p0, p1, p2, p3):
        # Emit the draw_curve command with the curve control points
        points = [
            {'x': p0[0], 'y': p0[1]}, 
            {'x': p1[0], 'y': p1[1]}, 
            {'x': p2[0], 'y': p2[1]}, 
            {'x': p3[0], 'y': p3[1]}
        ]
        self.socketio.emit('message', {'command': 'drawCubicBezier', 'params': {'points': points}})
        # print(f"Draw cubic Bezier curve from {p0} to {p3}")

    def send_test(self):
        """
        Send a test message to the client.
        """
        display.frame_start()     

        display.draw_point((300, 600))  # Draw a point away from the line

        # Draw lines
        display.draw_line((100, 100), (900, 700))  # Diagonal line across the canvas
        display.draw_line((500, 50), (500, 750))   # Vertical line

        # Draw a cubic Bezier curve
        p0 = (100, 700)   # Starting point
        p1 = (300, 200)   # Control point 1
        p2 = (700, 200)   # Control point 2
        p3 = (900, 700)   # Ending point
        display.draw_cubic_bezier(p0, p1, p2, p3)
        time.sleep(0.25)

# Test condition
if __name__ == "__main__":
    display = DisplayWeb()
    display.start()
    print("Web display started. Connect at http://127.0.0.1:5000/")


