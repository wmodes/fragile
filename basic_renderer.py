import time
import config
import numpy as np
import math
import threading
import sys
from display_qt import DisplayQT
from display_web import DisplayWeb
# from PySide6.QtWidgets import QApplication

class BasicRenderer:
    """
    BasicRenderer handles low-level rendering of points, lines, irregular polygons, and splines.
    It provides the foundational drawing capabilities for the VisualComposer class.

    Responsibilities:
    - Render individual points.
    - Render line segments.
    - Render irregular polygons.
    - Render splines.
    - Apply binary dropouts (if specified) to line segments or splines.
    """

    def __init__(self):
        """Initialize the BasicRenderer with a list of display class instances."""
        self.displays = []

        # Store important canvas parameters
        self.canvas_width, self.canvas_height = config.QT["canvas_size"]

    def add_display(self, display):
        """
        Add a display class instance to the list of display classes.
        Start the display in a separate thread.
        """
        # thread = threading.Thread(target=display.start)
        # thread.start()
        display.start()  # Assumes display.start() is already non-blocking
        self.displays.append(display)
    
    def execute_command(self, command, *args):
        """
        Directly call a method on all displays corresponding to the command.
        """
        for display in self.displays:
            # Check if the display has the method corresponding to the command
            if hasattr(display, command):
                method = getattr(display, command)
                if callable(method):
                    # Call the method with args
                    method(*args)
            else:
                print(f"Display does not support command: {command}")

    # Specific drawing methods can utilize the generic execute_on_all_displays
    def frame_start(self):
        self.execute_command('frame_start')

    def frame_end(self):
        self.execute_command('frame_end')

    def draw_point(self, p0):
        self.execute_command('draw_point', p0)

    def draw_line(self, p0, p1):
        self.execute_command('draw_line', p0, p1)

    def draw_cubic_bezier(self, p0, p1, p2, p3):
        self.execute_command('draw_cubic_bezier', p0, p1, p2, p3)


    def apply_binary_dropout(self, element):
        """
        Apply binary dropout (if specified) to a line segment or spline.

        :param element: The line segment or spline to which dropout is applied.
        """
        pass

    # Additional methods for specific rendering functionalities can be added here.

    #
    # TEST CODE
    #

    def start_animation_test(self, duration=10):
        """
        Run the animation test for a given duration.
        :param duration: Duration in seconds for the animation test.
        """
        self.initialize_test_lines()
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(100)  # 100 milliseconds interval

        # Stop the animation after the specified duration
        self.stop_timer = QTimer()
        self.stop_timer.singleShot(duration * 1000, self.stop_animation)

    def update_animation(self):
        """
        Update the animation state and redraw elements on all displays.
        """
        self.update_lines()

    def stop_animation(self):
        """
        Stop the animation.
        """
        self.animation_timer.stop()

    def initialize_test_lines(self):
        """
        Initialize test lines for the animation.
        """
        self.test_lines = [
            [[500, 500], [1500, 1500]],  # A diagonal line
            # Add other lines as needed
        ]
        self.rotation_angles = [0] * len(self.test_lines)

    def update_lines(self):
        """
        Update the animation state for each line and redraw elements on all displays.
        """
        for index, line in enumerate(self.test_lines):
            p0, p1 = line
            rotation_angle = math.radians(1)  # Rotate 1 degree
            self.rotation_angles[index] += rotation_angle

            # Rotate each line around its center
            center_x = (p0[0] + p1[0]) / 2
            center_y = (p0[1] + p1[1]) / 2
            new_p0 = self.rotate_point(p0, center_x, center_y, self.rotation_angles[index])
            new_p1 = self.rotate_point(p1, center_x, center_y, self.rotation_angles[index])

            # Bound the new points within the canvas
            self.test_lines[index] = [self.bound_point(new_p0), self.bound_point(new_p1)]

        # Redraw elements on all displays
        self.execute_command('frame_reset')  # Clears the screen
        for line in self.test_lines:
            self.execute_command('draw_line', line[0], line[1])
        self.execute_command('frame_complete')

    def rotate_point(self, point, cx, cy, angle):
        """
        Rotate a point around a given center.
        """
        s, c = math.sin(angle), math.cos(angle)
        x, y = point[0] - cx, point[1] - cy
        new_x = x * c - y * s
        new_y = x * s + y * c
        return [new_x + cx, new_y + cy]

    def bound_point(self, point):
        """
        Ensure the point stays within the canvas bounds.
        """
        x, y = point
        return [max(0, min(self.canvas_width, x)), max(0, min(self.canvas_height, y))]



if __name__ == "__main__":
    # app = QApplication(sys.argv)  # Start QApplication      
    
    # Instantiate the BasicRenderer
    renderer = BasicRenderer()

    # Instantiate DisplayQT and add the display to the BasicRenderer
    # display_qt = DisplayQT()
    # renderer.add_display(display_qt)
    display_web = DisplayWeb()
    renderer.add_display(display_web)
    print("Display added")

    while not display_web.is_connected:
        time.sleep(0.1)
    # Clear the frame and draw some static lines
    renderer.frame_start()  # Clears the screen
    renderer.draw_line([100, 100], [300, 300])
    renderer.draw_line([300, 100], [100, 300])
    renderer.draw_line([200, 50], [200, 350])
    renderer.draw_line([50, 200], [350, 200])

