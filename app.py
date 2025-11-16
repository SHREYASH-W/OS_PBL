from flask import Flask, render_template, request, jsonify
import psutil
import os
from datetime import datetime
from deadlock_detector import DeadlockDetector
from process_monitor import ProcessMonitor
from recovery_module import RecoveryModule

app = Flask(__name__)

# Initialize modules
deadlock_detector = DeadlockDetector()
process_monitor = ProcessMonitor()
recovery_module = RecoveryModule()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/manual/add_process', methods=['POST'])
def add_process():
    """Add a process in manual mode"""
    data = request.json
    process_id = data.get('process_id')
    process_name = data.get('process_name')
    
    deadlock_detector.add_process(process_id, process_name)
    return jsonify({'status': 'success', 'message': f'Process {process_name} added'})

@app.route('/api/manual/add_resource', methods=['POST'])
def add_resource():
    """Add a resource in manual mode"""
    data = request.json
    resource_id = data.get('resource_id')
    resource_name = data.get('resource_name')
    instances = data.get('instances', 1)
    
    deadlock_detector.add_resource(resource_id, resource_name, instances)
    return jsonify({'status': 'success', 'message': f'Resource {resource_name} added'})

@app.route('/api/manual/allocate', methods=['POST'])
def allocate_resource():
    """Allocate resource to process"""
    data = request.json
    process_id = data.get('process_id')
    resource_id = data.get('resource_id')
    
    deadlock_detector.allocate_resource(process_id, resource_id)
    return jsonify({'status': 'success'})

@app.route('/api/manual/request', methods=['POST'])
def request_resource():
    """Process requests a resource"""
    data = request.json
    process_id = data.get('process_id')
    resource_id = data.get('resource_id')
    
    deadlock_detector.request_resource(process_id, resource_id)
    return jsonify({'status': 'success'})

@app.route('/api/manual/detect', methods=['GET'])
def detect_deadlock_manual():
    """Detect deadlock in manual mode"""
    result = deadlock_detector.detect_deadlock()
    
    if result['deadlock_detected']:
        # Get full process details for recovery options
        process_details = []
        for process_id in result['deadlock_processes']:
            if process_id in deadlock_detector.processes:
                proc = deadlock_detector.processes[process_id]
                process_details.append({
                    'id': proc['id'],
                    'pid': proc['id'],  # Use id as pid for manual mode
                    'name': proc['name'],
                    'type': 'user',  # Manual processes are always user type
                    'cpu_percent': 0,
                    'memory_percent': 0,
                    'num_threads': 1
                })
        
        recovery_options = recovery_module.generate_recovery_options(
            result['deadlock_cycle'],
            process_details
        )
        result['recovery_options'] = recovery_options
    
    return jsonify(result)

@app.route('/api/manual/predict', methods=['GET'])
def predict_deadlock_manual():
    """Predict if system is in safe state"""
    result = deadlock_detector.predict_deadlock()
    return jsonify(result)

@app.route('/api/manual/predict_allocation', methods=['POST'])
def predict_allocation_manual():
    """Predict if allocation would be safe"""
    data = request.json
    process_id = data.get('process_id')
    resource_id = data.get('resource_id')
    
    result = deadlock_detector.predict_allocation(process_id, resource_id)
    return jsonify(result)

@app.route('/api/manual/get_state', methods=['GET'])
def get_manual_state():
    """Get current state of manual simulation"""
    return jsonify({
        'processes': deadlock_detector.get_processes(),
        'resources': deadlock_detector.get_resources(),
        'graph': deadlock_detector.get_graph_data()
    })

@app.route('/api/manual/reset', methods=['POST'])
def reset_manual():
    """Reset manual simulation"""
    deadlock_detector.reset()
    return jsonify({'status': 'success', 'message': 'Simulation reset'})

@app.route('/api/realtime/processes', methods=['GET'])
def get_realtime_processes():
    """Get real-time Windows processes"""
    processes = process_monitor.get_processes()
    return jsonify({'processes': processes})

@app.route('/api/realtime/detect', methods=['GET'])
def detect_deadlock_realtime():
    """Detect deadlock in real-time mode"""
    result = process_monitor.detect_deadlock()
    
    if result['deadlock_detected']:
        recovery_options = recovery_module.generate_recovery_options(
            result['deadlock_processes'],
            process_monitor.get_detailed_processes(result['deadlock_processes'])
        )
        result['recovery_options'] = recovery_options
    
    return jsonify(result)

@app.route('/api/recovery/execute', methods=['POST'])
def execute_recovery():
    """Execute recovery action"""
    data = request.json
    action = data.get('action')
    process_id = data.get('process_id')
    
    # Handle both string IDs (manual mode) and integer PIDs (real-time mode)
    # Pass deadlock_detector for manual mode to actually update the system
    result = recovery_module.execute_action(action, process_id, deadlock_detector)
    return jsonify(result)

@app.route('/api/system/stats', methods=['GET'])
def get_system_stats():
    """Get system statistics"""
    stats = {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'process_count': len(psutil.pids()),
        'timestamp': datetime.now().isoformat()
    }
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
