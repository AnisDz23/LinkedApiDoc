const express = require('express');
const Database = require('better-sqlite3');
const bcrypt = require('bcrypt');
const basicAuth = require('express-basic-auth');
const bodyParser = require('body-parser');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

// Initialize SQLite database - persist in mounted volume
const dbPath = path.join(__dirname, 'data', 'linkedapi.db');
const db = new Database(dbPath);

// Create tables
db.exec(`
  CREATE TABLE IF NOT EXISTS api_endpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    http_method TEXT NOT NULL,
    route TEXT NOT NULL,
    parameters TEXT,
    description TEXT DEFAULT '',
    controller TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );
`);

// Initialize default admin user if not exists
const adminExists = db.prepare('SELECT id FROM users WHERE username = ?').get('admin');
if (!adminExists) {
  const hashedPassword = bcrypt.hashSync('admin', 10);
  db.prepare('INSERT INTO users (username, password) VALUES (?, ?)').run('admin', hashedPassword);
  console.log('Default admin user created (admin/admin)');
}

// Insert sample data if table is empty
const count = db.prepare('SELECT COUNT(*) as count FROM api_endpoints').get();
if (count.count === 0) {
  const insert = db.prepare(`
    INSERT INTO api_endpoints (http_method, route, parameters, description, controller)
    VALUES (?, ?, ?, ?, ?)
  `);
  insert.run('GET', '/api/TRS_TIERS/SelectOrderTiers', '{"sec": "string"}', '', 'TRS_TIERS');
  insert.run('POST', '/api/TRS_TIERS/ChangeActivity', '{"ids": "List<string>", "act": "string"}', '', 'TRS_TIERS');
  console.log('Sample data inserted');
}

// Middleware
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, 'public')));

// Basic auth middleware
const userAuth = basicAuth({
  authorizer: (user, pass) => {
    const row = db.prepare('SELECT password FROM users WHERE username = ?').get(user);
    if (!row) return false;
    return bcrypt.compareSync(pass, row.password);
  },
  unauthorizedResponse: () => 'Authentication required'
});

// API Routes

// Get all endpoints
app.get('/api/endpoints', userAuth, (req, res) => {
  const { method, route, controller } = req.query;
  
  let sql = 'SELECT * FROM api_endpoints WHERE 1=1';
  const params = [];
  
  if (method) {
    sql += ' AND http_method = ?';
    params.push(method);
  }
  if (route) {
    sql += ' AND route LIKE ?';
    params.push(`%${route}%`);
  }
  if (controller) {
    sql += ' AND controller LIKE ?';
    params.push(`%${controller}%`);
  }
  
  sql += ' ORDER BY id';
  
  const endpoints = db.prepare(sql).all(...params);
  res.json(endpoints);
});

// Get single endpoint
app.get('/api/endpoints/:id', userAuth, (req, res) => {
  const endpoint = db.prepare('SELECT * FROM api_endpoints WHERE id = ?').get(req.params.id);
  if (!endpoint) {
    return res.status(404).json({ error: 'Endpoint not found' });
  }
  res.json(endpoint);
});

// Add new endpoint
app.post('/api/endpoints', userAuth, (req, res) => {
  const { http_method, route, parameters, description, controller } = req.body;
  
  if (!http_method || !route || !controller) {
    return res.status(400).json({ error: 'http_method, route, and controller are required' });
  }
  
  const stmt = db.prepare(`
    INSERT INTO api_endpoints (http_method, route, parameters, description, controller)
    VALUES (?, ?, ?, ?, ?)
  `);
  
  const result = stmt.run(http_method, route, parameters || '', description || '', controller);
  
  const newEndpoint = db.prepare('SELECT * FROM api_endpoints WHERE id = ?').get(result.lastInsertRowid);
  res.status(201).json(newEndpoint);
});

// Update endpoint
app.put('/api/endpoints/:id', userAuth, (req, res) => {
  const { http_method, route, parameters, description, controller } = req.body;
  const { id } = req.params;
  
  const existing = db.prepare('SELECT * FROM api_endpoints WHERE id = ?').get(id);
  if (!existing) {
    return res.status(404).json({ error: 'Endpoint not found' });
  }
  
  const stmt = db.prepare(`
    UPDATE api_endpoints 
    SET http_method = ?, route = ?, parameters = ?, description = ?, controller = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
  `);
  
  stmt.run(
    http_method || existing.http_method,
    route || existing.route,
    parameters !== undefined ? parameters : existing.parameters,
    description !== undefined ? description : existing.description,
    controller || existing.controller,
    id
  );
  
  const updated = db.prepare('SELECT * FROM api_endpoints WHERE id = ?').get(id);
  res.json(updated);
});

