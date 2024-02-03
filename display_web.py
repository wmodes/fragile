from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import time
import config
import math
import gevent.monkey
gevent.monkey.patch_all()

class DisplayWeb:
    """
    DisplayWeb runs a flask and socket server with it's own even loop running independently sending commands to a javascript app running in a webpage that it serves up. DisplayWeb is subservient to a BasicRenderer class which views DisplayWeb as a black box. The BasicRenderer class sends commands to DisplayWeb which are then sent to the javascript app running in the webpage. The javascript app then renders the commands on the canvas. DisplayWeb is responsible for:
    - Running a flask and socket server with it's own event loop
    - Serving up the webpage and static files, css, js, img, etc.
    - Sending commands as signals to a javascript client running in a webpage
    - Handling client connections and disconnections
    - Handling signals from the client
    - Running a test animation
    """
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'secret!'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='gevent')
        self.is_connected = False

        # route for serving the index.html file
        @self.app.route('/')
        def index():
            return render_template('index.html', config=config.WEB)
        
        # route for detecting client connection
        @self.socketio.on('connect')
        def handle_connect():
            self.is_connected = True
            print("Client connected")
            # self.animation_test()
            # You can also emit messages back to the client if needed
            # emit('message', {'data': 'Connected to server'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            self.is_connected = False
            print("Client disconnected")
            # Your disconnect handling code...

    def start(self):
        # Run the Flask app in a separate thread
        threading.Thread(target=self.socketio.run, args=(self.app,)).start()
        print("Web display started. Connect at http://127.0.0.1:5000/")

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

    #
    # TEST CODE
    #
        
    def send_test(self):
        """
        Send a test message to the client.
        """
        print("Sending test geometry")
        self.frame_start()     

        self.draw_point((300, 600))  # Draw a point away from the line

        # Draw lines
        self.draw_line((100, 100), (900, 700))  # Diagonal line across the canvas
        self.draw_line((500, 50), (500, 750))   # Vertical line

        # Draw a cubic Bezier curve
        p0 = (100, 700)   # Starting point
        p1 = (300, 200)   # Control point 1
        p2 = (700, 200)   # Control point 2
        p3 = (900, 700)   # Ending point
        self.draw_cubic_bezier(p0, p1, p2, p3)

        gevent.sleep(5)

        # self.frame_start() 
        # self.draw_line((500, 50), (500, 750))
        # gevent.sleep(1000)

        # self.frame_start() 
        # self.draw_line((450, 50), (450, 750))
        # gevent.sleep(1000)

        # self.frame_start() 
        # self.draw_line((400, 50), (400, 750))
        # gevent.sleep(1000)

        # self.frame_start() 
        # self.draw_line((350, 50), (350, 750))
        # gevent.sleep(1000)

        # self.frame_start() 
        # self.draw_line((300, 50), (300, 750))
        # gevent.sleep(1000)

        # self.frame_start() 
        # self.draw_line((250, 50), (250, 750))
        # gevent.sleep(1000)

        # self.frame_start() 
        # self.draw_line((200, 50), (200, 750))
        # gevent.sleep(1000)

        # self.frame_start() 
        # self.draw_line((150, 50), (150, 750))
        # gevent.sleep(1000)

        # self.frame_start() 
        # self.draw_line((100, 50), (100, 750))
        # gevent.sleep(1000)

        # self.frame_start() 
        # self.draw_line((50, 50), (50, 750))
        # gevent.sleep(1000)

     
    def animation_test(self, duration=120):
        """
        Run the animation test for a given duration.
        """
        print("Animation test started")
        self.initialize_test_lines()
        end_time = time.time() + duration

        while time.time() < end_time:
            self.update_lines()
            gevent.sleep(10)  # Update every 0.1 seconds
            self.frame_end()  # You might want to implement this to push updates if using websockets

    def initialize_test_lines(self):
        """
        Initialize test lines for the animation.
        """
        self.test_lines = [
            [[500, 500], [1500, 1500]],
            [[500, 1500], [1500, 500]],
            [[1000, 100], [1000, 1900]],
            [[100, 1000], [1900, 1000]]
        ]
        self.rotation_angles = [0] * len(self.test_lines)

    def update_lines(self):
        """
        Update the animation state for each line and redraw elements.
        """
        self.frame_start()  # Clear the frame before drawing

        for index, line in enumerate(self.test_lines):
            p0, p1 = line
            rotation_angle = math.radians(1)  # Rotate 1 degree
            self.rotation_angles[index] += rotation_angle

            # Rotate each line around its center
            center_x = (p0[0] + p1[0]) / 2
            center_y = (p0[1] + p1[1]) / 2
            new_p0 = self.rotate_point(p0, center_x, center_y, self.rotation_angles[index])
            new_p1 = self.rotate_point(p1, center_x, center_y, self.rotation_angles[index])

            # Draw the line with the updated endpoints
            self.draw_line((new_p0[0], new_p0[1]), (new_p1[0], new_p1[1]))

    def rotate_point(self, point, cx, cy, angle):
        """
        Rotate a point around a given center.
        """
        s, c = math.sin(angle), math.cos(angle)
        x, y = point[0] - cx, point[1] - cy
        new_x = x * c - y * s + cx
        new_y = x * s + y * c + cy
        return (new_x, new_y)


# Test condition
if __name__ == "__main__":
    display = DisplayWeb()
    display.start()


# TODO: Make sure this abstracts to the next level
# TODO: Add animation test
# TODO: Use a WSSGI server like gunicorn

