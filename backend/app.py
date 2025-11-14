from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import threading
import time
import psutil
import os

app = Flask(__name__)
CORS(app)

# Global state
processes = {}
resources = {}
allocation_graph = {}
request_graph = {}
resource_holders = {}
resource_waiters = {}
deadlocks_detected = 0
deadlocks_prevented = 0
activity_log = []

# Real-time OS monitoring
real_time_processes = {}
real_time_resources = {}

lock = threading.Lock()

# Helper Functions
def log_activity(message, log_type="info"):
    """Add entry to activity log"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = {
        "time": timestamp,
        "message": message,
        "type": log_type
    }
    activity_log.append(entry)
    if len(activity_log) > 100:
        activity_log.pop(0)

def get_real_time_os_data():
    """Get real-time OS process and resource information"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get top processes
        processes_list = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                pinfo = proc.info
                if pinfo['cpu_percent'] is not None or pinfo['memory_percent'] is not None:
                    processes_list.append({
                        'pid': pinfo['pid'],
                        'name': pinfo['name'][:30],
                        'cpu': round(pinfo['cpu_percent'] or 0, 2),
                        'memory': round(pinfo['memory_percent'] or 0, 2),
                        'status': pinfo['status']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by CPU usage and get top 10
        processes_list.sort(key=lambda x: x['cpu'], reverse=True)
        top_processes = processes_list[:10]
        
        return {
            'cpu': {
                'percent': round(cpu_percent, 2),
                'count': psutil.cpu_count()
            },
            'memory': {
                'total': round(memory.total / (1024**3), 2),
                'used': round(memory.used / (1024**3), 2),
                'percent': round(memory.percent, 2)
            },
            'disk': {
                'total': round(disk.total / (1024**3), 2),
                'used': round(disk.used / (1024**3), 2),
                'percent': round(disk.percent, 2)
            },
            'processes': top_processes,
            'process_count': len(processes_list)
        }
    except Exception as e:
        print(f"Error getting OS data: {e}")
        return None

def detect_cycle():
    """Detect cycle in Resource Allocation Graph using DFS"""
    visited = set()
    rec_stack = set()
    
    def dfs(node, path):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        neighbors = []
        if node.startswith('P'):
            if node in request_graph:
                neighbors.extend(request_graph[node])
        else:
            if node in resource_holders:
                neighbors.append(resource_holders[node])
        
        for neighbor in neighbors:
            if neighbor not in visited:
                result = dfs(neighbor, path[:])
                if result:
                    return result
            elif neighbor in rec_stack:
                cycle_start = path.index(neighbor)
                return path[cycle_start:] + [neighbor]
        
        rec_stack.remove(node)
        return None
    
    for process_id in processes.keys():
        if process_id not in visited:
            result = dfs(process_id, [])
            if result:
                return result
    
    return None

def is_safe_state(test_process=None, test_resource=None):
    """Check if granting a resource request would lead to safe state"""
    temp_allocation = {k: v[:] for k, v in allocation_graph.items()}
    temp_request = {k: v[:] for k, v in request_graph.items()}
    temp_holders = resource_holders.copy()
    
    if test_process and test_resource:
        if test_process not in temp_allocation:
            temp_allocation[test_process] = []
        temp_allocation[test_process].append(test_resource)
        temp_holders[test_resource] = test_process
        if test_process in temp_request and test_resource in temp_request[test_process]:
            temp_request[test_process].remove(test_resource)
    
    visited = set()
    rec_stack = set()
    
    def dfs(node):
        visited.add(node)
        rec_stack.add(node)
        
        neighbors = []
        if node.startswith('P'):
            if node in temp_request:
                neighbors.extend(temp_request[node])
        else:
            if node in temp_holders:
                neighbors.append(temp_holders[node])
        
        for neighbor in neighbors:
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
        
        rec_stack.remove(node)
        return False
    
    for process_id in processes.keys():
        if process_id not in visited:
            if dfs(process_id):
                return False
    
    return True

def get_recovery_victim():
    """Select victim process for recovery based on priority"""
    priority_map = {"low": 0, "medium": 1, "high": 2}
    
    victim = None
    min_priority = float('inf')
    
    for pid, pdata in processes.items():
        priority_val = priority_map.get(pdata['priority'], 1)
        if priority_val < min_priority:
            min_priority = priority_val
            victim = pid
    
    return victim

# API Endpoints
@app.route('/api/os-monitor', methods=['GET'])
def get_os_monitor():
    """Get real-time OS monitoring data"""
    data = get_real_time_os_data()
    if data:
        return jsonify(data)
    return jsonify({"error": "Unable to fetch OS data"}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current system status"""
    with lock:
        cycle = detect_cycle()
        status = "DEADLOCK" if cycle else "SAFE"
        
        return jsonify({
            "status": status,
            "activeProcesses": len(processes),
            "totalResources": len(resources),
            "deadlocksDetected": deadlocks_detected,
            "deadlocksPrevented": deadlocks_prevented,
            "cycle": cycle
        })

@app.route('/api/process', methods=['POST'])
def add_process():
    """Add a new process"""
    data = request.json
    process_id = data.get('processId')
    priority = data.get('priority', 'medium')
    
    with lock:
        if process_id in processes:
            return jsonify({"error": "Process already exists"}), 400
        
        processes[process_id] = {
            "id": process_id,
            "priority": priority,
            "createdAt": datetime.now().isoformat()
        }
        allocation_graph[process_id] = []
        request_graph[process_id] = []
        
        log_activity(f"Process {process_id} added with {priority} priority", "success")
        
        return jsonify({"success": True, "process": processes[process_id]})

@app.route('/api/resource', methods=['POST'])
def add_resource():
    """Add a new resource"""
    data = request.json
    resource_id = data.get('resourceId')
    resource_type = data.get('resourceType', 'CPU')
    
    with lock:
        if resource_id in resources:
            return jsonify({"error": "Resource already exists"}), 400
        
        resources[resource_id] = {
            "id": resource_id,
            "type": resource_type,
            "status": "available",
            "createdAt": datetime.now().isoformat()
        }
        resource_waiters[resource_id] = []
        
        log_activity(f"Resource {resource_id} ({resource_type}) added", "success")
        
        return jsonify({"success": True, "resource": resources[resource_id]})

@app.route('/api/request', methods=['POST'])
def request_resource():
    """Process requests a resource"""
    global deadlocks_prevented
    
    data = request.json
    process_id = data.get('processId')
    resource_id = data.get('resourceId')
    
    with lock:
        if process_id not in processes:
            return jsonify({"error": "Process not found"}), 404
        if resource_id not in resources:
            return jsonify({"error": "Resource not found"}), 404
        
        # Check if resource is available
        if resources[resource_id]["status"] == "available":
            # Predict deadlock before allocation
            if not is_safe_state(process_id, resource_id):
                deadlocks_prevented += 1
                log_activity(f"⚠️ Request denied: {process_id} → {resource_id} would cause deadlock", "warning")
                return jsonify({
                    "success": False,
                    "prevented": True,
                    "message": "Request denied - would cause deadlock"
                })
            
            # Allocate resource
            resources[resource_id]["status"] = "allocated"
            resource_holders[resource_id] = process_id
            allocation_graph[process_id].append(resource_id)
            
            log_activity(f"✓ Resource {resource_id} allocated to {process_id}", "success")
            return jsonify({"success": True, "allocated": True})
        else:
            # Resource is held by another process
            holder = resource_holders.get(resource_id)
            
            # Check if already waiting
            if resource_id in request_graph.get(process_id, []):
                return jsonify({
                    "success": False,
                    "message": "Process already waiting for this resource"
                })
            
            request_graph[process_id].append(resource_id)
            resource_waiters[resource_id].append(process_id)
            
            # Check for immediate deadlock
            cycle = detect_cycle()
            if cycle:
                # Remove the request that caused deadlock
                request_graph[process_id].remove(resource_id)
                resource_waiters[resource_id].remove(process_id)
                deadlocks_prevented += 1
                log_activity(f"⚠️ Request denied: {process_id} → {resource_id} would create cycle", "warning")
                return jsonify({
                    "success": False,
                    "prevented": True,
                    "cycle": cycle,
                    "message": "Request denied - would create cycle"
                })
            
            log_activity(f"Process {process_id} waiting for {resource_id} (held by {holder})", "info")
            return jsonify({"success": True, "waiting": True, "holder": holder})

@app.route('/api/release', methods=['POST'])
def release_resource():
    """Release a resource from a process"""
    data = request.json
    process_id = data.get('processId')
    resource_id = data.get('resourceId')
    
    with lock:
        if resource_id in allocation_graph.get(process_id, []):
            allocation_graph[process_id].remove(resource_id)
            resources[resource_id]["status"] = "available"
            del resource_holders[resource_id]
            
            # Check waiting processes
            if resource_waiters[resource_id]:
                waiting = resource_waiters[resource_id][0]
                log_activity(f"Resource {resource_id} released by {process_id}, {waiting} is waiting", "info")
            else:
                log_activity(f"Resource {resource_id} released and available", "success")
            
            return jsonify({"success": True})
        
        return jsonify({"error": "Resource not held by process"}), 400

@app.route('/api/detect', methods=['POST'])
def detect_deadlock():
    """Detect deadlock in current state"""
    global deadlocks_detected
    
    with lock:
        cycle = detect_cycle()
        
        if cycle:
            deadlocks_detected += 1
            log_activity(f"🚨 DEADLOCK DETECTED: Cycle found - {' → '.join(cycle)}", "error")
            return jsonify({
                "deadlock": True,
                "cycle": cycle,
                "message": "Deadlock detected in system"
            })
        else:
            log_activity("✓ No deadlock detected - system is safe", "success")
            return jsonify({
                "deadlock": False,
                "message": "System is in safe state"
            })

@app.route('/api/predict', methods=['POST'])
def predict_deadlock():
    """Predict potential deadlocks"""
    with lock:
        predictions = []
        
        for pid in processes:
            for rid in resources:
                if rid not in allocation_graph[pid] and rid not in request_graph[pid]:
                    if not is_safe_state(pid, rid):
                        predictions.append({
                            "process": pid,
                            "resource": rid,
                            "risk": "high"
                        })
        
        if predictions:
            log_activity(f"⚠️ Prediction: {len(predictions)} potential deadlock scenarios", "warning")
        else:
            log_activity("✓ Prediction: No deadlock risks detected", "success")
        
        return jsonify({
            "predictions": predictions,
            "riskLevel": "high" if predictions else "low"
        })

@app.route('/api/recover', methods=['POST'])
def recover_system():
    """Recover from deadlock by terminating victim process"""
    with lock:
        cycle = detect_cycle()
        
        if not cycle:
            return jsonify({"error": "No deadlock to recover from"}), 400
        
        victim = None
        for node in cycle:
            if node.startswith('P'):
                victim = node
                break
        
        if not victim:
            victim = get_recovery_victim()
        
        if victim in processes:
            released = allocation_graph.get(victim, [])
            for rid in released:
                resources[rid]["status"] = "available"
                if rid in resource_holders:
                    del resource_holders[rid]
            
            del processes[victim]
            if victim in allocation_graph:
                del allocation_graph[victim]
            if victim in request_graph:
                del request_graph[victim]
            
            log_activity(f"🔄 Recovery: Process {victim} terminated, resources {released} released", "warning")
            
            return jsonify({
                "success": True,
                "victim": victim,
                "released": released,
                "message": f"System recovered by terminating {victim}"
            })
        
        return jsonify({"error": "Recovery failed"}), 500

@app.route('/api/reset', methods=['POST'])
def reset_system():
    """Reset entire system"""
    global deadlocks_detected, deadlocks_prevented
    
    with lock:
        processes.clear()
        resources.clear()
        allocation_graph.clear()
        request_graph.clear()
        resource_holders.clear()
        resource_waiters.clear()
        activity_log.clear()
        deadlocks_detected = 0
        deadlocks_prevented = 0
        
        log_activity("System reset successfully", "info")
        
        return jsonify({"success": True})

@app.route('/api/processes', methods=['GET'])
def get_processes():
    """Get all processes with details"""
    with lock:
        process_list = []
        for pid, pdata in processes.items():
            process_list.append({
                "id": pid,
                "priority": pdata["priority"],
                "heldResources": allocation_graph.get(pid, []),
                "waitingFor": request_graph.get(pid, [])
            })
        return jsonify(process_list)

@app.route('/api/resources', methods=['GET'])
def get_resources():
    """Get all resources with details"""
    with lock:
        resource_list = []
        for rid, rdata in resources.items():
            resource_list.append({
                "id": rid,
                "type": rdata["type"],
                "status": rdata["status"],
                "heldBy": resource_holders.get(rid),
                "waitingProcesses": resource_waiters.get(rid, [])
            })
        return jsonify(resource_list)

@app.route('/api/log', methods=['GET'])
def get_activity_log():
    """Get activity log"""
    with lock:
        return jsonify(activity_log[-50:])

@app.route('/api/graph', methods=['GET'])
def get_graph_data():
    """Get graph data for visualization"""
    with lock:
        nodes = []
        edges = []
        
        for pid in processes:
            nodes.append({
                "id": pid,
                "type": "process",
                "priority": processes[pid]["priority"]
            })
        
        for rid in resources:
            nodes.append({
                "id": rid,
                "type": "resource",
                "resourceType": resources[rid]["type"]
            })
        
        for rid, pid in resource_holders.items():
            edges.append({
                "from": rid,
                "to": pid,
                "type": "allocation"
            })
        
        for pid, resource_list in request_graph.items():
            for rid in resource_list:
                edges.append({
                    "from": pid,
                    "to": rid,
                    "type": "request"
                })
        
        return jsonify({
            "nodes": nodes,
            "edges": edges
        })

if __name__ == '__main__':
    log_activity("System initialized successfully", "info")
    print("=" * 60)
    print("🔒 Deadlock Prediction & Recovery Tool - Backend Server")
    print("=" * 60)
    print("Server running on: http://localhost:5000")
    print("API endpoints available at: http://localhost:5000/api/*")
    print("\nPress CTRL+C to stop the server")
    print("=" * 60)
    app.run(debug=True, port=5000, host='0.0.0.0')