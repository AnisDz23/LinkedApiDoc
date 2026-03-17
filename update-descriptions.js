const Database = require('better-sqlite3');
const path = require('path');

// Connect to SQLite database
const dbPath = path.join(__dirname, 'data', 'linkedapi.db');
const db = new Database(dbPath);

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

// Extract entity name from route
function extractEntity(route, controller) {
  // Remove /api/ prefix and controller prefix
  const routePart = route.replace('/api/', '').replace(`${controller}/`, '');
  return routePart;
}

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
      // Replace {entité} with appropriate entity name
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

// Main update function
async function updateDescriptions() {
  console.log('Starting description update...');
  
  // Get all endpoints with empty or null descriptions
  const endpoints = db.prepare("SELECT * FROM api_endpoints WHERE description IS NULL OR description = ''").all();
  
  console.log(`Found ${endpoints.length} endpoints to update.`);
  
  let updatedCount = 0;
  for (const endpoint of endpoints) {
    const description = generateDescription(endpoint);
    db.prepare("UPDATE api_endpoints SET description = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?").run(description, endpoint.id);
    updatedCount++;
    console.log(`Updated ID ${endpoint.id}: ${endpoint.route} → "${description}"`);
  }
  
  console.log(`\nCompleted: ${updatedCount} descriptions updated.`);
  
  // Verify updates
  const updated = db.prepare("SELECT id, route, description FROM api_endpoints WHERE description != '' AND description IS NOT NULL").all();
  console.log(`\nTotal endpoints with descriptions: ${updated.length}`);
  
  db.close();
}

updateDescriptions();
