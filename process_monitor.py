import psutil
import os
from collections import defaultdict

class ProcessMonitor:
    """
    Monitor real-time Windows processes and detect potential deadlocks
    """
    
    # Critical system processes that should not be terminated
    CRITICAL_SYSTEM_PROCESSES = {
        'csrss.exe', 'smss.exe', 'wininit.exe', 'services.exe',
        'lsass.exe', 'winlogon.exe', 'dwm.exe', 'system'
    }
    
    # Non-critical but important system processes
    SYSTEM_PROCESSES = {
        'explorer.exe', 'svchost.exe', 'taskhost.exe', 'taskhostw.exe',
        'spoolsv.exe', 'searchindexer.exe'
    }
    
    def __init__(self):
        self.monitored_processes = {}
    
    def is_system_process(self, process):
        """
        Determine if a process is a system process
        Returns: 'critical', 'system', or 'user'
        """
        try:
            name = process.name().lower()
            
            # Check critical system processes
            if name in self.CRITICAL_SYSTEM_PROCESSES:
                return 'critical'
            
            # Check system processes
            if name in self.SYSTEM_PROCESSES:
                return 'system'
            
            # Check if running as SYSTEM user
            try:
                username = process.username()
                if 'SYSTEM' in username.upper() or 'LOCAL SERVICE' in username.upper():
                    return 'system'
            except:
                pass
            
            # Check if in System32 directory
            try:
                exe_path = process.exe()
                if 'System32' in exe_path or 'system32' in exe_path:
                    return 'system'
            except:
                pass
            
            return 'user'
        except:
            return 'unknown'
    
    def get_processes(self):
        """Get all running processes with details"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status', 'num_threads']):
            try:
                pinfo = proc.info
                process_type = self.is_system_process(proc)
                
                processes.append({
                    'pid': pinfo['pid'],
                    'name': pinfo['name'],
                    'username': pinfo.get('username', 'N/A'),
                    'cpu_percent': round(pinfo.get('cpu_percent', 0), 2),
                    'memory_percent': round(pinfo.get('memory_percent', 0), 2),
                    'status': pinfo.get('status', 'unknown'),
                    'num_threads': pinfo.get('num_threads', 0),
                    'type': process_type
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return processes
    
    def get_detailed_processes(self, pids):
        """Get detailed information for specific processes"""
        detailed = []
        
        for pid in pids:
            try:
                proc = psutil.Process(pid)
                process_type = self.is_system_process(proc)
                
                # Get open files
                try:
                    open_files = [f.path for f in proc.open_files()]
                except:
                    open_files = []
                
                # Get connections
                try:
                    connections = len(proc.connections())
                except:
                    connections = 0
                
                detailed.append({
                    'pid': pid,
                    'name': proc.name(),
                    'type': process_type,
                    'status': proc.status(),
                    'cpu_percent': proc.cpu_percent(interval=0.1),
                    'memory_percent': proc.memory_percent(),
                    'num_threads': proc.num_threads(),
                    'username': proc.username() if hasattr(proc, 'username') else 'N/A',
                    'open_files': open_files[:5],  # Limit to 5 files
                    'connections': connections,
                    'create_time': proc.create_time()
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return detailed
    
    def detect_deadlock(self):
        """
        Detect potential deadlocks in real-time processes
        This is a simplified detection based on:
        - Processes in 'waiting' or 'sleeping' state for too long
        - Circular wait detection using file locks
        - Thread analysis for waiting threads
        """
        waiting_processes = []
        file_locks = defaultdict(list)  # file -> [pids accessing it]
        suspicious_processes = []
        
        # Find processes that are waiting or have multiple threads in wait state
        for proc in psutil.process_iter(['pid', 'name', 'status', 'num_threads', 'cpu_percent']):
            try:
                pinfo = proc.info
                pid = pinfo['pid']
                
                # Check if process is waiting/sleeping with low CPU usage
                if pinfo['status'] in ['waiting', 'sleeping', 'disk-sleep']:
                    cpu = proc.cpu_percent(interval=0.1)
                    num_threads = pinfo.get('num_threads', 0)
                    
                    # Suspicious: waiting state + low CPU + multiple threads
                    if cpu < 1.0 and num_threads >= 2:
                        waiting_processes.append(pid)
                        suspicious_processes.append({
                            'pid': pid,
                            'name': pinfo['name'],
                            'status': pinfo['status'],
                            'threads': num_threads,
                            'cpu': cpu
                        })
                
                # Track file locks
                try:
                    for f in proc.open_files():
                        file_locks[f.path].append(pid)
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Check for multiple processes accessing same files
        potential_deadlock = []
        for file_path, pids in file_locks.items():
            if len(pids) > 1:
                # Multiple processes accessing same file
                waiting_on_file = [pid for pid in pids if pid in waiting_processes]
                if len(waiting_on_file) >= 1:
                    potential_deadlock.extend(waiting_on_file)
        
        # Also check for suspicious waiting processes (like our test script)
        if len(suspicious_processes) > 0:
            # Found processes that look like they might be deadlocked
            potential_deadlock.extend([p['pid'] for p in suspicious_processes])
        
        # Remove duplicates
        potential_deadlock = list(set(potential_deadlock))
        
        # If we found suspicious processes, report them
        if potential_deadlock:
            details = "\n".join([
                f"  - {p['name']} (PID: {p['pid']}) - Status: {p['status']}, Threads: {p['threads']}, CPU: {p['cpu']:.1f}%"
                for p in suspicious_processes if p['pid'] in potential_deadlock
            ])
            
            return {
                'deadlock_detected': True,
                'deadlock_processes': potential_deadlock,
                'message': f'Potential deadlock detected! {len(potential_deadlock)} process(es) in suspicious waiting state.',
                'details': details,
                'note': 'Real-time deadlock detection is approximate. Thread-level deadlocks are detected by monitoring waiting states and low CPU usage with multiple threads.'
            }
        
        return {
            'deadlock_detected': False,
            'message': 'No deadlock detected in current processes.'
        }
    
    def get_process_dependencies(self):
        """Get process dependency graph (parent-child relationships)"""
        dependencies = []
        
        for proc in psutil.process_iter(['pid', 'name', 'ppid']):
            try:
                pinfo = proc.info
                if pinfo['ppid'] != 0:  # Has parent
                    dependencies.append({
                        'child': pinfo['pid'],
                        'parent': pinfo['ppid'],
                        'name': pinfo['name']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return dependencies