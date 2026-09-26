/**
 * TRINETRA Tactical Map & Visual Overlay Inspector (Section 9.B & 9.D)
 */
class TacticalMapViewer {
  constructor(containerId, onMarkerClick) {
    this.container = document.getElementById(containerId);
    this.onMarkerClick = onMarkerClick;
    this.currentImage = null;
    this.markers = [];
    this.zoomLevel = 1;
    this._renderUI();
  }

  _renderUI() {
    this.container.innerHTML = `
      <div class="map-canvas-container" id="map-inner-container">
        <div class="map-hud-toolbar" style="position: absolute; top: 12px; right: 12px; z-index: 30; display: flex; gap: 6px;">
          <button class="btn btn-outline" id="btn-map-zoom-in" style="padding: 6px 10px;" title="Zoom In">+</button>
          <button class="btn btn-outline" id="btn-map-zoom-out" style="padding: 6px 10px;" title="Zoom Out">-</button>
          <button class="btn btn-outline" id="btn-map-reset" style="padding: 6px 10px;" title="Reset View">Fit</button>
        </div>
        <img class="map-image-element" id="map-img-elem" src="" alt="Tactical Map" style="display: none;" />
        <div class="map-overlay-layer" id="map-overlays"></div>
      </div>
    `;

    document.getElementById('btn-map-zoom-in').onclick = () => this.zoom(1.2);
    document.getElementById('btn-map-zoom-out').onclick = () => this.zoom(0.8);
    document.getElementById('btn-map-reset').onclick = () => this.reset();
  }

  loadImage(imageUrl, markers = []) {
    const imgElem = document.getElementById('map-img-elem');
    const overlayLayer = document.getElementById('map-overlays');

    this.currentImage = imageUrl;
    this.markers = markers;
    this.zoomLevel = 1;

    imgElem.onload = () => {
      imgElem.style.display = 'block';
      this.renderOverlays();
    };
    imgElem.src = imageUrl;
  }

  zoom(factor) {
    this.zoomLevel = Math.max(0.5, Math.min(3.0, this.zoomLevel * factor));
    const imgElem = document.getElementById('map-img-elem');
    const overlayLayer = document.getElementById('map-overlays');
    imgElem.style.transform = `scale(${this.zoomLevel})`;
    overlayLayer.style.transform = `scale(${this.zoomLevel})`;
  }

  reset() {
    this.zoomLevel = 1;
    const imgElem = document.getElementById('map-img-elem');
    const overlayLayer = document.getElementById('map-overlays');
    imgElem.style.transform = 'scale(1)';
    overlayLayer.style.transform = 'scale(1)';
  }

  renderOverlays() {
    const overlayLayer = document.getElementById('map-overlays');
    const imgElem = document.getElementById('map-img-elem');
    overlayLayer.innerHTML = '';

    const imgRect = imgElem.getBoundingClientRect();
    const containerRect = overlayLayer.parentElement.getBoundingClientRect();

    const offsetX = (containerRect.width - imgRect.width) / 2;
    const offsetY = (containerRect.height - imgRect.height) / 2;

    this.markers.forEach((m, idx) => {
      if (!m.bbox || m.bbox.length < 4) return;
      const [ymin, xmin, ymax, xmax] = m.bbox;

      const markerElem = document.createElement('div');
      markerElem.className = 'map-bbox-marker';
      markerElem.style.left = `${xmin * 100}%`;
      markerElem.style.top = `${ymin * 100}%`;
      markerElem.style.width = `${(xmax - xmin) * 100}%`;
      markerElem.style.height = `${(ymax - ymin) * 100}%`;

      markerElem.innerHTML = `
        <span class="map-bbox-tag">${m.text || m.label}</span>
      `;

      markerElem.onclick = (e) => {
        e.stopPropagation();
        document.querySelectorAll('.map-bbox-marker').forEach(el => el.classList.remove('active'));
        markerElem.classList.add('active');
        if (this.onMarkerClick) this.onMarkerClick(m);
      };

      overlayLayer.appendChild(markerElem);
    });
  }
}
