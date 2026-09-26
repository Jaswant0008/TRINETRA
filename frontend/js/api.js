/**
 * TRINETRA Official REST API Client
 */
const API = {
  baseUrl: '/api',

  async getStatus() {
    const res = await fetch(`${this.baseUrl}/status`);
    if (!res.ok) throw new Error('Failed to fetch system status');
    return res.json();
  },

  async getKnowledgeGraph() {
    const res = await fetch(`${this.baseUrl}/graph`);
    if (!res.ok) throw new Error('Failed to fetch knowledge graph');
    return res.json();
  },

  async getEntities() {
    const res = await fetch(`${this.baseUrl}/entities`);
    if (!res.ok) throw new Error('Failed to fetch entities');
    return res.json();
  },

  async getEntityById(entityId) {
    const res = await fetch(`${this.baseUrl}/entities/${entityId}`);
    if (!res.ok) throw new Error(`Failed to fetch entity details for ${entityId}`);
    return res.json();
  },

  async getTriples() {
    const res = await fetch(`${this.baseUrl}/triples`);
    if (!res.ok) throw new Error('Failed to fetch RDF triples');
    return res.json();
  },

  async getConflicts() {
    const res = await fetch(`${this.baseUrl}/conflicts`);
    if (!res.ok) throw new Error('Failed to fetch conflicts');
    return res.json();
  },

  async getResolutions() {
    const res = await fetch(`${this.baseUrl}/resolutions`);
    if (!res.ok) throw new Error('Failed to fetch entity resolutions');
    return res.json();
  },

  async getDocuments() {
    const res = await fetch(`${this.baseUrl}/documents`);
    if (!res.ok) throw new Error('Failed to fetch sources');
    return res.json();
  },

  async getPipelineStatus() {
    const res = await fetch(`${this.baseUrl}/pipeline/status`);
    if (!res.ok) throw new Error('Failed to fetch pipeline status');
    return res.json();
  },

  async getAgentsStatus() {
    const res = await fetch(`${this.baseUrl}/agents/status`);
    if (!res.ok) throw new Error('Failed to fetch active agent modules');
    return res.json();
  },

  async queryGraphRAG(queryText) {
    const res = await fetch(`${this.baseUrl}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: queryText })
    });
    if (!res.ok) throw new Error('Failed to execute GraphRAG query');
    return res.json();
  },

  async deleteDocument(sourceId) {
    const res = await fetch(`${this.baseUrl}/documents/${sourceId}`, {
      method: 'DELETE'
    });
    if (!res.ok) throw new Error('Failed to delete source');
    return res.json();
  },

  async clearAllDocuments() {
    const res = await fetch(`${this.baseUrl}/documents/clear`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Failed to clear documents');
    return res.json();
  },

  async uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${this.baseUrl}/documents/upload`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error('Failed to upload document');
    return res.json();
  },

  async reanalyzeSource(sourceId) {
    const res = await fetch(`${this.baseUrl}/sources/${sourceId}/reanalyze`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to reanalyze source document');
    return res.json();
  },

  async reingestAllUploads() {
    const res = await fetch(`${this.baseUrl}/documents/reingest-all`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to reingest uploaded documents');
    return res.json();
  },

  async loadDemoScenario() {
    const res = await fetch(`${this.baseUrl}/demo/load`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to load demo scenario');
    return res.json();
  },

  getExportJsonLdUrl() {
    return `${this.baseUrl}/export/jsonld`;
  },

  getExportTurtleUrl() {
    return `${this.baseUrl}/export/turtle`;
  }
};