// Delete endpoint
app.delete('/api/endpoints/:id', userAuth, (req, res) => {
  const { id } = req.params;
  
  const existing = db.prepare('SELECT * FROM api_endpoints WHERE id = ?').get(id);
  if (!existing) {
    return res.status(404).json({ error: 'Endpoint not found' });
  }
  
  db.prepare('DELETE FROM api_endpoints WHERE id = ?').run(id);
  res.json({ success: true, message: 'Endpoint deleted' });
});

// Controller descriptions mapping
const controllerDescriptions = {
  'TRS_TIERS': 'Gestion des tiers (clients, fournisseurs, employés).',
  'VTE_DOCUMENT': 'Gestion des documents de vente (factures, commandes, avoirs).',
  'STK_STOCK': 'Gestion des stocks (mouvements, inventaires, régularisations).',
  'ACH_DOCUMENT': 'Gestion des documents d\'achat (commandes, réceptions, retours).',
  'BSE_PRODUITS': 'Gestion des produits (références, familles, variantes).',
  'CRM_TOURNEE': 'Gestion des tournées commerciales (planning, visites, actions).',
  'STK_DOCUMENT': 'Gestion des documents de stock (entrées, sorties, transferts).',
  'VTE_COMPTOIR': 'Gestion des ventes au comptoir (tickets, paiements, retours).'
};

// Method prefix descriptions mapping
const methodPrefixes = {
  'Get': 'Récupère les détails de {entité}.',
  'Select': 'Récupère une liste filtrée de {entité}.',
  'Change': 'Modifie le statut de {entité}.',
  'Save': 'Enregistre ou met à jour {entité}.',
  'Import': 'Importe des données de {entité} depuis un fichier.',
  'Export': 'Exporte des données de {entité} vers un fichier.',
  'Delete': 'Supprime {entité}.',
  'Recalcul': 'Recalcule les données de {entité}.',
  'Fusion': 'Fusionne plusieurs {entité} en un seul.'
};

// Generate description based on rules
function generateDescription(endpoint) {
  const { controller, route, parameters } = endpoint;
  
  // Get base controller description
  const baseDesc = controllerDescriptions[controller] || `Gestion des ${controller.toLowerCase().replace('_', ' ')}.`;
  
  // Extract method name from route
  const routePart = route.replace('/api/', '').replace(`${controller}/`, '');
  const methodName = routePart;
  
  // Find matching prefix
  let methodDesc = '';
  for (const [prefix, desc] of Object.entries(methodPrefixes)) {
    if (methodName.startsWith(prefix)) {
      const entityName = methodName.replace(prefix, '').toLowerCase();
      methodDesc = desc.replace('{entité}', entityName);
      break;
    }
  }
  
  // Build parameters description
  let paramsDesc = '';
  if (parameters && parameters !== '{}') {
    try {
      const paramsObj = JSON.parse(parameters);
      const paramKeys = Object.keys(paramsObj);
      
      if (paramKeys.length > 0) {
        const paramDescriptions = [];
        for (const key of paramKeys) {
          if (key === 'ids') {
            paramDescriptions.push(`ids (liste des identifiants)`);
          } else if (key === 'sec') {
            paramDescriptions.push(`sec (secteur)`);
          } else if (key === 'act') {
            paramDescriptions.push(`act (statut : ACTIVE/INACTIVE)`);
          } else {
            paramDescriptions.push(`${key}`);
          }
        }
        paramsDesc = ` Paramètres : ${paramDescriptions.join(', ')}.`;
      }
    } catch (e) {
      // Invalid JSON, skip params
    }
  }
  
  // Combine descriptions
  let fullDescription = baseDesc;
  if (methodDesc) {
    fullDescription += ' ' + methodDesc;
  }
  if (paramsDesc) {
    fullDescription += paramsDesc;
  }
  
  return fullDescription;
}

// Get available controllers (for filter)
app.get('/api/controllers', userAuth, (req, res) => {
  const controllers = db.prepare('SELECT DISTINCT controller FROM api_endpoints ORDER BY controller').all();
  res.json(controllers.map(c => c.controller));
});

// Update descriptions for endpoints with empty descriptions
app.post('/api/update-descriptions', userAuth, (req, res) => {
  const endpoints = db.prepare("SELECT * FROM api_endpoints WHERE description IS NULL OR description = ''").all();
  
  let updatedCount = 0;
  for (const endpoint of endpoints) {
    const description = generateDescription(endpoint);
    db.prepare("UPDATE api_endpoints SET description = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?").run(description, endpoint.id);
    updatedCount++;
  }
  
  res.json({ success: true, updated: updatedCount, message: `${updatedCount} descriptions updated` });
});

// Serve the main HTML file
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Linked API Documentation running at http://localhost:${PORT}`);
});