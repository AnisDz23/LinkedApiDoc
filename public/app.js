// Linked API Documentation - Frontend JavaScript

const API_BASE = '';

// State
let authHeader = null;

// DOM Elements
const loginModal = document.getElementById('loginModal');
const endpointModal = document.getElementById('endpointModal');
const loginForm = document.getElementById('loginForm');
const endpointForm = document.getElementById('endpointForm');
const endpointsTableBody = document.getElementById('endpointsTableBody');
const filterMethod = document.getElementById('filterMethod');
const filterRoute = document.getElementById('filterRoute');
const filterController = document.getElementById('filterController');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  checkAuth();
  loadControllers();
  setupEventListeners();
});

// Check if already authenticated
function checkAuth() {
  const savedAuth = localStorage.getItem('apiAuth');
  if (savedAuth) {
    authHeader = 'Basic ' + savedAuth;
    loadEndpoints();
    loginModal.classList.remove('active');
  } else {
    loginModal.classList.add('active');
  }
}

// Setup Event Listeners
function setupEventListeners() {
  // Login
  loginForm.addEventListener('submit', handleLogin);
  
  // Logout
  document.getElementById('logoutBtn').addEventListener('click', handleLogout);
  
  // Add Endpoint
  document.getElementById('addEndpointBtn').addEventListener('click', () => openModal());
  
  // Close Modal
  document.getElementById('closeModal').addEventListener('click', closeModal);
  document.getElementById('cancelBtn').addEventListener('click', closeModal);
  
  // Endpoint Form
  endpointForm.addEventListener('submit', handleSubmit);
  
  // Filters
  document.getElementById('applyFilters').addEventListener('click', loadEndpoints);
  document.getElementById('clearFilters').addEventListener('click', clearFilters);
  
  // Close modal on outside click
  window.addEventListener('click', (e) => {
    if (e.target === loginModal) {
      // Don't close login modal
    }
    if (e.target === endpointModal) {
      closeModal();
    }
  });
}

// Handle Login
function handleLogin(e) {
  e.preventDefault();
  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;
  
  const credentials = btoa(`${username}:${password}`);
  authHeader = 'Basic ' + credentials;
  localStorage.setItem('apiAuth', credentials);
  
  // Test authentication by loading endpoints
  fetchEndpoints()
    .then(() => {
      loginModal.classList.remove('active');
      loadEndpoints();
      loadControllers();
    })
    .catch(() => {
      authHeader = null;
      localStorage.removeItem('apiAuth');
      alert('Invalid credentials');
    });
}

// Handle Logout
function handleLogout() {
  authHeader = null;
  localStorage.removeItem('apiAuth');
  loginModal.classList.add('active');
  document.getElementById('username').value = '';
  document.getElementById('password').value = '';
  endpointsTableBody.innerHTML = '<tr><td colspan="6" class="loading">Please login...</td></tr>';
}

// Load Controllers for Filter
async function loadControllers() {
  try {
    const response = await fetchWithAuth('/api/controllers');
    const controllers = await response.json();
    
    filterController.innerHTML = '<option value="">All Controllers</option>';
    controllers.forEach(ctrl => {
      const option = document.createElement('option');
      option.value = ctrl;
      option.textContent = ctrl;
      filterController.appendChild(option);
    });
  } catch (error) {
    console.error('Failed to load controllers:', error);
  }
}

// Load Endpoints
function loadEndpoints() {
  if (!authHeader) return;
  
  endpointsTableBody.innerHTML = '<tr><td colspan="6" class="loading">Loading endpoints...</td></tr>';
  
  fetchEndpoints()
    .then(endpoints => renderEndpoints(endpoints))
    .catch(error => {
      if (error.message === 'Unauthorized') {
        handleLogout();
      } else {
        endpointsTableBody.innerHTML = '<tr><td colspan="6" class="loading">Error loading endpoints</td></tr>';
      }
    });
}

// Fetch Endpoints with filters
async function fetchEndpoints() {
  const params = new URLSearchParams();
  
  if (filterMethod.value) params.append('method', filterMethod.value);
  if (filterRoute.value) params.append('route', filterRoute.value);
  if (filterController.value) params.append('controller', filterController.value);
  
  const url = `/api/endpoints${params.toString() ? '?' + params.toString() : ''}`;
  return fetchWithAuth(url).then(res => res.json());
}

