// API Configuration
const API_BASE = '';  // Same origin, no need for full URL
let authToken = localStorage.getItem('authToken');
let currentUser = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    if (authToken) {
        verifyToken();
    } else {
        showLogin();
    }
    
    setupEventListeners();
});

function setupEventListeners() {
    // Login form
    document.getElementById('loginForm')?.addEventListener('submit', handleLogin);
    
    // Logout button
    document.getElementById('logoutBtn')?.addEventListener('click', handleLogout);
    
    // Navigation links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const view = e.target.dataset.view;
            switchView(view);
        });
    });
}

// Authentication
async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('loginError');
    
    try {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await fetch(`${API_BASE}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Invalid credentials');
        }
        
        const data = await response.json();
        authToken = data.access_token;
        localStorage.setItem('authToken', authToken);
        
        await loadCurrentUser();
        showApp();
        loadDashboard();
    } catch (error) {
        errorDiv.textContent = error.message;
    }
}

async function verifyToken() {
    try {
        await loadCurrentUser();
        showApp();
        loadDashboard();
    } catch (error) {
        localStorage.removeItem('authToken');
        authToken = null;
        showLogin();
    }
}

async function loadCurrentUser() {
    const response = await apiCall('/api/auth/me');
    currentUser = response;
    document.getElementById('currentUser').textContent = `👤 ${currentUser.username} (${currentUser.role})`;
}

function handleLogout() {
    localStorage.removeItem('authToken');
    authToken = null;
    currentUser = null;
    showLogin();
}

function showLogin() {
    document.getElementById('loginScreen').style.display = 'block';
    document.getElementById('appScreen').style.display = 'none';
}

function showApp() {
    document.getElementById('loginScreen').style.display = 'none';
    document.getElementById('appScreen').style.display = 'flex';
}

// API Helper
async function apiCall(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers
    });
    
    if (!response.ok) {
        if (response.status === 401) {
            handleLogout();
        }
        throw new Error(`HTTP ${response.status}`);
    }
    
    return response.json();
}

// View Switching
function switchView(viewName) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    
    document.getElementById(`${viewName}View`).classList.add('active');
    document.querySelector(`[data-view="${viewName}"]`).classList.add('active');
    
    // Load data for the view
    switch(viewName) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'materials':
            loadMaterials();
            break;
        case 'projects':
            loadProjects();
            break;
        case 'stock':
            loadStock();
            break;
        case 'costs':
            loadLaborCosts();
            loadExtraCosts();
            break;
        case 'settings':
            loadSettings();
            break;
    }
}

// Dashboard
async function loadDashboard() {
    try {
        const [materials, projects, lowStock] = await Promise.all([
            apiCall('/api/materials/'),
            apiCall('/api/projects/'),
            apiCall('/api/materials/low-stock/alert')
        ]);
        
        document.getElementById('statMaterials').textContent = materials.length;
        document.getElementById('statProjects').textContent = projects.length;
        document.getElementById('statLowStock').textContent = lowStock.count || 0;
        
        const activeProjects = projects.filter(p => p.status !== 'COMPLETED' && p.status !== 'CANCELLED');
        document.getElementById('statActiveProjects').textContent = activeProjects.length;
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Materials
async function loadMaterials() {
    try {
        const materials = await apiCall('/api/materials/');
        const html = `
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Category</th>
                        <th>Unit</th>
                        <th>Current Stock</th>
                        <th>Min Stock</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${materials.map(m => `
                        <tr>
                            <td>${m.name}</td>
                            <td>${m.category}</td>
                            <td>${m.unit}</td>
                            <td>${m.current_stock}</td>
                            <td>${m.minimum_stock}</td>
                            <td class="action-btns">
                                <button class="btn btn-success" onclick="viewMaterialPrices(${m.id})">Prices</button>
                                <button class="btn btn-danger" onclick="deleteMaterial(${m.id})">Delete</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        document.getElementById('materialsList').innerHTML = html;
    } catch (error) {
        console.error('Error loading materials:', error);
    }
}

function showMaterialForm() {
    const html = `
        <h2>Add Material</h2>
        <form id="materialForm" onsubmit="createMaterial(event)">
            <div class="form-group">
                <label>Name:</label>
                <input type="text" name="name" required>
            </div>
            <div class="form-group">
                <label>Category:</label>
                <input type="text" name="category" required>
            </div>
            <div class="form-group">
                <label>Unit:</label>
                <input type="text" name="unit" required>
            </div>
            <div class="form-group">
                <label>Minimum Stock:</label>
                <input type="number" name="minimum_stock" step="0.01" required>
            </div>
            <button type="submit" class="btn btn-primary">Create</button>
        </form>
    `;
    showModal(html);
}

async function createMaterial(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
        name: formData.get('name'),
        category: formData.get('category'),
        unit: formData.get('unit'),
        minimum_stock: parseFloat(formData.get('minimum_stock'))
    };
    
    try {
        await apiCall('/api/materials/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        closeModal();
        loadMaterials();
    } catch (error) {
        alert('Error creating material: ' + error.message);
    }
}

async function deleteMaterial(id) {
    if (!confirm('Delete this material?')) return;
    
    try {
        await apiCall(`/api/materials/${id}`, { method: 'DELETE' });
        loadMaterials();
    } catch (error) {
        alert('Error deleting material: ' + error.message);
    }
}

async function viewMaterialPrices(id) {
    try {
        const prices = await apiCall(`/api/materials/${id}/prices`);
        const html = `
            <h2>Material Prices</h2>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Price (Net)</th>
                        <th>Supplier</th>
                        <th>Invoice</th>
                    </tr>
                </thead>
                <tbody>
                    ${prices.map(p => `
                        <tr>
                            <td>${new Date(p.date).toLocaleDateString()}</td>
                            <td>${p.price_net}</td>
                            <td>${p.supplier}</td>
                            <td>${p.invoice_number}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        showModal(html);
    } catch (error) {
        alert('Error loading prices: ' + error.message);
    }
}

// Projects
async function loadProjects() {
    try {
        const projects = await apiCall('/api/projects/');
        const html = `
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Client</th>
                        <th>System (kW)</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${projects.map(p => `
                        <tr>
                            <td>${p.name}</td>
                            <td>${p.client_name}</td>
                            <td>${p.system_kw}</td>
                            <td>${p.status}</td>
                            <td class="action-btns">
                                <button class="btn btn-success" onclick="viewBalance(${p.id})">Balance</button>
                                <button class="btn btn-danger" onclick="deleteProject(${p.id})">Delete</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        document.getElementById('projectsList').innerHTML = html;
    } catch (error) {
        console.error('Error loading projects:', error);
    }
}

function showProjectForm() {
    const html = `
        <h2>Add Project</h2>
        <form id="projectForm" onsubmit="createProject(event)">
            <div class="form-group">
                <label>Project Name:</label>
                <input type="text" name="name" required>
            </div>
            <div class="form-group">
                <label>Client Name:</label>
                <input type="text" name="client_name" required>
            </div>
            <div class="form-group">
                <label>Client Address:</label>
                <input type="text" name="client_address" required>
            </div>
            <div class="form-group">
                <label>System Size (kW):</label>
                <input type="number" name="system_kw" step="0.1" required>
            </div>
            <button type="submit" class="btn btn-primary">Create</button>
        </form>
    `;
    showModal(html);
}

async function createProject(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
        name: formData.get('name'),
        client_name: formData.get('client_name'),
        client_address: formData.get('client_address'),
        system_kw: parseFloat(formData.get('system_kw'))
    };
    
    try {
        await apiCall('/api/projects/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        closeModal();
        loadProjects();
    } catch (error) {
        alert('Error creating project: ' + error.message);
    }
}

async function deleteProject(id) {
    if (!confirm('Delete this project?')) return;
    
    try {
        await apiCall(`/api/projects/${id}`, { method: 'DELETE' });
        loadProjects();
    } catch (error) {
        alert('Error deleting project: ' + error.message);
    }
}

async function viewBalance(projectId) {
    try {
        const balance = await apiCall(`/api/balance/${projectId}`);
        const html = `
            <h2>Project Balance: ${balance.project_name}</h2>
            <div style="margin: 20px 0;">
                <p><strong>Client:</strong> ${balance.client_name}</p>
                <p><strong>System:</strong> ${balance.system_kw} kW</p>
            </div>
            <table>
                <tr>
                    <td><strong>Material Costs:</strong></td>
                    <td>${balance.material_costs.toFixed(2)} RON</td>
                </tr>
                <tr>
                    <td><strong>Labor Costs:</strong></td>
                    <td>${balance.labor_costs.toFixed(2)} RON</td>
                </tr>
                <tr>
                    <td><strong>Extra Costs:</strong></td>
                    <td>${balance.extra_costs.toFixed(2)} RON</td>
                </tr>
                <tr>
                    <td><strong>Total Net:</strong></td>
                    <td>${balance.total_net.toFixed(2)} RON</td>
                </tr>
                <tr>
                    <td><strong>VAT (${balance.vat_rate}%):</strong></td>
                    <td>${balance.vat_amount.toFixed(2)} RON</td>
                </tr>
                <tr style="font-weight: bold; font-size: 1.2em;">
                    <td><strong>Total with VAT:</strong></td>
                    <td>${balance.total_with_vat.toFixed(2)} RON</td>
                </tr>
                <tr>
                    <td><strong>Cost per kW:</strong></td>
                    <td>${balance.cost_per_kw.toFixed(2)} RON/kW</td>
                </tr>
            </table>
            <div style="margin-top: 20px;">
                <a href="/api/balance/${projectId}/pdf" target="_blank" class="btn btn-primary">Download PDF</a>
            </div>
        `;
        showModal(html);
    } catch (error) {
        alert('Error loading balance: ' + error.message);
    }
}

// Stock
async function loadStock() {
    try {
        const movements = await apiCall('/api/stock/movements');
        const html = `
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Material ID</th>
                        <th>Type</th>
                        <th>Quantity</th>
                        <th>Project ID</th>
                    </tr>
                </thead>
                <tbody>
                    ${movements.map(m => `
                        <tr>
                            <td>${new Date(m.created_at).toLocaleDateString()}</td>
                            <td>${m.material_id}</td>
                            <td><span style="color: ${m.movement_type === 'IN' ? 'green' : 'red'}">${m.movement_type}</span></td>
                            <td>${m.quantity}</td>
                            <td>${m.project_id || '-'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        document.getElementById('stockList').innerHTML = html;
    } catch (error) {
        console.error('Error loading stock:', error);
    }
}

async function showStockForm() {
    try {
        const materials = await apiCall('/api/materials/');
        const projects = await apiCall('/api/projects/');
        
        const html = `
            <h2>Add Stock Movement</h2>
            <form id="stockForm" onsubmit="createStockMovement(event)">
                <div class="form-group">
                    <label>Material:</label>
                    <select name="material_id" required>
                        ${materials.map(m => `<option value="${m.id}">${m.name}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label>Type:</label>
                    <select name="movement_type" required>
                        <option value="IN">IN</option>
                        <option value="OUT">OUT</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Quantity:</label>
                    <input type="number" name="quantity" step="0.01" required>
                </div>
                <div class="form-group">
                    <label>Price (Net):</label>
                    <input type="number" name="price_net" step="0.01">
                </div>
                <div class="form-group">
                    <label>Project (optional):</label>
                    <select name="project_id">
                        <option value="">None</option>
                        ${projects.map(p => `<option value="${p.id}">${p.name}</option>`).join('')}
                    </select>
                </div>
                <button type="submit" class="btn btn-primary">Create</button>
            </form>
        `;
        showModal(html);
    } catch (error) {
        alert('Error loading form data: ' + error.message);
    }
}

async function createStockMovement(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
        material_id: parseInt(formData.get('material_id')),
        movement_type: formData.get('movement_type'),
        quantity: parseFloat(formData.get('quantity')),
        price_net: formData.get('price_net') ? parseFloat(formData.get('price_net')) : null,
        project_id: formData.get('project_id') ? parseInt(formData.get('project_id')) : null
    };
    
    try {
        await apiCall('/api/stock/movement', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        closeModal();
        loadStock();
    } catch (error) {
        alert('Error creating stock movement: ' + error.message);
    }
}

// Costs
function switchCostTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(`${tab}Costs`).classList.add('active');
}

async function loadLaborCosts() {
    try {
        const costs = await apiCall('/api/costs/labor');
        const html = `
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Project ID</th>
                        <th>Worker</th>
                        <th>Hours</th>
                        <th>Rate</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
                    ${costs.map(c => `
                        <tr>
                            <td>${new Date(c.date).toLocaleDateString()}</td>
                            <td>${c.project_id}</td>
                            <td>${c.worker_name}</td>
                            <td>${c.hours}</td>
                            <td>${c.hourly_rate}</td>
                            <td>${(c.hours * c.hourly_rate).toFixed(2)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        document.getElementById('laborList').innerHTML = html;
    } catch (error) {
        console.error('Error loading labor costs:', error);
    }
}

async function loadExtraCosts() {
    try {
        const costs = await apiCall('/api/costs/extra');
        const html = `
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Project ID</th>
                        <th>Description</th>
                        <th>Category</th>
                        <th>Amount</th>
                    </tr>
                </thead>
                <tbody>
                    ${costs.map(c => `
                        <tr>
                            <td>${new Date(c.date).toLocaleDateString()}</td>
                            <td>${c.project_id}</td>
                            <td>${c.description}</td>
                            <td>${c.category}</td>
                            <td>${c.amount.toFixed(2)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        document.getElementById('extraList').innerHTML = html;
    } catch (error) {
        console.error('Error loading extra costs:', error);
    }
}

async function showLaborForm() {
    try {
        const projects = await apiCall('/api/projects/');
        const html = `
            <h2>Add Labor Cost</h2>
            <form id="laborForm" onsubmit="createLaborCost(event)">
                <div class="form-group">
                    <label>Project:</label>
                    <select name="project_id" required>
                        ${projects.map(p => `<option value="${p.id}">${p.name}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label>Worker Name:</label>
                    <input type="text" name="worker_name" required>
                </div>
                <div class="form-group">
                    <label>Description:</label>
                    <input type="text" name="description" required>
                </div>
                <div class="form-group">
                    <label>Hours:</label>
                    <input type="number" name="hours" step="0.1" required>
                </div>
                <div class="form-group">
                    <label>Hourly Rate:</label>
                    <input type="number" name="hourly_rate" step="0.01" required>
                </div>
                <button type="submit" class="btn btn-primary">Create</button>
            </form>
        `;
        showModal(html);
    } catch (error) {
        alert('Error loading form data: ' + error.message);
    }
}

async function createLaborCost(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
        project_id: parseInt(formData.get('project_id')),
        worker_name: formData.get('worker_name'),
        description: formData.get('description'),
        hours: parseFloat(formData.get('hours')),
        hourly_rate: parseFloat(formData.get('hourly_rate'))
    };
    
    try {
        await apiCall('/api/costs/labor', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        closeModal();
        loadLaborCosts();
    } catch (error) {
        alert('Error creating labor cost: ' + error.message);
    }
}

async function showExtraForm() {
    try {
        const projects = await apiCall('/api/projects/');
        const html = `
            <h2>Add Extra Cost</h2>
            <form id="extraForm" onsubmit="createExtraCost(event)">
                <div class="form-group">
                    <label>Project:</label>
                    <select name="project_id" required>
                        ${projects.map(p => `<option value="${p.id}">${p.name}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label>Description:</label>
                    <input type="text" name="description" required>
                </div>
                <div class="form-group">
                    <label>Category:</label>
                    <input type="text" name="category" required>
                </div>
                <div class="form-group">
                    <label>Amount:</label>
                    <input type="number" name="amount" step="0.01" required>
                </div>
                <button type="submit" class="btn btn-primary">Create</button>
            </form>
        `;
        showModal(html);
    } catch (error) {
        alert('Error loading form data: ' + error.message);
    }
}

async function createExtraCost(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
        project_id: parseInt(formData.get('project_id')),
        description: formData.get('description'),
        category: formData.get('category'),
        amount: parseFloat(formData.get('amount'))
    };
    
    try {
        await apiCall('/api/costs/extra', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        closeModal();
        loadExtraCosts();
    } catch (error) {
        alert('Error creating extra cost: ' + error.message);
    }
}

// Settings
async function loadSettings() {
    try {
        const settings = await apiCall('/api/settings/');
        const html = `
            <table>
                <thead>
                    <tr>
                        <th>Key</th>
                        <th>Value</th>
                        <th>Description</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${settings.map(s => `
                        <tr>
                            <td>${s.key}</td>
                            <td>${s.value}</td>
                            <td>${s.description || '-'}</td>
                            <td class="action-btns">
                                <button class="btn btn-danger" onclick="deleteSetting('${s.key}')">Delete</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        document.getElementById('settingsList').innerHTML = html;
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

function showSettingForm() {
    const html = `
        <h2>Add/Update Setting</h2>
        <form id="settingForm" onsubmit="createSetting(event)">
            <div class="form-group">
                <label>Key:</label>
                <input type="text" name="key" required>
            </div>
            <div class="form-group">
                <label>Value:</label>
                <input type="text" name="value" required>
            </div>
            <div class="form-group">
                <label>Description:</label>
                <input type="text" name="description">
            </div>
            <button type="submit" class="btn btn-primary">Save</button>
        </form>
    `;
    showModal(html);
}

async function createSetting(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
        key: formData.get('key'),
        value: formData.get('value'),
        description: formData.get('description') || null
    };
    
    try {
        await apiCall('/api/settings/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        closeModal();
        loadSettings();
    } catch (error) {
        alert('Error saving setting: ' + error.message);
    }
}

async function deleteSetting(key) {
    if (!confirm('Delete this setting?')) return;
    
    try {
        await apiCall(`/api/settings/${key}`, { method: 'DELETE' });
        loadSettings();
    } catch (error) {
        alert('Error deleting setting: ' + error.message);
    }
}

// Modal
function showModal(html) {
    document.getElementById('modalBody').innerHTML = html;
    document.getElementById('modal').classList.add('active');
}

function closeModal() {
    document.getElementById('modal').classList.remove('active');
}
