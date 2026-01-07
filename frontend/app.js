// FLEET Vehicle Management JavaScript

class FleetApp {
    constructor() {
        // Environment-specific API URL (set during deployment)
        this.apiUrl = 'https://f8bf6be68k.execute-api.eu-west-1.amazonaws.com/dev';
        
        this.vehicles = [];
        this.currentVehicle = null;
        this.serviceRecords = [];
        this.maintenanceAlerts = [];
        this.costAnalysis = [];
        this.fleetComparison = [];
        this.highCostAlerts = [];
        
        // Driver management data
        this.drivers = [];
        this.currentDriver = null;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadVehicles();
        this.loadMaintenanceAlerts();
        
        // Load cost analysis if the section exists
        if (document.getElementById('costAnalysisSection')) {
            this.loadCostAnalysis();
        }
    }
    
    bindEvents() {
        // Navigation tabs
        document.getElementById('vehiclesTab').addEventListener('click', () => {
            this.showVehiclesTab();
        });
        
        document.getElementById('driversTab').addEventListener('click', () => {
            this.showDriversTab();
        });
        
        // Vehicle form submission
        document.getElementById('vehicleForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addVehicle();
        });
        
        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.loadVehicles();
        });
        
        // Service record form submission
        document.getElementById('serviceRecordForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addServiceRecord();
        });
        
        // Service record form controls
        document.getElementById('cancelServiceForm').addEventListener('click', () => {
            this.hideServiceForm();
        });
        
        document.getElementById('addServiceRecordBtn').addEventListener('click', () => {
            this.showServiceForm();
        });
        
        document.getElementById('closeServiceHistory').addEventListener('click', () => {
            this.hideServiceHistory();
        });
        
        // Maintenance alerts refresh
        document.getElementById('refreshAlertsBtn').addEventListener('click', () => {
            this.loadMaintenanceAlerts();
        });
        
        // Cost analysis navigation - check if elements exist first
        const costAnalysisTab = document.getElementById('costAnalysisTab');
        const fleetComparisonTab = document.getElementById('fleetComparisonTab');
        const highCostAlertsTab = document.getElementById('highCostAlertsTab');
        
        if (costAnalysisTab) {
            costAnalysisTab.addEventListener('click', () => {
                this.showCostAnalysis();
            });
        }
        
        if (fleetComparisonTab) {
            fleetComparisonTab.addEventListener('click', () => {
                this.showFleetComparison();
            });
        }
        
        if (highCostAlertsTab) {
            highCostAlertsTab.addEventListener('click', () => {
                this.showHighCostAlerts();
            });
        }
        
        // Cost analysis refresh buttons - check if elements exist first
        const refreshCostAnalysisBtn = document.getElementById('refreshCostAnalysisBtn');
        const refreshFleetComparisonBtn = document.getElementById('refreshFleetComparisonBtn');
        const refreshHighCostAlertsBtn = document.getElementById('refreshHighCostAlertsBtn');
        
        if (refreshCostAnalysisBtn) {
            refreshCostAnalysisBtn.addEventListener('click', () => {
                this.loadCostAnalysis();
            });
        }
        
        if (refreshFleetComparisonBtn) {
            refreshFleetComparisonBtn.addEventListener('click', () => {
                this.loadFleetComparison();
            });
        }
        
        if (refreshHighCostAlertsBtn) {
            refreshHighCostAlertsBtn.addEventListener('click', () => {
                this.loadHighCostAlerts();
            });
        }
        
        // Driver management event bindings
        const driverForm = document.getElementById('driverForm');
        if (driverForm) {
            driverForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.addDriver();
            });
        }
        
        const refreshDriversBtn = document.getElementById('refreshDriversBtn');
        if (refreshDriversBtn) {
            refreshDriversBtn.addEventListener('click', () => {
                this.loadDrivers();
            });
        }
        
        const closeDriverDetails = document.getElementById('closeDriverDetails');
        if (closeDriverDetails) {
            closeDriverDetails.addEventListener('click', () => {
                this.hideDriverDetails();
            });
        }
        
        const editDriverBtn = document.getElementById('editDriverBtn');
        if (editDriverBtn) {
            editDriverBtn.addEventListener('click', () => {
                this.showEditDriverForm();
            });
        }
        
        const editDriverForm = document.getElementById('editDriverForm');
        if (editDriverForm) {
            editDriverForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.updateDriver();
            });
        }
        
        const cancelEditDriver = document.getElementById('cancelEditDriver');
        if (cancelEditDriver) {
            cancelEditDriver.addEventListener('click', () => {
                this.hideEditDriverForm();
            });
        }
        
        // Vehicle assignment event bindings
        const assignVehicleBtn = document.getElementById('assignVehicleBtn');
        if (assignVehicleBtn) {
            assignVehicleBtn.addEventListener('click', () => {
                this.showAssignVehicleForm();
            });
        }
        
        const assignVehicleForm = document.getElementById('assignVehicleForm');
        if (assignVehicleForm) {
            assignVehicleForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.assignVehicle();
            });
        }
        
        const cancelAssignVehicle = document.getElementById('cancelAssignVehicle');
        if (cancelAssignVehicle) {
            cancelAssignVehicle.addEventListener('click', () => {
                this.hideAssignVehicleForm();
            });
        }
        
        // Performance tracking event bindings
        const addPerformanceRecordBtn = document.getElementById('addPerformanceRecordBtn');
        if (addPerformanceRecordBtn) {
            addPerformanceRecordBtn.addEventListener('click', () => {
                this.showAddPerformanceForm();
            });
        }
        
        const addPerformanceForm = document.getElementById('addPerformanceForm');
        if (addPerformanceForm) {
            addPerformanceForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.addPerformanceRecord();
            });
        }
        
        const cancelAddPerformance = document.getElementById('cancelAddPerformance');
        if (cancelAddPerformance) {
            cancelAddPerformance.addEventListener('click', () => {
                this.hideAddPerformanceForm();
            });
        }
    }
    
    getApiUrl() {
        return this.apiUrl;
    }
    
    showStatus(message, type = 'success') {
        const statusEl = document.getElementById('statusMessage');
        statusEl.textContent = message;
        statusEl.className = `status-message ${type}`;
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            statusEl.className = 'status-message hidden';
        }, 3000);
    }
    
    async loadVehicles() {
        try {
            const response = await fetch(`${this.getApiUrl()}/vehicles`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.vehicles = data.vehicles || [];
            this.renderVehicles();
            this.updateVehicleCount();
            
        } catch (error) {
            console.error('Error loading vehicles:', error);
            this.showStatus(`Failed to load vehicles: ${error.message}`, 'error');
            document.getElementById('vehicleList').innerHTML = 
                '<div class="loading">Failed to load vehicles. Please check your connection and try again.</div>';
        }
    }
    
    async addVehicle() {
        const formData = new FormData(document.getElementById('vehicleForm'));
        const vehicleData = {
            make: formData.get('make').trim(),
            model: formData.get('model').trim(),
            year: parseInt(formData.get('year')),
            registration: formData.get('registration').trim().toUpperCase(),
            vin: formData.get('vin').trim() || null
        };
        
        // Basic validation
        if (!vehicleData.make || !vehicleData.model || !vehicleData.registration) {
            this.showStatus('Please fill in all required fields', 'error');
            return;
        }
        
        if (vehicleData.year < 1900 || vehicleData.year > 2030) {
            this.showStatus('Please enter a valid year', 'error');
            return;
        }
        
        try {
            const response = await fetch(`${this.getApiUrl()}/vehicles`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(vehicleData)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            const newVehicle = await response.json();
            this.showStatus(`Vehicle ${vehicleData.make} ${vehicleData.model} added successfully!`);
            
            // Reset form
            document.getElementById('vehicleForm').reset();
            
            // Reload vehicles
            this.loadVehicles();
            
        } catch (error) {
            console.error('Error adding vehicle:', error);
            this.showStatus(`Failed to add vehicle: ${error.message}`, 'error');
        }
    }
    
    async deleteVehicle(vehicleId) {
        if (!confirm('Are you sure you want to delete this vehicle?')) {
            return;
        }
        
        try {
            const response = await fetch(`${this.getApiUrl()}/vehicles/${vehicleId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            this.showStatus('Vehicle deleted successfully!');
            this.loadVehicles();
            
        } catch (error) {
            console.error('Error deleting vehicle:', error);
            this.showStatus(`Failed to delete vehicle: ${error.message}`, 'error');
        }
    }
    
    renderVehicles() {
        const vehicleList = document.getElementById('vehicleList');
        
        if (this.vehicles.length === 0) {
            vehicleList.innerHTML = '<div class="loading">No vehicles found. Add your first vehicle above!</div>';
            return;
        }
        
        vehicleList.innerHTML = this.vehicles.map(vehicle => this.renderVehicleCard(vehicle)).join('');
        
        // Bind delete buttons
        vehicleList.querySelectorAll('.btn-delete').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const vehicleId = e.target.dataset.vehicleId;
                this.deleteVehicle(vehicleId);
            });
        });
        
        // Bind service history buttons
        vehicleList.querySelectorAll('.btn-service').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const vehicleId = e.target.dataset.vehicleId;
                this.showServiceHistory(vehicleId);
            });
        });
    }
    
    renderVehicleCard(vehicle) {
        // Handle both API response formats (column names vs proper field names)
        const id = vehicle.column_0 || vehicle.id;
        const make = vehicle.column_1 || vehicle.make;
        const model = vehicle.column_2 || vehicle.model;
        const year = vehicle.column_3 || vehicle.year;
        const registration = vehicle.column_4 || vehicle.registration;
        const vin = vehicle.column_5 || vehicle.vin;
        const status = vehicle.column_6 || vehicle.status || 'active';
        const createdAt = vehicle.column_8 || vehicle.created_at;
        
        const formattedDate = createdAt ? new Date(createdAt).toLocaleDateString() : 'Unknown';
        
        return `
            <div class="vehicle-card">
                <h3>${make} ${model} (${year})</h3>
                <div class="vehicle-info">
                    <p><strong>Registration:</strong> ${registration}</p>
                    ${vin ? `<p><strong>VIN:</strong> ${vin}</p>` : ''}
                    <p><strong>Status:</strong> <span class="vehicle-status status-${status}">${status.replace('_', ' ')}</span></p>
                    <p><strong>Added:</strong> ${formattedDate}</p>
                </div>
                <div class="vehicle-actions">
                    <button class="btn-service" data-vehicle-id="${id}">🔧 Service History</button>
                    <button class="btn-delete" data-vehicle-id="${id}">🗑️ Delete</button>
                </div>
            </div>
        `;
    }
    
    updateVehicleCount() {
        const countEl = document.getElementById('vehicleCount');
        const count = this.vehicles.length;
        countEl.textContent = `${count} vehicle${count !== 1 ? 's' : ''} in fleet`;
    }
    
    // Service Records Methods
    async showServiceHistory(vehicleId) {
        // Find the vehicle
        this.currentVehicle = this.vehicles.find(v => (v.column_0 || v.id) === vehicleId);
        if (!this.currentVehicle) {
            this.showStatus('Vehicle not found', 'error');
            return;
        }
        
        // Update title
        const make = this.currentVehicle.column_1 || this.currentVehicle.make;
        const model = this.currentVehicle.column_2 || this.currentVehicle.model;
        const registration = this.currentVehicle.column_4 || this.currentVehicle.registration;
        document.getElementById('serviceHistoryTitle').textContent = 
            `Service History - ${make} ${model} (${registration})`;
        
        // Show service history container
        document.getElementById('serviceHistoryContainer').style.display = 'block';
        document.getElementById('serviceFormContainer').style.display = 'none';
        
        // Load service records
        await this.loadServiceHistory(vehicleId);
        
        // Scroll to service records section
        document.querySelector('.service-records-section').scrollIntoView({ behavior: 'smooth' });
    }
    
    hideServiceHistory() {
        document.getElementById('serviceHistoryContainer').style.display = 'none';
        this.currentVehicle = null;
    }
    
    showServiceForm() {
        if (!this.currentVehicle) {
            this.showStatus('Please select a vehicle first', 'error');
            return;
        }
        
        // Set vehicle ID in hidden field
        const vehicleId = this.currentVehicle.column_0 || this.currentVehicle.id;
        document.getElementById('serviceVehicleId').value = vehicleId;
        
        // Set default service date to today
        document.getElementById('serviceDate').value = new Date().toISOString().split('T')[0];
        
        // Show form
        document.getElementById('serviceFormContainer').style.display = 'block';
    }
    
    hideServiceForm() {
        document.getElementById('serviceFormContainer').style.display = 'none';
        document.getElementById('serviceRecordForm').reset();
    }
    
    async loadServiceHistory(vehicleId) {
        try {
            const response = await fetch(`${this.getApiUrl()}/vehicles/${vehicleId}/service-records`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.serviceRecords = data.service_records || [];
            this.renderServiceHistory();
            
        } catch (error) {
            console.error('Error loading service history:', error);
            this.showStatus(`Failed to load service history: ${error.message}`, 'error');
            document.getElementById('serviceHistoryList').innerHTML = 
                '<div class="loading">Failed to load service history. Please try again.</div>';
        }
    }
    
    async addServiceRecord() {
        const formData = new FormData(document.getElementById('serviceRecordForm'));
        const serviceData = {
            maintenance_type_id: parseInt(formData.get('maintenance_type_id')),
            description: formData.get('description').trim(),
            cost: parseFloat(formData.get('cost')),
            service_date: formData.get('service_date'),
            service_provider: formData.get('service_provider').trim(),
            mileage: formData.get('mileage') ? parseInt(formData.get('mileage')) : null,
            is_warranty: formData.get('is_warranty') === 'on',
            next_service_due: formData.get('next_service_due') || null,
            notes: formData.get('notes').trim() || null
        };
        
        // Basic validation
        if (!serviceData.description || !serviceData.service_provider || serviceData.cost < 0) {
            this.showStatus('Please fill in all required fields correctly', 'error');
            return;
        }
        
        const vehicleId = document.getElementById('serviceVehicleId').value;
        
        try {
            const response = await fetch(`${this.getApiUrl()}/vehicles/${vehicleId}/service-records`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(serviceData)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            this.showStatus('Service record added successfully!');
            this.hideServiceForm();
            
            // Reload service history
            await this.loadServiceHistory(vehicleId);
            
            // Refresh maintenance alerts
            this.loadMaintenanceAlerts();
            
        } catch (error) {
            console.error('Error adding service record:', error);
            this.showStatus(`Failed to add service record: ${error.message}`, 'error');
        }
    }
    
    renderServiceHistory() {
        const historyList = document.getElementById('serviceHistoryList');
        
        if (this.serviceRecords.length === 0) {
            historyList.innerHTML = '<div class="loading">No service records found. Add the first service record above!</div>';
            return;
        }
        
        // Sort by service date (newest first)
        const sortedRecords = [...this.serviceRecords].sort((a, b) => 
            new Date(b.service_date) - new Date(a.service_date)
        );
        
        historyList.innerHTML = sortedRecords.map(record => this.renderServiceRecordCard(record)).join('');
    }
    
    renderServiceRecordCard(record) {
        const serviceDate = new Date(record.service_date).toLocaleDateString();
        const cost = parseFloat(record.cost).toFixed(2);
        const maintenanceType = record.maintenance_type_name || 'Unknown';
        
        return `
            <div class="service-record-card">
                <div class="service-record-header">
                    <span class="service-record-type">${maintenanceType}</span>
                    <span class="service-record-cost">R${cost}</span>
                </div>
                <div class="service-record-details">
                    <p><strong>Date:</strong> ${serviceDate}</p>
                    <p><strong>Provider:</strong> ${record.service_provider}</p>
                    ${record.mileage ? `<p><strong>Mileage:</strong> ${record.mileage.toLocaleString()} km</p>` : ''}
                    ${record.is_warranty ? '<p><strong>Type:</strong> Warranty Service</p>' : ''}
                    ${record.next_service_due ? `<p><strong>Next Service:</strong> ${new Date(record.next_service_due).toLocaleDateString()}</p>` : ''}
                </div>
                <div class="service-record-description">
                    ${record.description}
                    ${record.notes ? `<br><small><strong>Notes:</strong> ${record.notes}</small>` : ''}
                </div>
            </div>
        `;
    }
    
    // Maintenance Alerts Methods
    async loadMaintenanceAlerts() {
        try {
            const response = await fetch(`${this.getApiUrl()}/maintenance-alerts`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.maintenanceAlerts = data.alerts || [];
            this.renderMaintenanceAlerts();
            this.updateAlertCount();
            
        } catch (error) {
            console.error('Error loading maintenance alerts:', error);
            this.showStatus(`Failed to load maintenance alerts: ${error.message}`, 'error');
            document.getElementById('maintenanceAlerts').innerHTML = 
                '<div class="loading">Failed to load maintenance alerts. Please try again.</div>';
        }
    }
    
    renderMaintenanceAlerts() {
        const alertsContainer = document.getElementById('maintenanceAlerts');
        
        if (this.maintenanceAlerts.length === 0) {
            alertsContainer.innerHTML = '<div class="no-alerts">No maintenance alerts - all vehicles are up to date!</div>';
            return;
        }
        
        alertsContainer.innerHTML = this.maintenanceAlerts.map(alert => this.renderAlertCard(alert)).join('');
    }
    
    renderAlertCard(alert) {
        const alertType = alert.alert_type || 'unknown';
        const alertTypeClass = alertType.replace('_', '-');
        const alertTypeDisplay = alertType.replace('_', ' ').toUpperCase();
        
        // Convert string values to numbers for proper formatting
        const totalCost = parseFloat(alert.total_cost) || 0;
        
        return `
            <div class="alert-card alert-${alertTypeClass}">
                <div class="alert-header">
                    <span class="alert-type ${alertType}">${alertTypeDisplay}</span>
                </div>
                <div class="alert-vehicle">${alert.make || 'Unknown'} ${alert.model || 'Unknown'} (${alert.registration || 'Unknown'})</div>
                <div class="alert-message">${alert.alert_message || 'No message available'}</div>
                <div class="alert-details">
                    ${alert.last_service_date ? `Last Service: ${new Date(alert.last_service_date).toLocaleDateString()}` : 'No service history'}
                    ${alert.total_cost ? `<br>Total Cost (12 months): R${totalCost.toFixed(2)}` : ''}
                    ${alert.next_service_due ? `<br>Next Service Due: ${new Date(alert.next_service_due).toLocaleDateString()}` : ''}
                </div>
            </div>
        `;
    }
    
    updateAlertCount() {
        const countEl = document.getElementById('alertCount');
        const count = this.maintenanceAlerts.length;
        countEl.textContent = `${count} alert${count !== 1 ? 's' : ''}`;
    }
    
    // Cost Analysis Methods
    showCostAnalysis() {
        this.hideAllTabs();
        document.getElementById('costAnalysisSection').style.display = 'block';
        this.setActiveTab('costAnalysisTab');
        this.loadCostAnalysis();
    }
    
    showFleetComparison() {
        this.hideAllTabs();
        document.getElementById('fleetComparisonSection').style.display = 'block';
        this.setActiveTab('fleetComparisonTab');
        this.loadFleetComparison();
    }
    
    showHighCostAlerts() {
        this.hideAllTabs();
        document.getElementById('highCostAlertsSection').style.display = 'block';
        this.setActiveTab('highCostAlertsTab');
        this.loadHighCostAlerts();
    }
    
    hideAllTabs() {
        document.getElementById('costAnalysisSection').style.display = 'none';
        document.getElementById('fleetComparisonSection').style.display = 'none';
        document.getElementById('highCostAlertsSection').style.display = 'none';
    }
    
    setActiveTab(activeTabId) {
        // Remove active class from all tabs
        document.querySelectorAll('.cost-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        // Add active class to selected tab
        document.getElementById(activeTabId).classList.add('active');
    }
    
    async loadCostAnalysis() {
        try {
            const response = await fetch(`${this.getApiUrl()}/cost-analysis`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.costAnalysis = data.cost_analysis || [];
            this.renderCostAnalysis(data);
            
        } catch (error) {
            console.error('Error loading cost analysis:', error);
            this.showStatus(`Failed to load cost analysis: ${error.message}`, 'error');
            document.getElementById('costAnalysisContent').innerHTML = 
                '<div class="loading">Failed to load cost analysis. Please try again.</div>';
        }
    }
    
    async loadFleetComparison() {
        try {
            const response = await fetch(`${this.getApiUrl()}/fleet-cost-comparison`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.fleetComparison = data.fleet_comparison || [];
            this.renderFleetComparison(data);
            
        } catch (error) {
            console.error('Error loading fleet comparison:', error);
            this.showStatus(`Failed to load fleet comparison: ${error.message}`, 'error');
            document.getElementById('fleetComparisonContent').innerHTML = 
                '<div class="loading">Failed to load fleet comparison. Please try again.</div>';
        }
    }
    
    async loadHighCostAlerts() {
        try {
            const response = await fetch(`${this.getApiUrl()}/high-cost-alerts`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.highCostAlerts = data.high_cost_alerts || [];
            this.renderHighCostAlerts(data);
            
        } catch (error) {
            console.error('Error loading high cost alerts:', error);
            this.showStatus(`Failed to load high cost alerts: ${error.message}`, 'error');
            document.getElementById('highCostAlertsContent').innerHTML = 
                '<div class="loading">Failed to load high cost alerts. Please try again.</div>';
        }
    }
    
    renderCostAnalysis(data) {
        const content = document.getElementById('costAnalysisContent');
        
        if (this.costAnalysis.length === 0) {
            content.innerHTML = '<div class="no-data">No cost analysis data available. Add vehicles and service records to see cost analysis.</div>';
            return;
        }
        
        // Summary section - convert string values to numbers
        const summary = data.summary || {};
        const totalVehicles = parseInt(summary.total_vehicles) || 0;
        const totalCost = parseFloat(summary.total_cost) || 0;
        const totalServices = parseInt(summary.total_services) || 0;
        const avgCostPerVehicle = parseFloat(summary.avg_cost_per_vehicle) || 0;
        
        const summaryHtml = `
            <div class="cost-summary">
                <h3>Fleet Cost Summary</h3>
                <div class="summary-grid">
                    <div class="summary-item">
                        <span class="summary-label">Total Vehicles</span>
                        <span class="summary-value">${totalVehicles}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Total Cost</span>
                        <span class="summary-value">R${totalCost.toFixed(2)}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Total Services</span>
                        <span class="summary-value">${totalServices}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Avg Cost/Vehicle</span>
                        <span class="summary-value">R${avgCostPerVehicle.toFixed(2)}</span>
                    </div>
                </div>
            </div>
        `;
        
        // Cost analysis by maintenance type
        const byTypeHtml = this.renderCostByMaintenanceType(data.by_maintenance_type || {});
        
        // Detailed cost analysis
        const detailsHtml = `
            <div class="cost-details">
                <h3>Detailed Cost Analysis</h3>
                <div class="cost-analysis-list">
                    ${this.costAnalysis.map(item => this.renderCostAnalysisItem(item)).join('')}
                </div>
            </div>
        `;
        
        content.innerHTML = summaryHtml + byTypeHtml + detailsHtml;
    }
    
    renderCostByMaintenanceType(byType) {
        if (Object.keys(byType).length === 0) {
            return '<div class="no-data">No maintenance type data available.</div>';
        }
        
        const typeItems = Object.entries(byType).map(([type, data]) => {
            // Convert string values to numbers for proper formatting
            const totalCost = parseFloat(data.total_cost) || 0;
            const serviceCount = parseInt(data.service_count) || 0;
            const vehicleCount = parseInt(data.vehicle_count) || 0;
            
            return `
                <div class="maintenance-type-item">
                    <div class="type-header">
                        <span class="type-name">${type}</span>
                        <span class="type-cost">R${totalCost.toFixed(2)}</span>
                    </div>
                    <div class="type-details">
                        <span>Services: ${serviceCount}</span>
                        <span>Vehicles: ${vehicleCount}</span>
                    </div>
                </div>
            `;
        }).join('');
        
        return `
            <div class="cost-by-type">
                <h3>Cost by Maintenance Type</h3>
                <div class="maintenance-types-list">
                    ${typeItems}
                </div>
            </div>
        `;
    }
    
    renderCostAnalysisItem(item) {
        const costCategory = item.cost_category || 'normal';
        const categoryClass = costCategory.replace('_', '-');
        
        // Convert string values to numbers for proper formatting
        const totalCost = parseFloat(item.total_cost) || 0;
        const avgCost = parseFloat(item.avg_cost) || 0;
        const fleetAvgCost = parseFloat(item.fleet_avg_cost) || 0;
        const serviceCount = parseInt(item.service_count) || 0;
        
        return `
            <div class="cost-analysis-item cost-${categoryClass}">
                <div class="cost-item-header">
                    <span class="vehicle-name">${item.make} ${item.model} (${item.registration})</span>
                    <span class="cost-category ${categoryClass}">${costCategory.replace('_', ' ').toUpperCase()}</span>
                </div>
                <div class="cost-item-details">
                    <div class="cost-detail">
                        <span class="detail-label">Maintenance Type:</span>
                        <span class="detail-value">${item.maintenance_type}</span>
                    </div>
                    <div class="cost-detail">
                        <span class="detail-label">Total Cost:</span>
                        <span class="detail-value">R${totalCost.toFixed(2)}</span>
                    </div>
                    <div class="cost-detail">
                        <span class="detail-label">Service Count:</span>
                        <span class="detail-value">${serviceCount}</span>
                    </div>
                    <div class="cost-detail">
                        <span class="detail-label">Average Cost:</span>
                        <span class="detail-value">R${avgCost.toFixed(2)}</span>
                    </div>
                    <div class="cost-detail">
                        <span class="detail-label">Fleet Average:</span>
                        <span class="detail-value">R${fleetAvgCost.toFixed(2)}</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderFleetComparison(data) {
        const content = document.getElementById('fleetComparisonContent');
        
        if (this.fleetComparison.length === 0) {
            content.innerHTML = '<div class="no-data">No fleet comparison data available. Add vehicles and service records to see fleet comparison.</div>';
            return;
        }
        
        // Fleet summary - convert string values to numbers
        const summary = data.fleet_summary || {};
        const totalVehicles = parseInt(summary.total_vehicles) || 0;
        const vehiclesWithService = parseInt(summary.vehicles_with_service) || 0;
        const highCostVehicles = parseInt(summary.high_cost_vehicles) || 0;
        const fleetTotalCost = parseFloat(summary.fleet_total_cost) || 0;
        
        const summaryHtml = `
            <div class="fleet-summary">
                <h3>Fleet Overview</h3>
                <div class="summary-grid">
                    <div class="summary-item">
                        <span class="summary-label">Total Vehicles</span>
                        <span class="summary-value">${totalVehicles}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">With Service History</span>
                        <span class="summary-value">${vehiclesWithService}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">High Cost Vehicles</span>
                        <span class="summary-value high-cost">${highCostVehicles}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Fleet Total Cost</span>
                        <span class="summary-value">R${fleetTotalCost.toFixed(2)}</span>
                    </div>
                </div>
            </div>
        `;
        
        // Vehicle comparison list
        const comparisonHtml = `
            <div class="fleet-comparison-list">
                <h3>Vehicle Cost Comparison</h3>
                ${this.fleetComparison.map(vehicle => this.renderFleetComparisonItem(vehicle)).join('')}
            </div>
        `;
        
        content.innerHTML = summaryHtml + comparisonHtml;
    }
    
    renderFleetComparisonItem(vehicle) {
        const costCategory = vehicle.cost_category || 'normal_cost';
        const categoryClass = costCategory.replace('_', '-');
        
        // Convert string values to numbers for proper formatting
        const totalCost = parseFloat(vehicle.total_cost) || 0;
        const totalServices = parseInt(vehicle.total_services) || 0;
        const avgServiceCost = parseFloat(vehicle.avg_service_cost) || 0;
        const fleetAvgCost = parseFloat(vehicle.fleet_avg_cost) || 0;
        const variancePercent = parseFloat(vehicle.cost_variance_percent) || 0;
        const estimatedMonthlyCost = parseFloat(vehicle.estimated_monthly_cost) || 0;
        
        const varianceClass = variancePercent > 0 ? 'positive' : variancePercent < 0 ? 'negative' : 'neutral';
        
        return `
            <div class="fleet-comparison-item ${categoryClass}">
                <div class="comparison-header">
                    <span class="vehicle-name">${vehicle.make} ${vehicle.model} (${vehicle.registration})</span>
                    <span class="cost-category ${categoryClass}">${costCategory.replace('_', ' ').toUpperCase()}</span>
                </div>
                <div class="comparison-details">
                    <div class="comparison-row">
                        <div class="comparison-detail">
                            <span class="detail-label">Total Cost:</span>
                            <span class="detail-value">R${totalCost.toFixed(2)}</span>
                        </div>
                        <div class="comparison-detail">
                            <span class="detail-label">Services:</span>
                            <span class="detail-value">${totalServices}</span>
                        </div>
                        <div class="comparison-detail">
                            <span class="detail-label">Avg Service Cost:</span>
                            <span class="detail-value">R${avgServiceCost.toFixed(2)}</span>
                        </div>
                    </div>
                    <div class="comparison-row">
                        <div class="comparison-detail">
                            <span class="detail-label">Fleet Average:</span>
                            <span class="detail-value">R${fleetAvgCost.toFixed(2)}</span>
                        </div>
                        <div class="comparison-detail">
                            <span class="detail-label">Variance:</span>
                            <span class="detail-value ${varianceClass}">${variancePercent > 0 ? '+' : ''}${variancePercent.toFixed(1)}%</span>
                        </div>
                        <div class="comparison-detail">
                            <span class="detail-label">Est. Monthly:</span>
                            <span class="detail-value">R${estimatedMonthlyCost.toFixed(2)}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderHighCostAlerts(data) {
        const content = document.getElementById('highCostAlertsContent');
        
        if (this.highCostAlerts.length === 0) {
            content.innerHTML = '<div class="no-alerts">No high cost alerts - all vehicles are within normal cost ranges!</div>';
            return;
        }
        
        // Alert summary - convert string values to numbers
        const summary = data.alert_summary || {};
        const critical = parseInt(summary.critical) || 0;
        const high = parseInt(summary.high) || 0;
        const moderate = parseInt(summary.moderate) || 0;
        const totalExcessCost = parseFloat(data.total_excess_cost) || 0;
        
        const summaryHtml = `
            <div class="alert-summary">
                <h3>High Cost Alert Summary</h3>
                <div class="alert-summary-grid">
                    <div class="alert-summary-item critical">
                        <span class="alert-count">${critical}</span>
                        <span class="alert-label">Critical</span>
                    </div>
                    <div class="alert-summary-item high">
                        <span class="alert-count">${high}</span>
                        <span class="alert-label">High</span>
                    </div>
                    <div class="alert-summary-item moderate">
                        <span class="alert-count">${moderate}</span>
                        <span class="alert-label">Moderate</span>
                    </div>
                    <div class="alert-summary-item total">
                        <span class="alert-count">R${totalExcessCost.toFixed(2)}</span>
                        <span class="alert-label">Total Excess Cost</span>
                    </div>
                </div>
            </div>
        `;
        
        // High cost alerts list
        const alertsHtml = `
            <div class="high-cost-alerts-list">
                <h3>High Cost Vehicles</h3>
                ${this.highCostAlerts.map(alert => this.renderHighCostAlertItem(alert)).join('')}
            </div>
        `;
        
        content.innerHTML = summaryHtml + alertsHtml;
    }
    
    renderHighCostAlertItem(alert) {
        const severity = alert.alert_severity || 'moderate';
        
        // Convert string values to numbers for proper formatting
        const totalCost = parseFloat(alert.total_cost) || 0;
        const avgFleetCost = parseFloat(alert.avg_fleet_cost) || 0;
        const variancePercent = parseFloat(alert.cost_variance_percent) || 0;
        const serviceCount = parseInt(alert.service_count) || 0;
        
        return `
            <div class="high-cost-alert-item ${severity}">
                <div class="alert-item-header">
                    <span class="vehicle-name">${alert.make} ${alert.model} (${alert.registration})</span>
                    <span class="alert-severity ${severity}">${severity.toUpperCase()}</span>
                </div>
                <div class="alert-item-message">
                    ${alert.alert_message}
                </div>
                <div class="alert-item-details">
                    <div class="alert-detail">
                        <span class="detail-label">Total Cost (12 months):</span>
                        <span class="detail-value">R${totalCost.toFixed(2)}</span>
                    </div>
                    <div class="alert-detail">
                        <span class="detail-label">Fleet Average:</span>
                        <span class="detail-value">R${avgFleetCost.toFixed(2)}</span>
                    </div>
                    <div class="alert-detail">
                        <span class="detail-label">Variance:</span>
                        <span class="detail-value positive">+${variancePercent.toFixed(1)}%</span>
                    </div>
                    <div class="alert-detail">
                        <span class="detail-label">Service Count:</span>
                        <span class="detail-value">${serviceCount}</span>
                    </div>
                    <div class="alert-detail">
                        <span class="detail-label">Maintenance Types:</span>
                        <span class="detail-value">${alert.maintenance_types || 'N/A'}</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Navigation Methods
    showVehiclesTab() {
        // Update tab buttons
        document.getElementById('vehiclesTab').classList.add('active');
        document.getElementById('driversTab').classList.remove('active');
        
        // Update content visibility
        document.getElementById('vehiclesContent').classList.add('active');
        document.getElementById('driversContent').classList.remove('active');
        
        // Load vehicles if not already loaded
        if (this.vehicles.length === 0) {
            this.loadVehicles();
        }
    }
    
    showDriversTab() {
        // Update tab buttons
        document.getElementById('driversTab').classList.add('active');
        document.getElementById('vehiclesTab').classList.remove('active');
        
        // Update content visibility
        document.getElementById('driversContent').classList.add('active');
        document.getElementById('vehiclesContent').classList.remove('active');
        
        // Load drivers
        this.loadDrivers();
    }
    
    // Driver Management Methods
    async loadDrivers() {
        try {
            const response = await fetch(`${this.getApiUrl()}/drivers`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.drivers = data.drivers || [];
            this.renderDrivers();
            
            // Update driver count
            const countEl = document.getElementById('driverCount');
            if (countEl) {
                countEl.textContent = `${this.drivers.length} driver${this.drivers.length !== 1 ? 's' : ''}`;
            }
            
        } catch (error) {
            console.error('Error loading drivers:', error);
            this.showStatus('Failed to load drivers. Please try again.', 'error');
        }
    }
    
    renderDrivers() {
        const driverList = document.getElementById('driverList');
        if (!driverList) return;
        
        if (this.drivers.length === 0) {
            driverList.innerHTML = `
                <div class="empty-state">
                    <h3>No drivers found</h3>
                    <p>Add your first driver using the form above.</p>
                </div>
            `;
            return;
        }
        
        driverList.innerHTML = this.drivers.map(driver => {
            const address = typeof driver.address === 'string' ? JSON.parse(driver.address) : driver.address;
            const emergencyContact = typeof driver.emergency_contact === 'string' ? JSON.parse(driver.emergency_contact) : driver.emergency_contact;
            
            return `
                <div class="driver-card" onclick="app.showDriverDetails('${driver.id}')">
                    <h3>${driver.first_name} ${driver.last_name}</h3>
                    <div class="driver-info">
                        <span><strong>License:</strong> ${driver.license_number}</span>
                        <span><strong>Phone:</strong> ${driver.phone}</span>
                        <span><strong>Email:</strong> ${driver.email || 'Not provided'}</span>
                        <span><strong>City:</strong> ${address?.city || 'Not provided'}</span>
                        <span><strong>License Expires:</strong> ${new Date(driver.license_expiry_date).toLocaleDateString()}</span>
                    </div>
                    <span class="driver-status ${driver.status}">${driver.status}</span>
                </div>
            `;
        }).join('');
    }
    
    async addDriver() {
        try {
            const form = document.getElementById('driverForm');
            const formData = new FormData(form);
            
            // Build address object
            const address = {
                street: formData.get('address_street'),
                city: formData.get('address_city'),
                province: formData.get('address_province') || '',
                postal_code: formData.get('address_postal_code') || ''
            };
            
            // Build emergency contact object
            const emergencyContact = {
                name: formData.get('emergency_name') || '',
                phone: formData.get('emergency_phone') || '',
                relationship: formData.get('emergency_relationship') || ''
            };
            
            const driverData = {
                first_name: formData.get('first_name'),
                last_name: formData.get('last_name'),
                id_number: formData.get('id_number'),
                email: formData.get('email') || '',
                phone: formData.get('phone'),
                license_number: formData.get('license_number'),
                license_expiry_date: formData.get('license_expiry_date'),
                address: address,
                emergency_contact: emergencyContact
            };
            
            const response = await fetch(`${this.getApiUrl()}/drivers`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(driverData)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            this.showStatus('Driver added successfully!');
            form.reset();
            this.loadDrivers();
            
        } catch (error) {
            console.error('Error adding driver:', error);
            this.showStatus(`Failed to add driver: ${error.message}`, 'error');
        }
    }
    
    async showDriverDetails(driverId) {
        try {
            // Load driver details with assignment info
            const response = await fetch(`${this.getApiUrl()}/drivers/${driverId}?include_assignment=true`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.currentDriver = data.driver;
            this.renderDriverDetails();
            
            // Load and render current assignment
            if (this.currentDriver.current_assignment) {
                this.renderCurrentAssignment(this.currentDriver.current_assignment);
            } else {
                this.renderCurrentAssignment(null);
            }
            
            // Load and render assignment history
            const assignments = await this.loadDriverAssignments(driverId);
            this.renderAssignmentHistory(assignments);
            
            // Load and render performance records
            await this.loadDriverPerformance(driverId);
            
            // Show driver details section
            document.getElementById('driverDetailsSection').style.display = 'block';
            document.getElementById('driverDetailsSection').scrollIntoView({ behavior: 'smooth' });
            
        } catch (error) {
            console.error('Error loading driver details:', error);
            this.showStatus('Failed to load driver details. Please try again.', 'error');
        }
    }
    
    renderDriverDetails() {
        if (!this.currentDriver) return;
        
        const driver = this.currentDriver;
        const address = typeof driver.address === 'string' ? JSON.parse(driver.address) : driver.address;
        const emergencyContact = typeof driver.emergency_contact === 'string' ? JSON.parse(driver.emergency_contact) : driver.emergency_contact;
        
        const detailsContent = document.getElementById('driverDetailsContent');
        if (!detailsContent) return;
        
        detailsContent.innerHTML = `
            <div class="driver-detail-section">
                <h4>Personal Information</h4>
                <div class="detail-item">
                    <span class="detail-label">Full Name:</span>
                    <span class="detail-value">${driver.first_name} ${driver.last_name}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">ID Number:</span>
                    <span class="detail-value">${driver.id_number}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Email:</span>
                    <span class="detail-value">${driver.email || 'Not provided'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Phone:</span>
                    <span class="detail-value">${driver.phone}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Status:</span>
                    <span class="detail-value">
                        <span class="driver-status ${driver.status}">${driver.status}</span>
                    </span>
                </div>
            </div>
            
            <div class="driver-detail-section">
                <h4>License & Address</h4>
                <div class="detail-item">
                    <span class="detail-label">License Number:</span>
                    <span class="detail-value">${driver.license_number}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">License Expires:</span>
                    <span class="detail-value">${new Date(driver.license_expiry_date).toLocaleDateString()}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Address:</span>
                    <span class="detail-value">
                        ${address?.street || ''}<br>
                        ${address?.city || ''} ${address?.province || ''} ${address?.postal_code || ''}
                    </span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Emergency Contact:</span>
                    <span class="detail-value">
                        ${emergencyContact?.name || 'Not provided'}<br>
                        ${emergencyContact?.phone || ''} (${emergencyContact?.relationship || ''})
                    </span>
                </div>
            </div>
        `;
    }
    
    hideDriverDetails() {
        document.getElementById('driverDetailsSection').style.display = 'none';
        document.getElementById('editDriverSection').style.display = 'none';
        document.getElementById('assignVehicleSection').style.display = 'none';
        this.currentDriver = null;
    }
    
    showEditDriverForm() {
        if (!this.currentDriver) return;
        
        const driver = this.currentDriver;
        const address = typeof driver.address === 'string' ? JSON.parse(driver.address) : driver.address;
        
        // Populate edit form
        document.getElementById('editDriverId').value = driver.id;
        document.getElementById('editFirstName').value = driver.first_name;
        document.getElementById('editLastName').value = driver.last_name;
        document.getElementById('editEmail').value = driver.email || '';
        document.getElementById('editPhone').value = driver.phone;
        document.getElementById('editLicenseNumber').value = driver.license_number;
        document.getElementById('editLicenseExpiryDate').value = driver.license_expiry_date;
        document.getElementById('editStatus').value = driver.status;
        
        // Show edit form
        document.getElementById('editDriverSection').style.display = 'block';
        document.getElementById('editDriverSection').scrollIntoView({ behavior: 'smooth' });
    }
    
    hideEditDriverForm() {
        document.getElementById('editDriverSection').style.display = 'none';
    }
    
    async updateDriver() {
        try {
            const form = document.getElementById('editDriverForm');
            const formData = new FormData(form);
            const driverId = formData.get('driver_id');
            
            const updateData = {
                first_name: formData.get('first_name'),
                last_name: formData.get('last_name'),
                email: formData.get('email') || '',
                phone: formData.get('phone'),
                license_number: formData.get('license_number'),
                license_expiry_date: formData.get('license_expiry_date'),
                status: formData.get('status')
            };
            
            const response = await fetch(`${this.getApiUrl()}/drivers/${driverId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(updateData)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            this.showStatus('Driver updated successfully!');
            this.hideEditDriverForm();
            this.loadDrivers();
            
            // Refresh driver details if still showing
            if (this.currentDriver && this.currentDriver.id === driverId) {
                this.showDriverDetails(driverId);
            }
            
        } catch (error) {
            console.error('Error updating driver:', error);
            this.showStatus(`Failed to update driver: ${error.message}`, 'error');
        }
    }
    
    // Vehicle Assignment Methods
    async showAssignVehicleForm() {
        if (!this.currentDriver) {
            this.showStatus('Please select a driver first', 'error');
            return;
        }
        
        // Set driver ID in hidden field
        document.getElementById('assignDriverId').value = this.currentDriver.id;
        
        // Set default assignment date to today
        document.getElementById('assignmentStartDate').value = new Date().toISOString().split('T')[0];
        
        // Load available vehicles
        await this.loadAvailableVehicles();
        
        // Show assignment form
        document.getElementById('assignVehicleSection').style.display = 'block';
        document.getElementById('assignVehicleSection').scrollIntoView({ behavior: 'smooth' });
    }
    
    hideAssignVehicleForm() {
        document.getElementById('assignVehicleSection').style.display = 'none';
        document.getElementById('assignVehicleForm').reset();
    }
    
    async loadAvailableVehicles() {
        try {
            const response = await fetch(`${this.getApiUrl()}/vehicles`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            const vehicles = data.vehicles || [];
            
            // Filter to only show active vehicles without current drivers
            const availableVehicles = vehicles.filter(v => {
                const status = v.status || 'active';
                const currentDriverId = v.current_driver_id;
                return status === 'active' && !currentDriverId;
            });
            
            // Populate select dropdown
            const select = document.getElementById('assignVehicleSelect');
            select.innerHTML = '<option value="">Select an available vehicle...</option>';
            
            if (availableVehicles.length === 0) {
                select.innerHTML += '<option value="" disabled>No available vehicles</option>';
            } else {
                availableVehicles.forEach(vehicle => {
                    const option = document.createElement('option');
                    option.value = vehicle.id;
                    option.textContent = `${vehicle.make} ${vehicle.model} (${vehicle.registration})`;
                    select.appendChild(option);
                });
            }
            
        } catch (error) {
            console.error('Error loading available vehicles:', error);
            this.showStatus('Failed to load available vehicles', 'error');
        }
    }
    
    async assignVehicle() {
        try {
            const form = document.getElementById('assignVehicleForm');
            const formData = new FormData(form);
            const driverId = formData.get('driver_id');
            
            const assignmentData = {
                vehicle_id: formData.get('vehicle_id'),
                assignment_start_date: formData.get('assignment_start_date'),
                notes: formData.get('notes') || ''
            };
            
            if (!assignmentData.vehicle_id) {
                this.showStatus('Please select a vehicle', 'error');
                return;
            }
            
            const response = await fetch(`${this.getApiUrl()}/drivers/${driverId}/assignments`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(assignmentData)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            this.showStatus('Vehicle assigned successfully!');
            this.hideAssignVehicleForm();
            
            // Refresh driver details to show new assignment
            this.showDriverDetails(driverId);
            
            // Refresh drivers list to update assignment status
            this.loadDrivers();
            
        } catch (error) {
            console.error('Error assigning vehicle:', error);
            this.showStatus(`Failed to assign vehicle: ${error.message}`, 'error');
        }
    }
    
    async loadDriverAssignments(driverId) {
        try {
            const response = await fetch(`${this.getApiUrl()}/drivers/${driverId}/assignments`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            return data.assignments || [];
            
        } catch (error) {
            console.error('Error loading driver assignments:', error);
            return [];
        }
    }
    
    renderCurrentAssignment(assignment) {
        const content = document.getElementById('currentAssignmentContent');
        
        if (!assignment) {
            content.innerHTML = '<div class="no-assignment">No current vehicle assignment</div>';
            return;
        }
        
        const startDate = new Date(assignment.assignment_start_date).toLocaleDateString();
        
        content.innerHTML = `
            <div class="current-assignment-card">
                <div class="assignment-vehicle">
                    <h4>🚗 ${assignment.make} ${assignment.model}</h4>
                    <span class="vehicle-registration">${assignment.registration}</span>
                </div>
                <div class="assignment-details">
                    <div class="detail-item">
                        <span class="detail-label">Year:</span>
                        <span class="detail-value">${assignment.year}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Assigned Since:</span>
                        <span class="detail-value">${startDate}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Status:</span>
                        <span class="detail-value assignment-status ${assignment.assignment_status}">${assignment.assignment_status}</span>
                    </div>
                    ${assignment.assignment_notes ? `
                    <div class="detail-item">
                        <span class="detail-label">Notes:</span>
                        <span class="detail-value">${assignment.assignment_notes}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    renderAssignmentHistory(assignments) {
        const content = document.getElementById('assignmentHistoryContent');
        
        if (!assignments || assignments.length === 0) {
            content.innerHTML = '<div class="no-history">No assignment history</div>';
            return;
        }
        
        content.innerHTML = assignments.map(assignment => {
            const startDate = new Date(assignment.assignment_start_date).toLocaleDateString();
            const endDate = assignment.assignment_end_date 
                ? new Date(assignment.assignment_end_date).toLocaleDateString() 
                : 'Present';
            
            return `
                <div class="assignment-history-card ${assignment.status}">
                    <div class="assignment-vehicle-info">
                        <span class="vehicle-name">${assignment.make} ${assignment.model}</span>
                        <span class="vehicle-registration">(${assignment.registration})</span>
                    </div>
                    <div class="assignment-dates">
                        <span>${startDate} - ${endDate}</span>
                    </div>
                    <span class="assignment-status-badge ${assignment.status}">${assignment.status}</span>
                </div>
            `;
        }).join('');
    }
    
    // Performance Tracking Methods
    async showAddPerformanceForm() {
        if (!this.currentDriver) {
            this.showStatus('Please select a driver first', 'error');
            return;
        }
        
        // Set driver ID and vehicle ID in hidden fields
        document.getElementById('performanceDriverId').value = this.currentDriver.id;
        
        // Get current vehicle assignment
        if (this.currentDriver.current_assignment) {
            document.getElementById('performanceVehicleId').value = this.currentDriver.current_assignment.vehicle_id;
        } else {
            this.showStatus('Driver must have an active vehicle assignment to record performance', 'error');
            return;
        }
        
        // Set default week start date to last Monday
        const today = new Date();
        const dayOfWeek = today.getDay();
        const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
        const lastMonday = new Date(today);
        lastMonday.setDate(today.getDate() - daysToMonday);
        document.getElementById('weekStartDate').value = lastMonday.toISOString().split('T')[0];
        
        // Show form
        document.getElementById('addPerformanceSection').style.display = 'block';
        document.getElementById('addPerformanceSection').scrollIntoView({ behavior: 'smooth' });
    }
    
    hideAddPerformanceForm() {
        document.getElementById('addPerformanceSection').style.display = 'none';
        document.getElementById('addPerformanceForm').reset();
    }
    
    async addPerformanceRecord() {
        try {
            const form = document.getElementById('addPerformanceForm');
            const formData = new FormData(form);
            const driverId = formData.get('driver_id');
            
            const performanceData = {
                vehicle_id: formData.get('vehicle_id'),
                week_start_date: formData.get('week_start_date'),
                card_earnings: parseFloat(formData.get('card_earnings')),
                cash_trips_value: parseFloat(formData.get('cash_trips_value')),
                total_trips: parseInt(formData.get('total_trips')),
                cash_trips_count: parseInt(formData.get('cash_trips_count')),
                notes: formData.get('notes') || ''
            };
            
            // Validation
            if (performanceData.cash_trips_count > performanceData.total_trips) {
                this.showStatus('Cash trips count cannot exceed total trips', 'error');
                return;
            }
            
            const response = await fetch(`${this.getApiUrl()}/drivers/${driverId}/performance`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(performanceData)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            this.showStatus('Performance record added successfully!');
            this.hideAddPerformanceForm();
            
            // Refresh performance records
            await this.loadDriverPerformance(driverId);
            
        } catch (error) {
            console.error('Error adding performance record:', error);
            this.showStatus(`Failed to add performance record: ${error.message}`, 'error');
        }
    }
    
    async loadDriverPerformance(driverId) {
        try {
            const response = await fetch(`${this.getApiUrl()}/drivers/${driverId}/performance`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.renderPerformanceRecords(data.performance_records || []);
            this.renderPerformanceSummary(data.summary || {});
            
        } catch (error) {
            console.error('Error loading driver performance:', error);
            this.showStatus('Failed to load performance records', 'error');
        }
    }
    
    renderPerformanceRecords(records) {
        const content = document.getElementById('performanceRecordsContent');
        
        if (!records || records.length === 0) {
            content.innerHTML = '<div class="no-records">No performance records found. Add the first record above!</div>';
            return;
        }
        
        content.innerHTML = records.map(record => {
            const weekStart = new Date(record.week_start_date).toLocaleDateString();
            const weekEnd = new Date(record.week_end_date).toLocaleDateString();
            const totalEarnings = parseFloat(record.total_earnings) || 0;
            const cardEarnings = parseFloat(record.card_earnings) || 0;
            const cashValue = parseFloat(record.cash_trips_value) || 0;
            const cashPercentage = parseFloat(record.cash_trip_percentage) || 0;
            const settlementAmount = parseFloat(record.settlement_amount) || 0;
            const shortfallAmount = parseFloat(record.shortfall_amount) || 0;
            const targetAchieved = record.target_achieved;
            
            const statusClass = targetAchieved ? 'achieved' : 'not-achieved';
            const statusText = targetAchieved ? '✓ Target Achieved' : '✗ Target Not Met';
            
            return `
                <div class="performance-record-card ${statusClass}">
                    <div class="performance-header">
                        <span class="performance-week">${weekStart} - ${weekEnd}</span>
                        <span class="performance-status ${statusClass}">${statusText}</span>
                    </div>
                    <div class="performance-details">
                        <div class="performance-row">
                            <div class="performance-item">
                                <span class="performance-label">Total Earnings:</span>
                                <span class="performance-value">R${totalEarnings.toFixed(2)}</span>
                            </div>
                            <div class="performance-item">
                                <span class="performance-label">Card Earnings:</span>
                                <span class="performance-value">R${cardEarnings.toFixed(2)}</span>
                            </div>
                            <div class="performance-item">
                                <span class="performance-label">Cash Trips:</span>
                                <span class="performance-value">R${cashValue.toFixed(2)}</span>
                            </div>
                        </div>
                        <div class="performance-row">
                            <div class="performance-item">
                                <span class="performance-label">Total Trips:</span>
                                <span class="performance-value">${record.total_trips}</span>
                            </div>
                            <div class="performance-item">
                                <span class="performance-label">Cash Trips:</span>
                                <span class="performance-value">${record.cash_trips_count} (${cashPercentage.toFixed(1)}%)</span>
                            </div>
                            <div class="performance-item">
                                <span class="performance-label">Settlement:</span>
                                <span class="performance-value">R${settlementAmount.toFixed(2)}</span>
                            </div>
                        </div>
                        ${shortfallAmount > 0 ? `
                        <div class="performance-shortfall">
                            <span class="shortfall-label">⚠️ Shortfall:</span>
                            <span class="shortfall-value">R${shortfallAmount.toFixed(2)}</span>
                        </div>
                        ` : ''}
                        ${record.notes ? `
                        <div class="performance-notes">
                            <strong>Notes:</strong> ${record.notes}
                        </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }).join('');
    }
    
    renderPerformanceSummary(summary) {
        const content = document.getElementById('performanceSummaryContent');
        
        if (!summary || Object.keys(summary).length === 0) {
            content.innerHTML = '';
            return;
        }
        
        const totalWeeks = parseInt(summary.total_weeks) || 0;
        const weeksAchieved = parseInt(summary.weeks_target_achieved) || 0;
        const avgEarnings = parseFloat(summary.avg_weekly_earnings) || 0;
        const avgCashPercentage = parseFloat(summary.avg_cash_percentage) || 0;
        const totalSettlements = parseFloat(summary.total_settlements) || 0;
        const totalShortfalls = parseFloat(summary.total_shortfalls) || 0;
        const achievementRate = totalWeeks > 0 ? (weeksAchieved / totalWeeks * 100) : 0;
        
        content.innerHTML = `
            <h4>Performance Summary</h4>
            <div class="summary-grid">
                <div class="summary-item">
                    <span class="summary-label">Total Weeks:</span>
                    <span class="summary-value">${totalWeeks}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Target Achievement Rate:</span>
                    <span class="summary-value">${achievementRate.toFixed(1)}%</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Avg Weekly Earnings:</span>
                    <span class="summary-value">R${avgEarnings.toFixed(2)}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Avg Cash %:</span>
                    <span class="summary-value">${avgCashPercentage.toFixed(1)}%</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Total Settlements:</span>
                    <span class="summary-value">R${totalSettlements.toFixed(2)}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Total Shortfalls:</span>
                    <span class="summary-value">R${totalShortfalls.toFixed(2)}</span>
                </div>
            </div>
        `;
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new FleetApp();
});
