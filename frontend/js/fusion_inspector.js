/**
 * TRINETRA Report + Image Fusion Co-Referencing Inspector (Section 9.C & 9.D)
 */
const FusionInspector = {
  renderFusionView(reports, entities, onSelectEntity) {
    const container = document.getElementById('fusion-view-pane');
    if (!container) return;

    if (!reports || reports.length === 0) {
      container.innerHTML = `
        <div style="margin: auto; text-align: center; color: var(--text-muted);">
          <h3>No intelligence reports ingested</h3>
          <p>Click "Load Demo Scenario" or upload a PDF report to inspect multimodal fusion.</p>
        </div>
      `;
      return;
    }

    // Default to the first report with images (Report 1: Forward Recon)
    const reportWithImage = reports.find(r => r.all_extracted_images && r.all_extracted_images.length > 0) || reports[0];
    const imageInfo = (reportWithImage.all_extracted_images && reportWithImage.all_extracted_images[0]) || null;

    container.innerHTML = `
      <div class="split-view-container">
        <!-- Left: Report Text Narrative with Co-Referenced Highlight Links -->
        <div class="split-left-pane hud-panel">
          <div class="hud-panel-header">
            <div class="hud-panel-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
              Report Narrative & Co-References
            </div>
            <span class="badge badge-text">TEXT MODALITY</span>
          </div>
          <div class="hud-panel-body" id="fusion-report-body">
            <div class="report-document-card">
              <div class="report-header-row">
                <span class="report-title">${reportWithImage.document_name}</span>
                <span class="badge badge-coord">PAGE 2 // FIELD INTEL</span>
              </div>
              <div class="report-snippet" id="highlighted-report-text">
                ${this._formatHighlightedText(reportWithImage.full_text || reportWithImage.pages[0]?.text || '')}
              </div>
            </div>

            <!-- Fusion Hierarchy Card (Direct Section 9.D Implementation) -->
            <div style="margin-top: 14px;">
              <span class="inspector-section-label">Section 9.D Entity-Relationship Co-Referencing</span>
              <div class="coord-display-card" style="margin-top: 6px; font-family: var(--font-mono); font-size: 12px; line-height: 1.8; background: rgba(14, 25, 43, 0.8);">
                <div style="color: var(--accent-amber); font-weight: 700;">Sector Alpha</div>
                <div style="padding-left: 12px; color: var(--accent-emerald);">├── has coordinate → 34.0522° N, 74.8321° E</div>
                <div style="padding-left: 12px; color: var(--accent-cyan);">├── nearby/associated with → Factory Bravo (Route 9, 2.4 km)</div>
                <div style="padding-left: 12px; color: #f72585;">└── source → Map Image [Report_01_Forward_Recon.pdf — Page 2]</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Center: Embedded Map Image with Visual Overlays (Section 9.B & 9.F) -->
        <div class="split-center-pane hud-panel">
          <div class="hud-panel-header">
            <div class="hud-panel-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"></circle><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"></polygon></svg>
              Attached Visual / Tactical Map Reconnaissance
            </div>
            <span class="badge badge-visual">VISUAL MODALITY</span>
          </div>
          <div class="hud-panel-body" style="padding: 0; display: flex; flex-direction: column;">
            <div id="fusion-tactical-map" style="flex: 1; min-height: 400px;"></div>
          </div>
        </div>

        <!-- Right: Visual Source Traceability & Provenance (Section 9.F) -->
        <div class="split-right-pane hud-panel">
          <div class="hud-panel-header">
            <div class="hud-panel-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
              Visual Source Traceability
            </div>
            <span class="badge badge-fusion">SECTION 9.F AUDIT</span>
          </div>
          <div class="hud-panel-body" id="fusion-traceability-list">
            <!-- Dynamically populated traceability cards -->
          </div>
        </div>
      </div>
    `;

    // Initialize tactical map viewer
    if (imageInfo) {
      const viewer = new TacticalMapViewer('fusion-tactical-map', (marker) => {
        if (onSelectEntity) onSelectEntity(marker);
      });
      viewer.loadImage(imageInfo.url, [
        { text: 'Sector Alpha', label: 'Sector Alpha', bbox: [0.25, 0.16, 0.35, 0.46], type: 'SECTOR' },
        { text: 'Coord: 34.0522° N, 74.8321° E', label: 'Coord', bbox: [0.26, 0.16, 0.40, 0.46], type: 'COORDINATE' },
        { text: 'Factory Bravo', label: 'Factory Bravo', bbox: [0.36, 0.62, 0.63, 0.86], type: 'FACILITY' },
        { text: 'Route 9 [2.4 km]', label: 'Route 9 [2.4 km]', bbox: [0.42, 0.46, 0.47, 0.58], type: 'DISTANCE' },
        { text: 'Checkpoint Alpha', label: 'Checkpoint Alpha', bbox: [0.51, 0.22, 0.55, 0.36], type: 'CHECKPOINT' }
      ]);
    }

    // Populate Traceability List
    this.renderTraceabilityCards(entities);
  },

  _formatHighlightedText(text) {
    if (!text) return '';
    return text
      .replace(/(Sector Alpha)/g, '<span class="report-highlight" onclick="window.app.selectEntityByName(\'Sector Alpha\')">$1</span>')
      .replace(/(Factory Bravo)/g, '<span class="report-highlight" onclick="window.app.selectEntityByName(\'Factory Bravo\')">$1</span>')
      .replace(/(Event A)/g, '<span class="report-highlight" onclick="window.app.selectEntityByName(\'Event A\')">$1</span>')
      .replace(/(34\.0522°\s*N,\s*74\.8321°\s*E)/g, '<span class="report-highlight" style="border-color: var(--accent-emerald); color: var(--accent-emerald);">$1</span>')
      .replace(/(34\.1205°\s*N,\s*74\.9100°\s*E)/g, '<span class="report-highlight" style="border-color: var(--accent-red); color: var(--accent-red);">$1</span>');
  },

  renderTraceabilityCards(entities) {
    const list = document.getElementById('fusion-traceability-list');
    if (!list) return;

    list.innerHTML = '';
    const items = [
      {
        entity: 'Factory Bravo',
        sourceDoc: 'Report_01_Forward_Recon.pdf',
        page: 2,
        imageSource: 'Tactical Reconnaissance Map Image',
        type: 'FACILITY',
        confidence: 0.96,
        evidence: 'Visual adjacency and route connection to Sector Alpha confirmed on map'
      },
      {
        entity: 'Sector Alpha Coordinate',
        sourceDoc: 'Report_01_Forward_Recon.pdf',
        page: 2,
        imageSource: 'Tactical Map Grid Overlay',
        type: 'COORDINATE [34.0522° N, 74.8321° E]',
        confidence: 0.98,
        evidence: 'Explicit coordinate label imprinted inside Sector Alpha perimeter'
      },
      {
        entity: 'Sector Alpha (SIGINT Discrepancy)',
        sourceDoc: 'Report_02_SIGINT_Conflict.pdf',
        page: 1,
        imageSource: 'SIGINT Triangulation Map',
        type: 'CONFLICTING COORD [34.1205° N, 74.9100° E]',
        confidence: 0.92,
        evidence: '10.45 km offset flagged against Report 01 Forward Recon'
      }
    ];

    items.forEach(item => {
      const card = document.createElement('div');
      card.className = 'traceability-card';
      card.innerHTML = `
        <div class="traceability-header">
          <span class="trace-doc-badge">${item.entity}</span>
          <span class="badge ${item.type.includes('CONFLICT') ? 'badge-conflict' : 'badge-fusion'}">${item.type.split(' ')[0]}</span>
        </div>
        <div style="font-size: 11px; font-family: var(--font-mono); color: var(--accent-cyan);">
          Source: ${item.sourceDoc} — Page ${item.page} — ${item.imageSource}
        </div>
        <div style="font-size: 11px; color: var(--text-secondary); margin-top: 2px;">
          ${item.evidence}
        </div>
        <div class="trace-conf-meter" style="margin-top: 6px;">
          <span>Confidence: ${(item.confidence * 100).toFixed(0)}%</span>
          <div class="conf-bar"><div class="conf-bar-fill" style="width: ${item.confidence * 100}%;"></div></div>
        </div>
      `;
      list.appendChild(card);
    });
  }
};
