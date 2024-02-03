
import sys
import signal
import config
import numpy as np
import random
import math

# everything we need from PySide6
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QMainWindow, QGraphicsView,
    QGraphicsScene, QGraphicsRectItem, QGraphicsLineItem, QGraphicsEllipseItem,
    QGraphicsPathItem, QGraphicsDropShadowEffect, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QResizeEvent, QColor, QPen, QPainterPath


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

class DisplayQT:
    """
    DisplayQT class provides a fullscreen canvas using PySide6 for rendering graphics.

    Responsibilities:
    - Create a fullscreen canvas.
    - Provide methods for drawing points, lines, and other graphical elements.
    """

    def __init__(self, canvas_width, canvas_height):
        """
        Initialize the DisplayQT instance and create the resizable canvas with a fixed virtual size.
        """
        # Create the PySide6 application - this apparently shouldn't be here, so don't uncomment
        # self.app = QApplication(sys.argv)

        # store our params
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height

        # Create the fullscreen canvas
        aspect_ratio = canvas_width / canvas_height
        self.window = AspectRatioMainWindow(aspect_ratio)

        # Create the QGraphicsView and QGraphicsScene     
        self.scene = QGraphicsScene()
        self.view = CustomGraphicsView(self.scene, canvas_width, canvas_height)

        # Set the central widget of the QMainWindow to the QGraphicsView
        central_widget = QWidget()
        self.window.setCentralWidget(central_widget)

        # Add the QGraphicsView to the layout
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.setContentsMargins(0, 0, 0, 0)
        central_widget.setLayout(layout)

        # Set the window properties
        self.view.setFrameStyle(QGraphicsView.NoFrame)
        self.window.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.window.setMinimumSize(*config.QT["min_win_size"])

        # Default colors for stroke and fill
        self.stroke_color = QColor(*config.QT["default_stroke_color"]) 
        self.fill_color = QColor(*config.QT["default_fill_color"])
        self.color_fringing_on = config.QT["color_fringing_on"]  # Boolean for whether the laser glow effect is on
        self.fringing_color = QColor(*config.QT["fringing_color"]) 

        # Initialize an array to record each line, point, spline, or square
        # and clear the screen
        self.frame_reset()

        signal.signal(signal.SIGINT, self.handle_interrupt)

        # for testing
        self.rotation_angles = []  # Store rotation angles for each line


        self.window.show()  # Show the window here

    def handle_interrupt(self, signal, frame):
        self.app.quit()
        sys.exit(0)

    def frame_reset(self):
        """
        Clears the screen to the background color and initializes an array for recording graphical elements.
        """
        # Clear the scene
        self.scene.clear()

        # Set the background color
        self.scene.setBackgroundBrush(QColor(*config.QT["bkgd_color"]))

        # clear the elements array
        self.elements_array = []

    def set_stroke_color(self, r, g, b, a=config.QT["default_alpha"]):
        """
        Set the stroke color for drawing.
        """
        self.stroke_color = QColor(r, g, b, a)

    def set_fill_color(self, r, g, b, a=config.QT["default_alpha"]):
        """
        Set the fill color for drawing.
        """
        self.fill_color = QColor(r, g, b, a)

    def draw_point(self, x, y, size=config.QT["point_size"]):
        """
        Draw a point at the specified coordinates (x, y).
        """
        point = QGraphicsEllipseItem(x - size / 2, y - size / 2, size, size)
        point.setPen(QPen(self.stroke_color))
        point.setBrush(QColor(self.fill_color))
        if self.color_fringing_on:
            self.draw_with_fringing(point)
        else:
            self.scene.addItem(point)
        self.elements_array.append({'type': 'point', 'x': x, 'y': y, 'size': size})

    def draw_line(self, start_x, start_y, end_x, end_y):
        """
        Draw a line from (start_x, start_y) to (end_x, end_y).
        """
        line = QGraphicsLineItem(start_x, start_y, end_x, end_y)
        line.setPen(QPen(self.stroke_color))
        if self.color_fringing_on:
            self.draw_with_fringing(line)
        else:
            self.scene.addItem(line)
        self.elements_array.append({'type': 'line', 'start_x': start_x, 'start_y': start_y, 'end_x': end_x, 'end_y': end_y})

    def draw_spline(self, points):
        """
        Draw a spline (smooth curve) through the given points.
        """
        if len(points) < 2:
            return  # Need at least two points to draw a spline

        path = QPainterPath()
        path.moveTo(points[0][0], points[0][1])

        if len(points) == 2:
            # For two points, just draw a straight line
            path.lineTo(points[1][0], points[1][1])
        else:
            # Create a smooth curve using the points
            for i in range(1, len(points) - 1):
                # Control points could be calculated here for a more accurate spline
                # This is a simplification using mid-points
                mid_point_x = (points[i][0] + points[i + 1][0]) / 2
                mid_point_y = (points[i][1] + points[i + 1][1]) / 2
                path.quadTo(points[i][0], points[i][1], mid_point_x, mid_point_y)

            path.lineTo(points[-1][0], points[-1][1])

        spline = QGraphicsPathItem(path)
        spline.setPen(QPen(self.stroke_color))
        if self.color_fringing_on:
            self.draw_with_fringing(spline)
        else:
            self.scene.addItem(spline)
        self.elements_array.append({'type': 'spline', 'points': points})

    def draw_square(self, x, y, size):
        """
        Draw an unfilled square at the specified coordinates (x, y) with the given size.
        """
        square = QGraphicsRectItem(x, y, size, size)
        square.setPen(QPen(self.stroke_color))
        if self.color_fringing_on:
            self.draw_with_fringing(square)
        else:
            self.scene.addItem(square)
        self.elements_array.append({'type': 'square', 'x': x, 'y': y, 'size': size})

    # Additional drawing methods can be added here

    def draw_with_fringing(self, original_item, fringe_width=config.QT["fringe_width"]):
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
                display_object.setPath(original_item.path())  # Set the path for splines

            display_object.setPen(pen)
            display_object.setOpacity(opacity)
            display_object.setZValue(config.QT["fringe_z_value"])  # Set the z-value for the glow
            self.scene.addItem(display_object)

        # Add the original item on top of its glow
        self.scene.addItem(original_item)

    def draw_hotspot(self, x, y):
        """
        Draw a hotspot at the specified coordinates (x, y).
        """
        size = config.QT["hotspot_size"]  # Diameter of the hotspot
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
        # Extract line segments and endpoints from elements_array
        lines = []
        for e in self.elements_array:
            if e['type'] == 'line':
                lines.append(((e['start_x'], e['start_y']), (e['end_x'], e['end_y'])))
                # Add endpoints of the line
                self.draw_hotspot(e['start_x'], e['start_y'])
                self.draw_hotspot(e['end_x'], e['end_y'])
            elif e['type'] == 'spline':
                # Add endpoints of the spline
                self.draw_hotspot(e['points'][0][0], e['points'][0][1])
                self.draw_hotspot(e['points'][-1][0], e['points'][-1][1])
            elif e['type'] == 'square':
                # Add corners of the square
                x, y, size = e['x'], e['y'], e['size']
                self.draw_hotspot(x, y)
                self.draw_hotspot(x + size, y)
                self.draw_hotspot(x, y + size)
                self.draw_hotspot(x + size, y + size)
            elif e['type'] == 'point':
                # Add the point itself
                self.draw_hotspot(e['x'], e['y'])

        # Calculate intersections
        intersections = self.calculate_intersections(lines)

        # Draw hotspots at intersections
        for x, y in intersections:
            self.draw_hotspot(x, y)

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
    
    def run(self):
        """
        Start the PySide6 application event loop.
        """
        QApplication.instance().exec()
    
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
        self.frame_reset()  # Clear the scene

        for index, line in enumerate(self.test_lines):
            # Get the current position of the line endpoints
            start_x, start_y = line[0]
            end_x, end_y = line[1]

            # Calculate a fixed rotation angle for the line (e.g., 1 degree)
            rotation_angle = math.radians(1)  # Change the angle as needed

            # Accumulate the rotation angle for this line
            if len(self.rotation_angles) <= index:
                self.rotation_angles.append(0)
            self.rotation_angles[index] += rotation_angle

            # Calculate the center point of the line
            center_x = (start_x + end_x) / 2
            center_y = (start_y + end_y) / 2

            # Rotate the start point
            new_start_x = center_x + (start_x - center_x) * math.cos(self.rotation_angles[index]) - (start_y - center_y) * math.sin(self.rotation_angles[index])
            new_start_y = center_y + (start_x - center_x) * math.sin(self.rotation_angles[index]) + (start_y - center_y) * math.cos(self.rotation_angles[index])

            # Rotate the end point
            new_end_x = center_x + (end_x - center_x) * math.cos(self.rotation_angles[index]) - (end_y - center_y) * math.sin(self.rotation_angles[index])
            new_end_y = center_y + (end_x - center_x) * math.sin(self.rotation_angles[index]) + (end_y - center_y) * math.cos(self.rotation_angles[index])

            # Ensure the points stay within the canvas bounds
            new_start_x = max(0, min(self.canvas_width, new_start_x))
            new_start_y = max(0, min(self.canvas_height, new_start_y))
            new_end_x = max(0, min(self.canvas_width, new_end_x))
            new_end_y = max(0, min(self.canvas_height, new_end_y))

            # Draw the line with the updated endpoints
            self.draw_line(new_start_x, new_start_y, new_end_x, new_end_y)

        if config.QT["hotspots_on"]:
            self.draw_all_hotspots()  # Draw hotspots


if __name__ == "__main__":
    app = QApplication(sys.argv)
    canvas_width, canvas_height = config.QT["canvas_size"]  # Example canvas size

    display = DisplayQT(canvas_width, canvas_height)
    display.animation_test()  # Initialize and start the line animation
    display.run()