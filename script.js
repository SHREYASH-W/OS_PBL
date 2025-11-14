// API Configuration
const API_BASE = 'http://localhost:5000/api';

// Track if auto-refresh should pause
let pauseAutoRefresh = false;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('🔒 Deadlock Tool initialized');
    console.log('Connecting to backend at:', API_BASE);
    
    // Test backend connection
    testBackendConnection();
    
    // Initial updates
    updateOSMonitor();
    updateStatus();
    updateTables();
    updateLog();
    updateGraph();
    
    // Auto-refresh OS monitor every 1 second
    setInterval(() => {
        updateOSMonitor();
    }, 1000);
    
    // Auto-refresh simulation data every 2 seconds
    setInterval(() => {
        if (!pauseAutoRefresh) {
            updateStatus();
            updateTables();
            updateLog();
            updateGraph();
        }
    }, 2000);
});

// Test backend connection
async function testBackendConnection() {
    try {
        const response = await fetch(`${API_BASE}/status`);
        if (response.ok) {
            console.log('✅ Backend connection successful');
        } else {
            console.error('❌ Backend returned error:', response.status);
            showConnectionError();
        }
    } catch (error) {
        console.error('❌ Cannot connect to backend:', error);
        showConnectionError();
    }
}

function showConnectionError() {
    const logContainer = document.getElementById('activityLog');
    logContainer.innerHTML = `
        <div class="log-entry error">
            <span class="log-time">ERROR</span>
            <span class="log-message">❌ Cannot connect to backend server. Make sure Flask is running on port 5000.</span>
        </div>
        <div class="log-entry warning">
            <span class="log-time">INFO</span>
            <span class="log-message">Run: python app.py</span>
        </div>
    `;
}