// Fetch with Auth
async function fetchWithAuth(url, options = {}) {
  const response = await fetch(API_BASE + url, {
    ...options,
    headers: {
      ...(authHeader && { 'Authorization': authHeader }),
      'Content-Type': 'application/json',
      ...options.headers
    }
  });
  
  if (response.status === 401) {
    throw new Error('Unauthorized');
  }
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Request failed' }));
    throw new Error(error.error || 'Request failed');
  }
  
  return response;
}

// Render Endpoints Table
function renderEndpoints(endpoints) {
  if (endpoints.length === 0) {
    endpointsTableBody.innerHTML = '<tr><td colspan="6" class="loading">No endpoints found</td></tr>';
    return;
  }
  
  endpointsTableBody.innerHTML = endpoints.map(endpoint => `
    <tr>
      <td><span class="method-badge ${endpoint.http_method.toLowerCase()}">${endpoint.http_method}</span></td>
      <td><code class="route-text">${escapeHtml(endpoint.route)}</code></td>
      <td><pre class="parameters-text">${escapeHtml(endpoint.parameters || '')}</pre></td>
      <td>${escapeHtml(endpoint.controller)}</td>
      <td><div class="description-text">${escapeHtml(endpoint.description || '<em>No description</em>')}</div></td>
      <td>
        <div class="action-buttons">
          <button class="btn btn-secondary" onclick="editEndpoint(${endpoint.id})">Edit</button>
          <button class="btn btn-danger" onclick="deleteEndpoint(${endpoint.id})">Delete</button>
        </div>
      </td>
    </tr>
  `).join('');
}

// Open Modal for Add/Edit
function openModal(endpoint = null) {
  const modalTitle = document.getElementById('modalTitle');
  
  if (endpoint) {
    modalTitle.textContent = 'Edit Endpoint';
    document.getElementById('endpointId').value = endpoint.id;
    document.getElementById('httpMethod').value = endpoint.http_method;
    document.getElementById('route').value = endpoint.route;
    document.getElementById('parameters').value = endpoint.parameters || '';
    document.getElementById('description').value = endpoint.description || '';
    document.getElementById('controller').value = endpoint.controller;
  } else {
    modalTitle.textContent = 'Add Endpoint';
    document.getElementById('endpointId').value = '';
    endpointForm.reset();
  }
  
  endpointModal.classList.add('active');
}

// Edit Endpoint
async function editEndpoint(id) {
  try {
    const response = await fetchWithAuth(`/api/endpoints/${id}`);
    const endpoint = await response.json();
    openModal(endpoint);
  } catch (error) {
    alert('Failed to load endpoint: ' + error.message);
  }
}

// Delete Endpoint
async function deleteEndpoint(id) {
  if (!confirm('Are you sure you want to delete this endpoint?')) return;
  
  try {
    const response = await fetchWithAuth(`/api/endpoints/${id}`, { method: 'DELETE' });
    const result = await response.json();
    
    if (result.success) {
      loadEndpoints();
      loadControllers();
    }
  } catch (error) {
    alert('Failed to delete endpoint: ' + error.message);
  }
}

// Handle Form Submit
async function handleSubmit(e) {
  e.preventDefault();
  
  const id = document.getElementById('endpointId').value;
  const data = {
    http_method: document.getElementById('httpMethod').value,
    route: document.getElementById('route').value,
    parameters: document.getElementById('parameters').value,
    description: document.getElementById('description').value,
    controller: document.getElementById('controller').value
  };
  
  try {
    if (id) {
      // Update
      await fetchWithAuth(`/api/endpoints/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data)
      });
    } else {
      // Create
      await fetchWithAuth('/api/endpoints', {
        method: 'POST',
        body: JSON.stringify(data)
      });
    }
    
    closeModal();
    loadEndpoints();
    loadControllers();
  } catch (error) {
    alert('Failed to save endpoint: ' + error.message);
  }
}

// Close Modal
function closeModal() {
  endpointModal.classList.remove('active');
}

// Clear Filters
function clearFilters() {
  filterMethod.value = '';
  filterRoute.value = '';
  filterController.value = '';
  loadEndpoints();
}

// Escape HTML
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Make editEndpoint and deleteEndpoint available globally
window.editEndpoint = editEndpoint;
window.deleteEndpoint = deleteEndpoint;