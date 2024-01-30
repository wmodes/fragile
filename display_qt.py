
import sys
import config
import numpy as np
import math
import threading

# everything we need from PySide6   
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QMainWindow, QGraphicsView,
    QGraphicsScene, QGraphicsRectItem, QGraphicsLineItem, QGraphicsEllipseItem,
    QGraphicsPathItem, QGraphicsDropShadowEffect, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QResizeEvent, QColor, QPen, QPainterPath


class DisplayQT(QObject):
    """
    DisplayQT class provides a fullscreen canvas using PySide6 for rendering graphics.

    Responsibilities:
    - Create a fullscreen canvas.
    - Provide methods for drawing points, lines, and other graphical elements.
    """

    # General command signal
    command_signal = Signal(str, tuple)

    def __init__(self):
        """
        Initialize the DisplayQT instance.
        """
        # Call the parent constructor
        super().__init__()

        # Store important canvas parameters
        self.canvas_width, self.canvas_height = config.qt_canvas_size

        # Default colors for stroke and fill
        self.stroke_color = QColor(*config.qt_default_stroke_color)
        self.fill_color = QColor(*config.qt_default_fill_color)
        self.color_fringing_on = config.qt_color_fringing_on
        self.fringing_color = QColor(*config.qt_fringing_color)

        # Initialize an array to record each line, point, curve, or square
        self.elements_array = []

        # Connect command signal to slot
        self.command_signal.connect(self.command_slot)

        # Rotation angles for testing
        self.rotation_angles = []
        
    def setup_ui(self):
        """
        Set up the UI components of the display.
        """
        # Create the fullscreen canvas
        aspect_ratio = self.canvas_width / self.canvas_height
        self.window = AspectRatioMainWindow(aspect_ratio)

        # Create the QGraphicsView and QGraphicsScene
        self.scene = QGraphicsScene()
        self.view = CustomGraphicsView(self.scene, self.canvas_width, self.canvas_height)

        # Set up the layout and window properties
        central_widget = QWidget()
        self.window.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.setContentsMargins(0, 0, 0, 0)
        central_widget.setLayout(layout)
        self.view.setFrameStyle(QGraphicsView.NoFrame)
        self.window.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.window.setMinimumSize(*config.qt_min_win_size)

        # Show the window
        self.window.show()

    def start_display(self):
        """Start the display and its event loop in the main thread."""
        # No need for a separate command processor thread
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()

        self.setup_ui()
        self.app.exec_()

    @Slot(str, tuple)
    def command_slot(self, command, args):
        """
        Slot to interpret and execute the command.
        """
        if hasattr(self, command):
            getattr(self, command)(*args)

    #
    # DISPLAY COMMANDS
    #

    def frame_start(self):
        """
        Clears the screen to the background color and initializes an array for recording graphical elements.
        """
        # Clear the scene
        self.scene.clear()

        # Set the background color
        self.scene.setBackgroundBrush(QColor(*config.qt_bkgd_color))

        # clear the elements array
        self.elements_array = []

    def frame_end(self):
        """
        Finishing touches to the frame including:
            - Drawing hotspots
        """
        if config.qt_hotspots_on:
            self.draw_all_hotspots()    

    def set_stroke_color(self, rgb, a=config.qt_default_alpha):
        """
        Set the stroke color for drawing.
        :param rgb: RGB color as a tuple (r, g, b).
        :param a: Alpha value.
        """
        r, g, b = rgb
        self.stroke_color = QColor(r, g, b, a)

    def set_fill_color(self, rgb, a=config.qt_default_alpha):
        """
        Set the fill color for drawing.
        :param rgb: RGB color as a tuple (r, g, b).
        :param a: Alpha value.
        """
        r, g, b = rgb
        self.fill_color = QColor(r, g, b, a)

    def draw_point(self, p0):
        """
        Draw a point at the specified coordinates p.
        :param p: Coordinates of the point (tuple of x, y).
        :param size: Size of the point.
        """
        x, y = p0
        size = config.qt_point_size
        point = QGraphicsEllipseItem(x - size / 2, y - size / 2, size, size)
        point.setPen(QPen(self.stroke_color))
        point.setBrush(QColor(self.fill_color))
        if self.color_fringing_on:
            self.draw_with_fringing(point)
        else:
            self.scene.addItem(point)
        self.elements_array.append({'type': 'point', 'points': [p0]})

    def draw_line(self, p0, p1):
        """
        Draw a line from p0 to p1.
        :param p0: Starting point of the line (tuple of x, y coordinates).
        :param p1: Ending point of the line (tuple of x, y coordinates).
        """
        line = QGraphicsLineItem(p0[0], p0[1], p1[0], p1[1])
        line.setPen(QPen(self.stroke_color))
        if self.color_fringing_on:
            self.draw_with_fringing(line)
        else:
            self.scene.addItem(line)
        self.elements_array.append({'type': 'line', 'points': [p0, p1]})
        print(f"draw line from {p0} to {p1}, color: {self.stroke_color}")

    def draw_cubic_bezier(self, p0, p1, p2, p3):
        """
        Draw a cubic Bezier curve with four control points.

        :param p0: Starting point of the curve (tuple).
        :param p1: First control point (tuple).
        :param p2: Second control point (tuple).
        :param p3: Ending point of the curve (tuple).
        """
        path = QPainterPath()
        path.moveTo(p0[0], p0[1])
        path.cubicTo(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1])

        curve = QGraphicsPathItem(path)
        curve.setPen(QPen(self.stroke_color))
        if self.color_fringing_on:
            self.draw_with_fringing(curve)
        else:
            self.scene.addItem(curve)
        self.elements_array.append({'type': 'cubic_bezier', 'points': [p0, p1, p2, p3]})

    # Additional drawing methods can be added here

    def draw_with_fringing(self, original_item, fringe_width=config.qt_fringe_width):
        """
        Apply a glow effect to the given QGraphicsItem if self.color_fringing_on is True.

        :param original_item: QGraphicsItem to which the glow effect is applied.
        :param fringe_width: Width of the glow effect.
        """
        if not self.color_fringing_on:
            self.scene.addItem(original_item)
            return

        for i in range(fringe_width, 0, -1):
            opacity = (fringe_width - i + 1) / fringe_width
            pen = QPen(self.fringing_color, i * 2, Qt.SolidLine)

            display_object = type(original_item)()  # Create a new item of the same type
            if isinstance(original_item, QGraphicsLineItem):
                display_object.setLine(original_item.line())
            elif isinstance(original_item, QGraphicsEllipseItem):
                display_object.setRect(original_item.rect())
            elif isinstance(original_item, QGraphicsRectItem):
                display_object.setRect(original_item.rect())
            elif isinstance(original_item, QGraphicsPathItem):
                display_object.setPath(original_item.path())  # Set the path for curves

            display_object.setPen(pen)
            display_object.setOpacity(opacity)
            display_object.setZValue(config.qt_fringe_z_value)  # Set the z-value for the glow
            self.scene.addItem(display_object)

        # Add the original item on top of its glow
        self.scene.addItem(original_item)

    def draw_hotspot(self, p0):
        """
        Draw a hotspot at the specified coordinates p0.
        :param p0: Coordinates of the hotspot (tuple of x, y).
        """
        x, y = p0
        size = config.qt_hotspot_size  # Diameter of the hotspot
        hotspot = QGraphicsEllipseItem(x - size / 2, y - size / 2, size, size)
        hotspot.setBrush(self.stroke_color)  # Set the color of the hotspot's fill
        pen = QPen(self.stroke_color)  # Use the stroke_color for the border as well
        pen.setWidth(1)  # Set the desired border width
        hotspot.setPen(pen)  # Apply the pen to the hotspot

        if self.color_fringing_on:
            self.draw_with_fringing(hotspot)
        else:
            self.scene.addItem(hotspot)

    def draw_all_hotspots(self):
        """
        Draw hotspots at endpoints and intersections of all elements.
        """
        lines = []
        for e in self.elements_array:
            if e['type'] == 'point':
                # Draw hotspot for the point
                self.draw_hotspot(e['points'][0])
            elif e['type'] == 'line':
                # Add line to the list for intersection calculation
                lines.append((e['points'][0], e['points'][1]))
                # Draw hotspots at endpoints of the line
                self.draw_hotspot(e['points'][0])
                self.draw_hotspot(e['points'][1])
            elif e['type'] == 'cubic_bezier':
                # Draw hotspots at endpoints of the cubic bezier curve
                self.draw_hotspot(e['points'][0])
                self.draw_hotspot(e['points'][-1])

        # Calculate intersections
        intersections = self.calculate_intersections(lines)

        # Draw hotspots at intersections
        for intersection in intersections:
            self.draw_hotspot(intersection)

    def calculate_intersections(self, lines):
        """
        Find intersections among all pairs of lines.
        Each line is defined by two points: ((x1, y1), (x2, y2)).
        """
        intersections = []
        for i in range(len(lines)):
            for j in range(i + 1, len(lines)):
                intersection = self.calculate_line_intersection(lines[i], lines[j])
                if intersection is not None:
                    intersections.append(intersection)
        return intersections

    def calculate_line_intersection(self, line1, line2):
        """
        Calculate the intersection point of two lines.
        Each line is defined by two points: ((x1, y1), (x2, y2)).
        """
        p0, p1 = np.array(line1[0]), np.array(line1[1])
        p2, p3 = np.array(line2[0]), np.array(line2[1])

        s10 = p1 - p0
        s32 = p3 - p2
        denom = np.cross(s10, s32)
        if denom == 0:
            return None  # Parallel lines

        t = np.cross(p2 - p0, s32) / denom
        if 0 <= t <= 1:
            intersection = p0 + t * s10
            return intersection.tolist()

        return None
    

    
    #
    # TEST CODE
    #
    
    def animation_test(self):
        # Initialize test lines as mutable lists
        self.test_lines = [
            [[500, 500], [1500, 1500]],  # A diagonal line across the canvas
            [[500, 1500], [1500, 500]],  # Another diagonal line, in the opposite direction
            [[1000, 100], [1000, 1000]],  # A vertical line near the center
            [[100, 1000], [1900, 1000]]   # A horizontal line near the center
        ]
        self.start_animation()

    def start_animation(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_lines)
        self.timer.start(10)  # Update every 100 milliseconds

    def update_lines(self):
        self.frame_start()  # Clear the scene

        for index, line in enumerate(self.test_lines):
            # Get the current position of the line endpoints
            p0x, p0y = line[0]
            p1x, p1y = line[1]

            # Calculate a fixed rotation angle for the line (e.g., 1 degree)
            rotation_angle = math.radians(1)  # Change the angle as needed

            # Accumulate the rotation angle for this line
            if len(self.rotation_angles) <= index:
                self.rotation_angles.append(0)
            self.rotation_angles[index] += rotation_angle

            # Calculate the center point of the line
            center_x = (p0x + p1x) / 2
            center_y = (p0y + p1y) / 2

            # Rotate the start point
            new_p0x = center_x + (p0x - center_x) * math.cos(self.rotation_angles[index]) - (p0y - center_y) * math.sin(self.rotation_angles[index])
            new_p0y = center_y + (p0x - center_x) * math.sin(self.rotation_angles[index]) + (p0y - center_y) * math.cos(self.rotation_angles[index])

            # Rotate the end point
            new_p1x = center_x + (p1x - center_x) * math.cos(self.rotation_angles[index]) - (p1y - center_y) * math.sin(self.rotation_angles[index])
            new_p1y = center_y + (p1x - center_x) * math.sin(self.rotation_angles[index]) + (p1y - center_y) * math.cos(self.rotation_angles[index])

            # Ensure the points stay within the canvas bounds
            new_p0x = max(0, min(self.canvas_width, new_p0x))
            new_p0y = max(0, min(self.canvas_height, new_p0y))
            new_p1x = max(0, min(self.canvas_width, new_p1x))
            new_p1y = max(0, min(self.canvas_height, new_p1y))

            # Draw the line with the updated endpoints
            self.draw_line((new_p0x, new_p0y), (new_p1x, new_p1y))

        if config.qt_hotspots_on:
            self.draw_all_hotspots()  # Draw hotspots



class AspectRatioMainWindow(QMainWindow):
    def __init__(self, aspect_ratio, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aspect_ratio = aspect_ratio

    def resizeEvent(self, event):
        size = self.size()
        new_width = size.height() * self.aspect_ratio
        new_height = size.width() / self.aspect_ratio

        if new_width != size.width():
            self.resize(int(new_width), size.height())
        elif new_height != size.height():
            self.resize(size.width(), int(new_height))
        super().resizeEvent(event)

class CustomGraphicsView(QGraphicsView):
    def __init__(self, scene, canvas_width, canvas_height):
        super().__init__(scene)
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.setSceneRect(0, 0, canvas_width, canvas_height)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)



if __name__ == "__main__":
    app = QApplication(sys.argv)

    display = DisplayQT()
    display.animation_test()  # Initialize and start the line animation
    display.run()