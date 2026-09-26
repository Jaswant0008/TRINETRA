/**
 * TRINETRA Official Knowledge Network Graph Visualizer
 * Conforms to Section 8 (Subtle node colors: People blue, Org green, Location gold, Event orange, Equipment grey)
 */
class OfficialGraphVisualizer {
  constructor(canvasId, onNodeSelect) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.onNodeSelect = onNodeSelect;

    this.nodes = [];
    this.edges = [];
    this.nodeMap = new Map();
    this.selectedCategory = 'ALL';
    this.searchQuery = '';

    // Camera settings
    this.camera = { x: 0, y: 0, zoom: 1 };
    this.isDragging = false;
    this.dragNode = null;
    this.lastMouse = { x: 0, y: 0 };
    this.hoverNode = null;

    this.simSpeed = 0.85;
    this._setupCanvas();
    this._bindEvents();
    this._startLoop();
  }

  _setupCanvas() {
    const parent = this.canvas.parentElement;
    const rect = parent.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.width = rect.width || 800;
    this.height = (rect.height && rect.height > 100) ? rect.height : (parseInt(parent.style?.height) || 400);
    this.canvas.width = this.width * dpr;
    this.canvas.height = this.height * dpr;
    this.ctx.scale(dpr, dpr);

    this.camera.x = this.width / 2;
    this.camera.y = this.height / 2;
  }

  resize() {
    const parent = this.canvas.parentElement;
    if (!parent) return;
    const rect = parent.getBoundingClientRect();
    if (rect.width === 0) return;
    const dpr = window.devicePixelRatio || 1;
    this.width = rect.width;
    this.height = (rect.height && rect.height > 100) ? rect.height : (parseInt(parent.style?.height) || 400);
    this.canvas.width = this.width * dpr;
    this.canvas.height = this.height * dpr;
    this.ctx.scale(dpr, dpr);
    this.autoFit();
  }

  setData(graphData) {
    const prevPos = new Map();
    this.nodes.forEach(n => prevPos.set(n.id, { x: n.x, y: n.y, vx: n.vx, vy: n.vy }));

    this.nodeMap.clear();
    const rawNodes = graphData.nodes || [];
    
    // Check if there is a primary hub node (like Sector Alpha)
    const hubNode = rawNodes.find(n => n.name.toLowerCase().includes('sector') || n.name.toLowerCase().includes('base')) || rawNodes[0];

    this.nodes = rawNodes.map((n, idx) => {
      const prev = prevPos.get(n.id);
      let posX = 0;
      let posY = 0;

      if (prev) {
        posX = prev.x;
        posY = prev.y;
      } else if (hubNode && n.id === hubNode.id) {
        posX = 0;
        posY = 0;
      } else {
        const others = rawNodes.filter(rn => rn.id !== (hubNode ? hubNode.id : null));
        const otherIdx = others.findIndex(rn => rn.id === n.id);
        const count = Math.max(others.length, 1);
        const angle = (otherIdx / count) * 2 * Math.PI;
        const radius = 160 + (otherIdx % 3) * 35;
        posX = Math.cos(angle) * radius;
        posY = Math.sin(angle) * radius;
      }

      const nodeObj = {
        ...n,
        x: posX,
        y: posY,
        vx: prev ? prev.vx : 0,
        vy: prev ? prev.vy : 0,
        radius: (hubNode && n.id === hubNode.id) ? 26 : 20
      };
      this.nodeMap.set(n.id, nodeObj);
      return nodeObj;
    });

    const rawEdges = graphData.edges || [];
    this.edges = rawEdges.map(e => ({
      ...e,
      sourceNode: this.nodeMap.get(e.subject_id || e.source),
      targetNode: this.nodeMap.get(e.object_id || e.target)
    })).filter(e => e.sourceNode && e.targetNode);

    this.simSpeed = 0.85;
    this.autoFit();
  }

  setCategoryFilter(category) {
    this.selectedCategory = category;
  }

  setSearchQuery(q) {
    this.searchQuery = (q || '').toLowerCase().trim();
  }

  highlightEntities(entityNames) {
    if (!entityNames || entityNames.length === 0) {
      this.highlightedNames = null;
      return;
    }
    this.highlightedNames = new Set(entityNames.map(n => n.toLowerCase().trim()));
    // Center camera on the first matching node
    const target = this.nodes.find(n => this.highlightedNames.has(n.name.toLowerCase().trim()));
    if (target) {
      this.camera.x = this.width / 2 - target.x * this.camera.zoom;
      this.camera.y = this.height / 2 - target.y * this.camera.zoom;
    }
    // Auto-clear highlight after 8 seconds
    if (this._highlightTimeout) clearTimeout(this._highlightTimeout);
    this._highlightTimeout = setTimeout(() => {
      this.highlightedNames = null;
    }, 8000);
  }

  autoFit() {
    if (!this.nodes || this.nodes.length === 0) return;
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    for (const n of this.nodes) {
      if (n.x < minX) minX = n.x;
      if (n.x > maxX) maxX = n.x;
      if (n.y < minY) minY = n.y;
      if (n.y > maxY) maxY = n.y;
    }
    const graphWidth = Math.max(maxX - minX + 180, 240);
    const graphHeight = Math.max(maxY - minY + 180, 240);
    const scaleX = this.width / graphWidth;
    const scaleY = this.height / graphHeight;
    this.camera.zoom = Math.min(Math.max(Math.min(scaleX, scaleY) * 0.85, 0.4), 1.3);
    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;
    this.camera.x = this.width / 2 - centerX * this.camera.zoom;
    this.camera.y = this.height / 2 - centerY * this.camera.zoom;
  }

  resetView() {
    this.autoFit();
  }

  zoomIn() {
    this.camera.zoom = Math.min(this.camera.zoom * 1.25, 3.0);
  }

  zoomOut() {
    this.camera.zoom = Math.max(this.camera.zoom / 1.25, 0.3);
  }

  _bindEvents() {
    window.addEventListener('resize', () => this.resize());

    this.canvas.addEventListener('mousedown', (e) => {
      const mouse = this._getTransformedMouse(e);
      const clicked = this._findNodeAt(mouse.x, mouse.y);
      if (clicked) {
        this.dragNode = clicked;
        if (this.onNodeSelect) this.onNodeSelect(clicked);
      } else {
        this.isDragging = true;
      }
      this.lastMouse = { x: e.clientX, y: e.clientY };
    });

    window.addEventListener('mousemove', (e) => {
      const mouse = this._getTransformedMouse(e);
      this.hoverNode = this._findNodeAt(mouse.x, mouse.y);
      this.canvas.style.cursor = this.hoverNode ? 'pointer' : (this.isDragging ? 'grabbing' : 'grab');

      if (this.dragNode) {
        this.dragNode.x = mouse.x;
        this.dragNode.y = mouse.y;
        this.dragNode.vx = 0;
        this.dragNode.vy = 0;
        this.simSpeed = Math.max(this.simSpeed, 0.3);
      } else if (this.isDragging) {
        const dx = e.clientX - this.lastMouse.x;
        const dy = e.clientY - this.lastMouse.y;
        this.camera.x += dx;
        this.camera.y += dy;
        this.lastMouse = { x: e.clientX, y: e.clientY };
      }
    });

    window.addEventListener('mouseup', () => {
      this.isDragging = false;
      this.dragNode = null;
    });

    this.canvas.addEventListener('wheel', (e) => {
      e.preventDefault();
      const factor = e.deltaY < 0 ? 1.1 : 0.9;
      const newZoom = Math.min(Math.max(this.camera.zoom * factor, 0.3), 3.0);
      const rect = this.canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;

      this.camera.x = mx - (mx - this.camera.x) * (newZoom / this.camera.zoom);
      this.camera.y = my - (my - this.camera.y) * (newZoom / this.camera.zoom);
      this.camera.zoom = newZoom;
    });
  }

  _getTransformedMouse(e) {
    const rect = this.canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    return {
      x: (mx - this.camera.x) / this.camera.zoom,
      y: (my - this.camera.y) / this.camera.zoom
    };
  }

  _findNodeAt(x, y) {
    for (let i = this.nodes.length - 1; i >= 0; i--) {
      const node = this.nodes[i];
      if (this._isNodeFiltered(node)) continue;
      const dist = Math.hypot(node.x - x, node.y - y);
      if (dist <= node.radius + 6) return node;
    }
    return null;
  }

  _isNodeFiltered(node) {
    if (this.selectedCategory !== 'ALL' && node.category !== this.selectedCategory && node.type !== this.selectedCategory) {
      return true;
    }
    if (this.searchQuery && !node.name.toLowerCase().includes(this.searchQuery)) {
      return true;
    }
    return false;
  }

  _getNodeColor(category) {
    // 2026 Defence-Intelligence Category Palette
    switch (category) {
      case 'People': return '#38bdf8';       // Intelligence Cyan/Blue
      case 'Organizations': return '#22c55e';// Tactical Military Green
      case 'Locations': return '#f59e0b';    // Tactical Amber/Gold
      case 'Events': return '#fb923c';       // Strategic Orange
      case 'Equipment': return '#94a3b8';    // Slate/Gunmetal Grey
      default: return '#38bdf8';
    }
  }

  _simulate() {
    if (this.simSpeed < 0.01) return;

    for (let i = 0; i < this.nodes.length; i++) {
      for (let j = i + 1; j < this.nodes.length; j++) {
        const n1 = this.nodes[i];
        const n2 = this.nodes[j];
        const dx = n2.x - n1.x;
        const dy = n2.y - n1.y;
        const dist = Math.hypot(dx, dy) || 1;
        if (dist < 260) {
          const force = (260 - dist) / dist * 0.12 * this.simSpeed;
          n1.vx -= dx * force;
          n1.vy -= dy * force;
          n2.vx += dx * force;
          n2.vy += dy * force;
        }
      }
    }

    for (const edge of this.edges) {
      const n1 = edge.sourceNode;
      const n2 = edge.targetNode;
      const dx = n2.x - n1.x;
      const dy = n2.y - n1.y;
      const dist = Math.hypot(dx, dy) || 1;
      const targetDist = 160;
      const force = (dist - targetDist) * 0.015 * this.simSpeed;
      n1.vx += (dx / dist) * force;
      n1.vy += (dy / dist) * force;
      n2.vx -= (dx / dist) * force;
      n2.vy -= (dy / dist) * force;
    }

    for (const node of this.nodes) {
      if (node === this.dragNode) continue;
      node.vx -= node.x * 0.003 * this.simSpeed;
      node.vy -= node.y * 0.003 * this.simSpeed;
      node.x += node.vx;
      node.y += node.vy;
      node.vx *= 0.82;
      node.vy *= 0.82;
    }

    this.simSpeed *= 0.992;
  }

  _startLoop() {
    const render = () => {
      this._simulate();
      this._draw();
      requestAnimationFrame(render);
    };
    requestAnimationFrame(render);
  }

  _draw() {
    this.ctx.clearRect(0, 0, this.width, this.height);

    this.ctx.save();
    this.ctx.translate(this.camera.x, this.camera.y);
    this.ctx.scale(this.camera.zoom, this.camera.zoom);

    // Draw Subtle Grid
    this.ctx.strokeStyle = '#1e293b';
    this.ctx.lineWidth = 1;
    const size = 1000;
    const step = 80;
    for (let x = -size; x <= size; x += step) {
      this.ctx.beginPath();
      this.ctx.moveTo(x, -size);
      this.ctx.lineTo(x, size);
      this.ctx.stroke();
    }
    for (let y = -size; y <= size; y += step) {
      this.ctx.beginPath();
      this.ctx.moveTo(-size, y);
      this.ctx.lineTo(size, y);
      this.ctx.stroke();
    }

    // Draw Edges (Triples)
    for (const edge of this.edges) {
      if (this._isNodeFiltered(edge.sourceNode) || this._isNodeFiltered(edge.targetNode)) continue;
      const src = edge.sourceNode;
      const tgt = edge.targetNode;
      const isHovered = (this.hoverNode === src || this.hoverNode === tgt);

      this.ctx.beginPath();
      this.ctx.moveTo(src.x, src.y);
      this.ctx.lineTo(tgt.x, tgt.y);
      this.ctx.strokeStyle = isHovered ? '#38bdf8' : '#334155';
      this.ctx.lineWidth = isHovered ? 2.5 : 1.5;
      this.ctx.stroke();

      // Predicate Text
      const midX = (src.x + tgt.x) / 2;
      const midY = (src.y + tgt.y) / 2;
      this.ctx.font = '10px "JetBrains Mono", monospace';
      this.ctx.fillStyle = isHovered ? '#ffffff' : '#94a3b8';
      this.ctx.textAlign = 'center';
      this.ctx.fillText(edge.predicate, midX, midY - 6);
    }

    // Draw Nodes
    for (const node of this.nodes) {
      if (this._isNodeFiltered(node)) continue;
      const isHovered = (this.hoverNode === node);
      const isHighlighted = this.highlightedNames && this.highlightedNames.has(node.name.toLowerCase().trim());
      const color = this._getNodeColor(node.category || node.type);

      // Highlight Glow Ring
      if (isHighlighted) {
        this.ctx.beginPath();
        this.ctx.arc(node.x, node.y, node.radius + 10, 0, Math.PI * 2);
        this.ctx.strokeStyle = '#38bdf8';
        this.ctx.lineWidth = 3;
        this.ctx.setLineDash([4, 4]);
        this.ctx.stroke();
        this.ctx.setLineDash([]);
      }

      // Node base
      this.ctx.beginPath();
      this.ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
      this.ctx.fillStyle = '#0f172a';
      this.ctx.fill();
      this.ctx.lineWidth = (isHovered || isHighlighted) ? 3.5 : 2;
      this.ctx.strokeStyle = isHighlighted ? '#38bdf8' : color;
      this.ctx.stroke();

      // Node Core
      this.ctx.beginPath();
      this.ctx.arc(node.x, node.y, isHighlighted ? 8 : 6, 0, Math.PI * 2);
      this.ctx.fillStyle = isHighlighted ? '#38bdf8' : color;
      this.ctx.fill();

      // Conflict warning indicator if applicable
      if (node.has_conflict) {
        this.ctx.beginPath();
        this.ctx.arc(node.x + 14, node.y - 14, 5, 0, Math.PI * 2);
        this.ctx.fillStyle = '#dc2626';
        this.ctx.fill();
      }

      // Label
      this.ctx.font = isHighlighted ? '700 13px "Outfit", sans-serif' : '600 12px "Outfit", sans-serif';
      this.ctx.fillStyle = (isHovered || isHighlighted) ? '#ffffff' : '#e2e8f0';
      this.ctx.textAlign = 'center';
      this.ctx.fillText(node.name, node.x, node.y + node.radius + 15);
    }

    this.ctx.restore();
  }
}