// Update Real-Time OS Monitor
async function updateOSMonitor() {
    try {
        const response = await fetch(`${API_BASE}/os-monitor`);
        const data = await response.json();
        
        if (data.error) {
            console.error('Error fetching OS data:', data.error);
            return;
        }
        
        // Update CPU stats
        document.getElementById('cpuUsage').textContent = `${data.cpu.percent}%`;
        document.getElementById('cpuCores').textContent = data.cpu.count;
        
        // Update Memory stats
        document.getElementById('memoryUsage').textContent = `${data.memory.percent}%`;
        document.getElementById('memoryUsed').textContent = data.memory.used;
        document.getElementById('memoryTotal').textContent = data.memory.total;
        
        // Update Disk stats
        document.getElementById('diskUsage').textContent = `${data.disk.percent}%`;
        document.getElementById('diskUsed').textContent = data.disk.used;
        document.getElementById('diskTotal').textContent = data.disk.total;
        
        // Update process count
        document.getElementById('osProcessCount').textContent = data.process_count;
        
        // Update top processes table
        const tbody = document.getElementById('osProcessTableBody');
        if (data.processes && data.processes.length > 0) {
            tbody.innerHTML = data.processes.map(proc => `
                <tr>
                    <td>${proc.pid}</td>
                    <td>${proc.name}</td>
                    <td><span class="badge badge-${proc.cpu > 50 ? 'high' : proc.cpu > 20 ? 'medium' : 'low'}">${proc.cpu}%</span></td>
                    <td>${proc.memory}%</td>
                    <td><span class="badge badge-${proc.status === 'running' ? 'available' : 'allocated'}">${proc.status}</span></td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No process data available</td></tr>';
        }
    } catch (error) {
        console.error('Error updating OS monitor:', error);
    }
}

// Prevent multiple simultaneous calls
let isProcessing = false;

// Add Process Function
async function addProcess() {
    if (isProcessing) {
        console.log('Already processing, please wait...');
        return;
    }
    
    const processId = document.getElementById('processId').value.trim();
    const priority = document.getElementById('processPriority').value;

    console.log('Adding process:', processId, priority);

    if (!processId) {
        alert('⚠️ Please enter a process ID');
        return;
    }

    isProcessing = true;
    pauseAutoRefresh = true;

    // Show loading state
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = 'Adding...';
    button.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                processId: processId,
                priority: priority
            })
        });
        
        const data = await response.json();
        console.log('Response:', response.status, data);
        
        if (response.ok && data.success) {
            // Clear input
            document.getElementById('processId').value = '';
            
            // Show success message
            showNotification(`✅ Process ${processId} added successfully!`, 'success');
            
            // Update UI immediately
            await updateDropdowns();
            await updateTables();
            await updateStatus();
            await updateLog();
        } else {
            showNotification(`❌ Error: ${data.error || 'Failed to add process'}`, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('❌ Error connecting to backend. Make sure Flask server is running.', 'error');
    } finally {
        button.textContent = originalText;
        button.disabled = false;
        isProcessing = false;
        pauseAutoRefresh = false;
    }
}

// Add Resource Function
async function addResource() {
    const resourceId = document.getElementById('resourceId').value.trim();
    const resourceType = document.getElementById('resourceType').value;

    console.log('Adding resource:', resourceId, resourceType);

    if (!resourceId) {
        alert('⚠️ Please enter a resource ID');
        return;
    }

    pauseAutoRefresh = true;

    try {
        const response = await fetch(`${API_BASE}/resource`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                resourceId: resourceId,
                resourceType: resourceType
            })
        });
        
        const data = await response.json();
        console.log('Response:', data);
        
        if (response.ok && data.success) {
            // Clear input
            document.getElementById('resourceId').value = '';
            
            // Update UI immediately
            await updateDropdowns();
            await updateTables();
            await updateStatus();
            await updateLog();
            
            alert(`✅ Resource ${resourceId} added successfully!`);
        } else {
            alert(`❌ Error: ${data.error || 'Failed to add resource'}`);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('❌ Error connecting to backend. Make sure Flask server is running:\n\npython app.py');
    } finally {
        pauseAutoRefresh = false;
    }
}

// Request Resource Function
async function requestResource() {
    const processId = document.getElementById('reqProcessId').value;
    const resourceId = document.getElementById('reqResourceId').value;

    console.log('Requesting resource:', processId, resourceId);

    if (!processId || !resourceId) {
        alert('⚠️ Please select both process and resource');
        return;
    }

    pauseAutoRefresh = true;

    try {
        const response = await fetch(`${API_BASE}/request`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                processId: processId,
                resourceId: resourceId
            })
        });
        
        const data = await response.json();
        console.log('Response:', data);
        
        if (data.success) {
            if (data.allocated) {
                alert(`✅ Resource ${resourceId} allocated to ${processId}`);
            } else if (data.waiting) {
                alert(`⏳ Process ${processId} is waiting for ${resourceId}\n(Currently held by ${data.holder})`);
            }
        } else {
            if (data.prevented) {
                alert(`⚠️ REQUEST DENIED\n\n${data.message}\n\nThis request would cause a deadlock!`);
            } else {
                alert(`❌ ${data.message || 'Request failed'}`);
            }
        }
        
        // Update UI
        await updateTables();
        await updateStatus();
        await updateGraph();
        await updateLog();
        
    } catch (error) {
        console.error('Error:', error);
        alert('❌ Error connecting to backend. Make sure Flask server is running:\n\npython app.py');
    } finally {
        pauseAutoRefresh = false;
    }
}

// Detect Deadlock Function
async function detectDeadlock() {
    console.log('Detecting deadlock...');
    
    try {
        const response = await fetch(`${API_BASE}/detect`, {method: 'POST'});
        const data = await response.json();
        
        console.log('Detection result:', data);
        
        if (data.deadlock) {
            alert(`🚨 DEADLOCK DETECTED!\n\nCycle found:\n${data.cycle.join(' → ')}\n\nUse "Recover System" to resolve the deadlock.`);
        } else {
            alert('✅ No deadlock detected.\n\nSystem is in a safe state.');
        }
        
        await updateStatus();
        await updateLog();
    } catch (error) {
        console.error('Error:', error);
        alert('❌ Error connecting to backend.');
    }
}

// Predict Deadlock Function
async function predictDeadlock() {
    console.log('Predicting deadlock...');
    
    try {
        const response = await fetch(`${API_BASE}/predict`, {method: 'POST'});
        const data = await response.json();
        
        console.log('Prediction result:', data);
        
        if (data.predictions.length > 0) {
            let msg = `⚠️ DEADLOCK PREDICTION\n\nFound ${data.predictions.length} potential deadlock scenario(s):\n\n`;
            data.predictions.forEach((p, index) => {
                msg += `${index + 1}. ${p.process} requesting ${p.resource} - ${p.risk.toUpperCase()} RISK\n`;
            });
            msg += '\n⚠️ Avoid these resource requests to prevent deadlocks!';
            alert(msg);
        } else {
            alert('✅ No deadlock risks detected!\n\nAll possible resource requests are safe.');
        }
        
        await updateLog();
    } catch (error) {
        console.error('Error:', error);
        alert('❌ Error connecting to backend.');
    }
}

// Recover System Function
async function recoverDeadlock() {
    if (!confirm('⚠️ SYSTEM RECOVERY\n\nThis will terminate a process to recover from deadlock.\n\nDo you want to continue?')) {
        return;
    }

    console.log('Recovering from deadlock...');

    try {
        const response = await fetch(`${API_BASE}/recover`, {method: 'POST'});
        const data = await response.json();
        
        console.log('Recovery result:', data);
        
        if (data.success) {
            alert(`✅ RECOVERY SUCCESSFUL\n\nTerminated Process: ${data.victim}\nReleased Resources: ${data.released.join(', ')}\n\nSystem is now in a safe state.`);
            await updateTables();
            await updateStatus();
            await updateGraph();
            await updateLog();
        } else {
            alert(`❌ ${data.error}\n\nMake sure there is a deadlock to recover from.`);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('❌ Error connecting to backend.');
    }
}

// Reset System Function
async function resetSystem() {
    if (!confirm('⚠️ SYSTEM RESET\n\nThis will remove all processes and resources.\n\nAre you sure you want to reset the system?')) {
        return;
    }

    console.log('Resetting system...');

    try {
        const response = await fetch(`${API_BASE}/reset`, {method: 'POST'});
        
        if (response.ok) {
            alert('✅ System reset successfully!\n\nAll processes and resources have been removed.');
            await updateTables();
            await updateStatus();
            await updateDropdowns();
            await updateGraph();
            
            document.getElementById('activityLog').innerHTML = '<div class="log-entry info"><span class="log-time">00:00:00</span><span class="log-message">System reset and reinitialized</span></div>';
        }
    } catch (error) {
        console.error('Error:', error);
        alert('❌ Error connecting to backend.');
    }
}

// Update System Status
async function updateStatus() {
    try {
        const response = await fetch(`${API_BASE}/status`);
        const data = await response.json();

        document.getElementById('systemStatus').textContent = data.status;
        document.getElementById('activeProcesses').textContent = data.activeProcesses;
        document.getElementById('totalResources').textContent = data.totalResources;
        document.getElementById('deadlocksDetected').textContent = data.deadlocksDetected;
        document.getElementById('deadlocksPrevented').textContent = data.deadlocksPrevented;

        const statusCard = document.getElementById('statusCard');
        const statusIcon = statusCard.querySelector('.status-icon');
        
        if (data.status === 'DEADLOCK') {
            statusCard.className = 'status-card deadlock';
            statusIcon.textContent = '🚨';
        } else {
            statusCard.className = 'status-card safe';
            statusIcon.textContent = '✅';
        }
    } catch (error) {
        console.error('Error updating status:', error);
    }
}

// Update Process and Resource Tables
async function updateTables() {
    try {
        const processResponse = await fetch(`${API_BASE}/processes`);
        const processes = await processResponse.json();
        
        const processTableBody = document.getElementById('processTableBody');
        
        if (processes.length === 0) {
            processTableBody.innerHTML = '<tr><td colspan="4" class="empty-state">No processes added yet</td></tr>';
        } else {
            processTableBody.innerHTML = processes.map(p => `
                <tr>
                    <td><strong>${p.id}</strong></td>
                    <td><span class="badge badge-${p.priority}">${p.priority.toUpperCase()}</span></td>
                    <td>${p.heldResources.length > 0 ? p.heldResources.join(', ') : '-'}</td>
                    <td>${p.waitingFor.length > 0 ? p.waitingFor.join(', ') : '-'}</td>
                </tr>
            `).join('');
        }

        const resourceResponse = await fetch(`${API_BASE}/resources`);
        const resources = await resourceResponse.json();
        
        const resourceTableBody = document.getElementById('resourceTableBody');
        
        if (resources.length === 0) {
            resourceTableBody.innerHTML = '<tr><td colspan="5" class="empty-state">No resources added yet</td></tr>';
        } else {
            resourceTableBody.innerHTML = resources.map(r => `
                <tr>
                    <td><strong>${r.id}</strong></td>
                    <td>${r.type}</td>
                    <td><span class="badge badge-${r.status}">${r.status.toUpperCase()}</span></td>
                    <td>${r.heldBy || '-'}</td>
                    <td>${r.waitingProcesses.length > 0 ? r.waitingProcesses.join(', ') : '-'}</td>
                </tr>
            `).join('');
        }

        await updateDropdowns();
    } catch (error) {
        console.error('Error updating tables:', error);
    }
}

// Update Dropdown Menus
async function updateDropdowns() {
    try {
        const processResponse = await fetch(`${API_BASE}/processes`);
        const processes = await processResponse.json();
        
        const processSelect = document.getElementById('reqProcessId');
        const currentProcessValue = processSelect.value;
        processSelect.innerHTML = '<option value="">Select Process</option>' +
            processes.map(p => `<option value="${p.id}">${p.id} (${p.priority})</option>`).join('');
        
        // Restore selection if it still exists
        if (currentProcessValue && processes.some(p => p.id === currentProcessValue)) {
            processSelect.value = currentProcessValue;
        }

        const resourceResponse = await fetch(`${API_BASE}/resources`);
        const resources = await resourceResponse.json();
        
        const resourceSelect = document.getElementById('reqResourceId');
        const currentResourceValue = resourceSelect.value;
        resourceSelect.innerHTML = '<option value="">Select Resource</option>' +
            resources.map(r => `<option value="${r.id}">${r.id} (${r.type}) - ${r.status}</option>`).join('');
        
        // Restore selection if it still exists
        if (currentResourceValue && resources.some(r => r.id === currentResourceValue)) {
            resourceSelect.value = currentResourceValue;
        }
    } catch (error) {
        console.error('Error updating dropdowns:', error);
    }
}

// Update Activity Log
async function updateLog() {
    try {
        const response = await fetch(`${API_BASE}/log`);
        const logs = await response.json();
        
        const logContainer = document.getElementById('activityLog');
        
        if (logs.length === 0) {
            logContainer.innerHTML = '<div class="log-entry info"><span class="log-time">00:00:00</span><span class="log-message">No activity yet</span></div>';
            return;
        }
        
        logContainer.innerHTML = logs.map(log => `
            <div class="log-entry ${log.type}">
                <span class="log-time">${log.time}</span>
                <span class="log-message">${log.message}</span>
            </div>
        `).join('');
        
        logContainer.scrollTop = logContainer.scrollHeight;
    } catch (error) {
        console.error('Error updating log:', error);
    }
}

// Update Resource Allocation Graph
async function updateGraph() {
    try {
        const response = await fetch(`${API_BASE}/graph`);
        const data = await response.json();
        
        const canvas = document.getElementById('ragCanvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = canvas.offsetWidth;
        canvas.height = 400;
        
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        if (data.nodes.length === 0) {
            ctx.fillStyle = '#666';
            ctx.font = '16px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('No processes or resources to display', canvas.width / 2, canvas.height / 2);
            return;
        }
        
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const radius = Math.min(canvas.width, canvas.height) * 0.35;
        
        const nodePositions = {};
        data.nodes.forEach((node, i) => {
            const angle = (i / data.nodes.length) * 2 * Math.PI - Math.PI / 2;
            nodePositions[node.id] = {
                x: centerX + radius * Math.cos(angle),
                y: centerY + radius * Math.sin(angle),
                type: node.type,
                priority: node.priority,
                resourceType: node.resourceType
            };
        });
        
        data.edges.forEach(edge => {
            const from = nodePositions[edge.from];
            const to = nodePositions[edge.to];
            
            if (!from || !to) return;
            
            const dx = to.x - from.x;
            const dy = to.y - from.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            const unitX = dx / distance;
            const unitY = dy / distance;
            
            const startX = from.x + unitX * 30;
            const startY = from.y + unitY * 30;
            const endX = to.x - unitX * 30;
            const endY = to.y - unitY * 30;
            
            ctx.beginPath();
            ctx.moveTo(startX, startY);
            ctx.lineTo(endX, endY);
            
            if (edge.type === 'allocation') {
                ctx.strokeStyle = '#10b981';
                ctx.lineWidth = 3;
                ctx.setLineDash([]);
            } else {
                ctx.strokeStyle = '#ef4444';
                ctx.lineWidth = 3;
                ctx.setLineDash([8, 4]);
            }
            
            ctx.stroke();
            ctx.setLineDash([]);
            
            const angle = Math.atan2(dy, dx);
            const arrowLength = 15;
            const arrowAngle = Math.PI / 6;
            
            ctx.beginPath();
            ctx.moveTo(endX, endY);
            ctx.lineTo(
                endX - arrowLength * Math.cos(angle - arrowAngle),
                endY - arrowLength * Math.sin(angle - arrowAngle)
            );
            ctx.moveTo(endX, endY);
            ctx.lineTo(
                endX - arrowLength * Math.cos(angle + arrowAngle),
                endY - arrowLength * Math.sin(angle + arrowAngle)
            );
            ctx.strokeStyle = edge.type === 'allocation' ? '#10b981' : '#ef4444';
            ctx.lineWidth = 3;
            ctx.stroke();
        });
        
        data.nodes.forEach(node => {
            const pos = nodePositions[node.id];
            
            ctx.beginPath();
            ctx.arc(pos.x, pos.y, 25, 0, 2 * Math.PI);
            
            if (node.type === 'process') {
                ctx.fillStyle = '#667eea';
            } else {
                ctx.fillStyle = '#10b981';
            }
            
            ctx.fill();
            ctx.strokeStyle = '#333';
            ctx.lineWidth = 2;
            ctx.stroke();
            
            ctx.fillStyle = 'white';
            ctx.font = 'bold 14px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(node.id, pos.x, pos.y);
            
            ctx.fillStyle = '#333';
            ctx.font = '11px Arial';
            ctx.fillText(
                node.type === 'process' ? `(${node.priority})` : `(${node.resourceType})`,
                pos.x,
                pos.y + 40
            );
        });
        
    } catch (error) {
        console.error('Error updating graph:', error);
    }
}