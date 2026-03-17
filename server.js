const express = require('express');
const Database = require('better-sqlite3');
const bcrypt = require('bcrypt');
const basicAuth = require('express-basic-auth');
const bodyParser = require('body-parser');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

// Initialize SQLite database
const db = new Database('api_doc.db');

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

// Get available controllers (for filter)
app.get('/api/controllers', userAuth, (req, res) => {
  const controllers = db.prepare('SELECT DISTINCT controller FROM api_endpoints ORDER BY controller').all();
  res.json(controllers.map(c => c.controller));
});

// Serve the main HTML file
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Linked API Documentation running at http://localhost:${PORT}`);
});