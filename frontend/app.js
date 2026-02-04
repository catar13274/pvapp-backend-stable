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
        case 'invoices':
            loadInvoices();
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

// Invoices
async function loadInvoices() {
    try {
        const invoices = await apiCall('/api/invoices/pending');
        const list = document.getElementById('invoicesList');
        
        if (invoices.length === 0) {
            list.innerHTML = '<p>No pending invoices found. Click "Upload Invoice" to add one.</p>';
            return;
        }
        
        list.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Supplier</th>
                        <th>Invoice Number</th>
                        <th>Date</th>
                        <th>Amount</th>
                        <th>Status</th>
                        <th>Items</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${invoices.map(inv => {
                        const statusClass = inv.status === 'CONFIRMED' ? 'success' : 
                                          inv.status === 'VALIDATED' ? 'info' : 
                                          inv.status === 'PARSED' ? 'warning' : 'warning';
                        return `
                        <tr>
                            <td>${inv.id}</td>
                            <td>${inv.supplier || '-'}</td>
                            <td>${inv.invoice_number || '-'}</td>
                            <td>${inv.invoice_date || '-'}</td>
                            <td>${inv.total_amount ? inv.total_amount.toFixed(2) : '-'}</td>
                            <td><span class="badge badge-${statusClass}">${inv.status}</span></td>
                            <td>${inv.items ? inv.items.length : 0}</td>
                            <td>
                                <button class="btn btn-sm btn-primary" onclick="viewInvoice(${inv.id})">View</button>
                                ${inv.status === 'PENDING' || inv.status === 'VALIDATED' ? `<button class="btn btn-sm btn-success" onclick="confirmInvoice(${inv.id})">Confirm</button>` : ''}
                            </td>
                        </tr>
                    `}).join('')}
                </tbody>
            </table>
        `;
    } catch (error) {
        document.getElementById('invoicesList').innerHTML = `<p class="error">Error loading invoices: ${error.message}</p>`;
    }
}

async function viewInvoice(invoiceId) {
    try {
        const invoice = await apiCall(`/api/invoices/${invoiceId}`);
        const materials = await apiCall('/api/materials/');
        
        const html = `
            <h2>Invoice Details</h2>
            <div class="invoice-details">
                <p><strong>Supplier:</strong> ${invoice.supplier || '-'}</p>
                <p><strong>Invoice Number:</strong> ${invoice.invoice_number || '-'}</p>
                <p><strong>Date:</strong> ${invoice.invoice_date || '-'}</p>
                <p><strong>Total Amount:</strong> ${invoice.total_amount ? invoice.total_amount.toFixed(2) : '-'}</p>
                <p><strong>Status:</strong> <span class="badge badge-${invoice.status === 'CONFIRMED' ? 'success' : 'warning'}">${invoice.status}</span></p>
            </div>
            
            <h3>Items</h3>
            <table>
                <thead>
                    <tr>
                        <th>Description</th>
                        <th>Quantity</th>
                        <th>Unit Price</th>
                        <th>Total</th>
                        <th>Material</th>
                        ${invoice.status === 'PENDING' ? '<th>Action</th>' : ''}
                    </tr>
                </thead>
                <tbody>
                    ${invoice.items.map(item => `
                        <tr>
                            <td>${item.description || '-'}</td>
                            <td>${item.quantity}</td>
                            <td>${item.unit_price ? item.unit_price.toFixed(2) : '-'}</td>
                            <td>${item.total_price ? item.total_price.toFixed(2) : '-'}</td>
                            <td>
                                ${item.material_id ? 
                                    materials.find(m => m.id === item.material_id)?.name || `Material #${item.material_id}` 
                                    : 'Not mapped'}
                            </td>
                            ${invoice.status === 'PENDING' ? `
                                <td>
                                    ${!item.material_id ? `
                                        <select onchange="mapInvoiceItem(${invoiceId}, ${item.id}, this.value)">
                                            <option value="">Select Material</option>
                                            ${materials.map(m => `<option value="${m.id}">${m.name}</option>`).join('')}
                                        </select>
                                    ` : 'Mapped ✓'}
                                </td>
                            ` : ''}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            
            ${invoice.status === 'PENDING' ? `
                <div style="margin-top: 20px;">
                    <button class="btn btn-success" onclick="confirmInvoice(${invoiceId})">Confirm Invoice</button>
                    <button class="btn btn-secondary" onclick="closeModal()">Close</button>
                </div>
            ` : `
                <div style="margin-top: 20px;">
                    <button class="btn btn-secondary" onclick="closeModal()">Close</button>
                </div>
            `}
        `;
        
        showModal(html);
    } catch (error) {
        alert('Error loading invoice: ' + error.message);
    }
}

async function mapInvoiceItem(invoiceId, itemId, materialId) {
    if (!materialId) return;
    
    try {
        await apiCall(`/api/invoices/${invoiceId}/items/${itemId}?material_id=${materialId}`, {
            method: 'PUT'
        });
        alert('Item mapped successfully!');
        viewInvoice(invoiceId); // Reload invoice view
    } catch (error) {
        alert('Error mapping item: ' + error.message);
    }
}

async function confirmInvoice(invoiceId) {
    if (!confirm('Are you sure you want to confirm this invoice? This will create stock movements for all mapped items.')) {
        return;
    }
    
    try {
        const result = await apiCall(`/api/invoices/${invoiceId}/confirm`, {
            method: 'POST'
        });
        alert(`Invoice confirmed! ${result.items_processed} items processed.`);
        closeModal();
        loadInvoices();
    } catch (error) {
        alert('Error confirming invoice: ' + error.message);
    }
}

function refreshInvoices() {
    loadInvoices();
}

// Invoice File Upload Functions
function showUploadInvoiceForm() {
    const html = `
        <h2>Upload Invoice File</h2>
        <p>Upload invoice in PDF, DOC, TXT, or XML format. The system will automatically extract materials.</p>
        
        <form id="uploadInvoiceForm" onsubmit="uploadInvoiceFile(event)">
            <div class="form-group">
                <label>Select File:</label>
                <input type="file" id="invoiceFile" accept=".pdf,.doc,.docx,.txt,.xml" required>
                <small>Supported formats: PDF, DOC, DOCX, TXT, XML (Max 10MB)</small>
            </div>
            
            <div id="uploadProgress" style="display: none;">
                <div class="progress-bar">
                    <div id="progressBar" style="width: 0%; height: 20px; background-color: #4CAF50;"></div>
                </div>
                <p id="uploadStatus">Uploading...</p>
            </div>
            
            <div class="form-actions">
                <button type="submit" class="btn btn-primary">Upload & Parse</button>
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            </div>
        </form>
    `;
    showModal(html);
}

async function uploadInvoiceFile(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById('invoiceFile');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a file');
        return;
    }
    
    // Show progress
    document.getElementById('uploadProgress').style.display = 'block';
    document.getElementById('uploadStatus').textContent = 'Uploading...';
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/invoices/upload', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }
        
        const result = await response.json();
        document.getElementById('uploadStatus').textContent = 'Parsing complete!';
        
        // Show validation interface
        setTimeout(() => {
            showInvoiceValidation(result);
        }, 500);
        
    } catch (error) {
        document.getElementById('uploadStatus').textContent = 'Error: ' + error.message;
        alert('Error uploading invoice: ' + error.message);
    }
}

async function showInvoiceValidation(uploadResult) {
    const materials = await apiCall('/api/materials/');
    const invoice = uploadResult.invoice;
    const items = uploadResult.items;
    
    const html = `
        <h2>Validate Invoice Items</h2>
        <div class="invoice-details">
            <p><strong>Supplier:</strong> ${invoice.supplier || 'Not detected'}</p>
            <p><strong>Invoice Number:</strong> ${invoice.invoice_number || 'Not detected'}</p>
            <p><strong>Date:</strong> ${invoice.invoice_date || 'Not detected'}</p>
            <p><strong>Total:</strong> ${invoice.total_amount ? invoice.total_amount.toFixed(2) + ' RON' : 'Not detected'}</p>
        </div>
        
        <h3>Extracted Items (${items.length})</h3>
        <p>Please validate the materials extracted from the invoice. You can match to existing materials or create new ones.</p>
        
        <form id="validationForm" onsubmit="submitInvoiceValidation(event, ${invoice.id})">
            <table>
                <thead>
                    <tr>
                        <th>Description</th>
                        <th>Qty</th>
                        <th>Unit</th>
                        <th>Unit Price</th>
                        <th>Total</th>
                        <th>Action</th>
                        <th>Material</th>
                    </tr>
                </thead>
                <tbody>
                    ${items.map((item, index) => {
                        const suggestedMaterial = item.suggested_material_id ? 
                            materials.find(m => m.id === item.suggested_material_id) : null;
                        
                        return `
                            <tr id="item-row-${index}">
                                <td>${item.description || '-'}</td>
                                <td>${item.quantity || 0}</td>
                                <td>${item.unit || '-'}</td>
                                <td>${item.unit_price ? item.unit_price.toFixed(2) : '-'}</td>
                                <td>${item.total_price ? item.total_price.toFixed(2) : '-'}</td>
                                <td>
                                    <select id="action-${index}" onchange="toggleMaterialOptions(${index})">
                                        <option value="existing" ${suggestedMaterial ? 'selected' : ''}>Use Existing</option>
                                        <option value="new">Create New</option>
                                    </select>
                                </td>
                                <td>
                                    <div id="existing-${index}" style="display: ${suggestedMaterial ? 'block' : 'block'};">
                                        <select id="material-${index}">
                                            <option value="">Select Material</option>
                                            ${materials.map(m => `
                                                <option value="${m.id}" ${m.id === item.suggested_material_id ? 'selected' : ''}>
                                                    ${m.name} ${m.id === item.suggested_material_id ? `(${Math.round(item.match_confidence * 100)}% match)` : ''}
                                                </option>
                                            `).join('')}
                                        </select>
                                    </div>
                                    <div id="new-${index}" style="display: none;">
                                        <input type="text" id="newname-${index}" placeholder="Material Name" value="${item.description || ''}" style="margin-bottom: 5px;">
                                        <input type="text" id="newcat-${index}" placeholder="Category" value="General" style="margin-bottom: 5px;">
                                        <input type="text" id="newunit-${index}" placeholder="Unit" value="${item.unit || 'pcs'}" style="margin-bottom: 5px;">
                                        <input type="number" id="newmin-${index}" placeholder="Min Stock" value="0" style="margin-bottom: 5px;">
                                    </div>
                                    <input type="hidden" id="itemid-${index}" value="${item.id}">
                                </td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
            
            <div class="form-actions" style="margin-top: 20px;">
                <button type="submit" class="btn btn-success">✓ Validate & Confirm</button>
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            </div>
        </form>
    `;
    
    showModal(html);
}

function toggleMaterialOptions(index) {
    const action = document.getElementById(`action-${index}`).value;
    document.getElementById(`existing-${index}`).style.display = action === 'existing' ? 'block' : 'none';
    document.getElementById(`new-${index}`).style.display = action === 'new' ? 'block' : 'none';
}

async function submitInvoiceValidation(event, invoiceId) {
    event.preventDefault();
    
    const form = document.getElementById('validationForm');
    const rows = form.querySelectorAll('tbody tr');
    const validatedItems = [];
    
    rows.forEach((row, index) => {
        const action = document.getElementById(`action-${index}`).value;
        const itemId = parseInt(document.getElementById(`itemid-${index}`).value);
        
        if (action === 'existing') {
            const materialId = parseInt(document.getElementById(`material-${index}`).value);
            if (materialId) {
                validatedItems.push({
                    item_id: itemId,
                    material_id: materialId,
                    create_new: false
                });
            }
        } else if (action === 'new') {
            const name = document.getElementById(`newname-${index}`).value;
            const category = document.getElementById(`newcat-${index}`).value;
            const unit = document.getElementById(`newunit-${index}`).value;
            const minStock = parseFloat(document.getElementById(`newmin-${index}`).value) || 0;
            
            if (name) {
                validatedItems.push({
                    item_id: itemId,
                    create_new: true,
                    new_material: {
                        name: name,
                        category: category,
                        unit: unit,
                        minimum_stock: minStock
                    }
                });
            }
        }
    });
    
    if (validatedItems.length === 0) {
        alert('Please select or create materials for at least one item');
        return;
    }
    
    try {
        const result = await apiCall(`/api/invoices/${invoiceId}/validate-items`, {
            method: 'POST',
            body: JSON.stringify(validatedItems)
        });
        
        alert(`Success! ${result.created_materials} new materials created, ${result.updated_items} items mapped.`);
        
        // Ask if user wants to confirm invoice now
        if (confirm('Do you want to confirm this invoice and create stock movements now?')) {
            await confirmInvoice(invoiceId);
        } else {
            closeModal();
            loadInvoices();
        }
        
    } catch (error) {
        alert('Error validating items: ' + error.message);
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
