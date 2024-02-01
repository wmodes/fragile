

class DisplayWeb {
  constructor() {
    this.canvas = document.getElementById('displayCanvas');
    this.ctx = this.canvas.getContext('2d');
    this.container = document.getElementById('canvas-container');

    self.config = config;

    // Initial resize
    this.resizeCanvas();

    // Resize on window resize event
    window.addEventListener('resize', () => this.resizeCanvas());

    // SocketIO connection setup
    this.socket = io.connect('http://' + document.domain + ':' + location.port);

    this.socket.on('connect', () => {
      console.log('SocketIO connected');
    });
    
    // Generic SocketIO message event listener
    this.socket.on('message', (data) => {
      this.handleSocketMessage(data);
    });
  }

  resizeCanvas() {
    const container = document.getElementById('canvas-container');
    const contentPadding = 20; // Padding for the content element

    // Calculate the maximum width and height considering the padding
    const maxWidth = window.innerWidth - contentPadding * 2;
    const maxHeight = window.innerHeight - contentPadding * 2;

    // Determine the best fit for the 16:9 aspect ratio
    let containerWidth = maxWidth;
    let containerHeight = containerWidth * (9 / 16);
    if (containerHeight > maxHeight) {
      containerHeight = maxHeight;
      containerWidth = containerHeight * (16 / 9);
    }

    // Set the dimensions of the container and canvas
    container.style.width = `${containerWidth}px`;
    container.style.height = `${containerHeight}px`;
    this.canvas.width = containerWidth;
    this.canvas.height = containerHeight;
  }

  onWebSocketOpen() {
    console.log('WebSocket connection established');
  }

  onWebSocketError(error) {
    console.error('WebSocket Error:', error);
    console.log('WebSocket URL:', this.ws.url);
  }

  handleSocketMessage(data) {
    console.log('Received message:', data);
    switch (data.command) {
      case 'frameStart':
        this.frameStart();
        break;
      case 'frameEnd':
        this.frameEnd();
        break;
      case 'drawPoint':
        this.drawPoint(data.params.point);
        break;
      case 'drawLine':
        this.drawLine(data.params.points[0], data.params.points[1]);
        break;
      case 'drawCubicBezier':
        this.drawCubicBezier(data.params.points[0], data.params.points[1], data.params.points[2], data.params.points[3]);
        break;
      // Add more cases for other commands as needed
    }
  }

  frameStart() {
    console.log('Starting new frame');
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
  }

  frameEnd() {
    console.log('Ending frame');
    if (self.config.color_fringing) {
      // add fringing_on
    }
    if (self.config.hotspots_on) {
      // add hotspots
    }
  }  
  
  drawPoint(point) {
    console.log('Drawing point:', point);
    const size = config.point_size; 
    const color = `rgb(${config.default_stroke_color.join(',')})`;
    this.ctx.fillStyle = color; 
    this.ctx.beginPath();
    this.ctx.arc(point.x, point.y, size / 2, 0, 2 * Math.PI);
    this.ctx.fill();
  }

  drawLine(point1, point2) {
    console.log('Drawing line:', point1, point2);
    const color = `rgb(${config.default_stroke_color.join(',')})`;
    this.ctx.strokeStyle = color; 
    this.ctx.lineWidth = config.default_stroke_width; // Set stroke width
    this.ctx.beginPath();
    this.ctx.moveTo(point1.x, point1.y);
    this.ctx.lineTo(point2.x, point2.y);
    this.ctx.stroke();
  }

  drawCubicBezier(p0, p1, p2, p3) {
    console.log('Drawing cubic bezier:', p0, p1, p2, p3);
    const color = `rgb(${config.default_stroke_color.join(',')})`;
    this.ctx.strokeStyle = color; 
    this.ctx.lineWidth = config.default_stroke_width; // Set stroke width
    this.ctx.beginPath();
    this.ctx.moveTo(p0.x, p0.y);
    this.ctx.bezierCurveTo(p1.x, p1.y, p2.x, p2.y, p3.x, p3.y);
    this.ctx.stroke();
  }

  // Add more drawing functions as needed
}

console.log('Fragile.js loaded');
const displayWeb = new DisplayWeb(); // Instantiate the class