// TODO: Ensure the canvas minimum size is this.config.min_win_size
// TODO: Add hotspots according to this.config.hotspot_size
// TODO: Add hotspot and fringing switches to the UI

class DisplayWebClient {
  constructor() {
    this.canvas = document.getElementById('displayCanvas');
    this.ctx = this.canvas.getContext('2d');
    this.container = document.getElementById('canvas-container');

    this.config = config;
    this.fringing_on = config.color_fringing_on;
    this.hotspots_on = config.hotspots_on;

    this.elements_array = [];

    // handle resizing
    this.setupResizing();

    // SocketIO connection setup
    this.setupSocketIO()

    // Set control listeners
    this.setupControlListeners()
  }

  //
  // SocketIO
  //

  setupSocketIO() {
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

  onWebSocketOpen() {
    console.log('WebSocket connection established');
  }

  onWebSocketError(error) {
    console.error('WebSocket Error:', error);
    console.log('WebSocket URL:', this.ws.url);
  }

  async handleSocketMessage(data) {
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

  //
  // Controls
  //

  setupControlListeners() {

    // Listen for changes on fringing switch
    $('#switch-fringing').change(() => {
      this.fringing_on = $('#switch-fringing').is(':checked');
      // console.log("Fringing toggled:", this.fringing_on);
    });

    // Listen for changes on hotspots switch
    $('#switch-hotspots').change(() => {
      this.hotspots_on = $('#switch-hotspots').is(':checked');
      // console.log("Hotspots toggled:", this.hotspots_on);
    });

  }
  
  //
  // Resizing
  //

  setupResizing(){
    // Bind the debounced resizeCanvas method
    const debounceInterval = 250; // 250 milliseconds
    this.debouncedResizeCanvas = this.debounce(this.resizeCanvas, debounceInterval);

    // Attach the debounced resizeCanvas method to the window resize event
    window.addEventListener('resize', () => this.debouncedResizeCanvas());

    // Initial resize to set up the canvas
    this.resizeCanvas();
  }

  // Debounce function
  debounce(func, wait) {
    let timeout;
    return () => {
      const context = this, args = arguments;
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(context, args), wait);
    };
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

    this.redrawElements();
  }

  //
  // Scaling
  //

  scaleVirtual(point) {
    // Calculate scale factors based on actual vs. virtual canvas sizes
    const scaleX = this.canvas.width / this.config.canvas_size[0];
    const scaleY = this.canvas.height / this.config.canvas_size[1];
    
    // Return the scaled point
    return {
      x: point.x * scaleX,
      y: point.y * scaleY
    };
  }
  
  scaleNum(n) {
    // Calculate the scale factor based on the actual canvas dimensions and the virtual canvas size
    const scaleFactor = Math.min(this.canvas.width / this.config.canvas_size[0], this.canvas.height / this.config.canvas_size[1]);
    
    // Scale the input number by the scale factor
    return n * scaleFactor;
  }  

  //
  // Drawing Functions
  //

  frameStart() {
    console.log('Starting new frame');
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    this.elements_array = []; // Clear elements array
  }

  frameEnd() {
    console.log('Ending frame');
    if (this.fringing_on) {
      // add fringing_on
    }
    if (this.hotspots_on) {
      // add hotspots
    }
  }

  addFringing() {
    if (this.fringing_on) {
      this.ctx.shadowBlur = this.scaleNum(this.config.fringe_width);
      this.ctx.shadowColor = `rgba(${this.config.fringing_color.join(',')})`;
    } else {
      this.ctx.shadowBlur = 0;
    }
  }
  
  drawPoint(point) {
    console.log('Drawing point:', point);
    // attributes
    const size = this.scaleNum(this.config.point_size);
    const scaledPoint = this.scaleVirtual(point);
    const color = `rgb(${this.config.default_stroke_color.join(',')})`;
    this.ctx.fillStyle = color; 
    this.addFringing()
    // draw
    this.ctx.beginPath();
    this.ctx.arc(scaledPoint.x, scaledPoint.y, size / 2, 0, 2 * Math.PI);
    this.ctx.fill();
    // store
    this.elements_array.push({ command: 'drawPoint', params: { point } });
  }
  
  drawLine(point1, point2) {
    console.log('Drawing line:', point1, point2);
    // attributes
    const color = `rgb(${this.config.default_stroke_color.join(',')})`;
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = this.scaleNum(this.config.default_stroke_width);
    this.addFringing()
    // points
    const scaledPoint1 = this.scaleVirtual(point1);
    const scaledPoint2 = this.scaleVirtual(point2);
    // draw
    this.ctx.beginPath();
    this.ctx.moveTo(scaledPoint1.x, scaledPoint1.y);
    this.ctx.lineTo(scaledPoint2.x, scaledPoint2.y);
    this.ctx.stroke();
    // store
    this.elements_array.push({ command: 'drawLine', params: { points: [point1, point2] } });
  }
  
  drawCubicBezier(p0, p1, p2, p3) {
    console.log('Drawing cubic bezier:', p0, p1, p2, p3);
    // attributes
    const color = `rgb(${this.config.default_stroke_color.join(',')})`;
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = this.scaleNum(this.config.default_stroke_width);
    this.addFringing()
    // points
    const scaledP0 = this.scaleVirtual(p0);
    const scaledP1 = this.scaleVirtual(p1);
    const scaledP2 = this.scaleVirtual(p2);
    const scaledP3 = this.scaleVirtual(p3);
    // draw
    this.ctx.beginPath();
    this.ctx.moveTo(scaledP0.x, scaledP0.y);
    this.ctx.bezierCurveTo(scaledP1.x, scaledP1.y, scaledP2.x, scaledP2.y, scaledP3.x, scaledP3.y);
    this.ctx.stroke();
    // store
    this.elements_array.push({ command: 'drawCubicBezier', params: { points: [p0, p1, p2, p3] } });
  }

  redrawElements() {
    this.elements_array.forEach(item => {
      switch (item.command) {
        case 'drawPoint':
          this.drawPoint(item.params.point);
          break;
        case 'drawLine':
          this.drawLine(item.params.points[0], item.params.points[1]);
          break;
        case 'drawCubicBezier':
          this.drawCubicBezier(item.params.points[0], item.params.points[1], item.params.points[2], item.params.points[3]);
          break;
      }
    });
  }

  // Add more drawing functions as needed
}

console.log('Fragile.js loaded');
const displayWeb = new DisplayWebClient(); // Instantiate the class