import psutil
import signal
import os

class RecoveryModule:
    """
    Handles deadlock recovery with user decision support
    Provides multiple recovery strategies with risk assessment
    """
    
    def generate_recovery_options(self, deadlock_cycle, processes):
        """
        Generate recovery options for detected deadlock
        
        Args:
            deadlock_cycle: List of process IDs in deadlock
            processes: List of process dictionaries with details
        
        Returns:
            List of recovery options with risk assessment
        """
        options = []
        
        # Filter only process nodes from the cycle (exclude resource nodes)
        process_ids_in_cycle = [node for node in deadlock_cycle if isinstance(node, str) and node.startswith('P')]
        
        for process in processes:
            # Skip if this process is not in the deadlock cycle
            pid = process.get('pid') or process.get('id')
            if str(pid) not in process_ids_in_cycle:
                continue
            
            name = process.get('name', 'Unknown')
            process_type = process.get('type', 'user')
            
            # Calculate risk and impact
            risk_level, risk_description = self._assess_risk(process_type)
            impact_score = self._calculate_impact(process)
            
            # Option 1: Terminate Process
            options.append({
                'action': 'terminate',
                'process_id': str(pid),
                'process_name': name,
                'process_type': process_type,
                'risk_level': risk_level,
                'risk_description': risk_description,
                'impact_score': impact_score,
                'recommendation': self._get_recommendation(process_type, impact_score),
                'description': f'Terminate {name} (ID: {pid})',
                'pros': self._get_pros('terminate', process_type),
                'cons': self._get_cons('terminate', process_type)
            })
            
            # Option 2: Suspend Process (if not critical)
            if process_type != 'critical':
                options.append({
                    'action': 'suspend',
                    'process_id': str(pid),
                    'process_name': name,
                    'process_type': process_type,
                    'risk_level': 'low',
                    'risk_description': 'Temporarily suspend process',
                    'impact_score': impact_score * 0.5,
                    'recommendation': 'Safe alternative to termination',
                    'description': f'Suspend {name} (ID: {pid})',
                    'pros': ['Reversible', 'No data loss', 'Can resume later'],
                    'cons': ['Process remains in memory', 'May not fully resolve deadlock']
                })
        
        # Sort by impact score (lower is better)
        options.sort(key=lambda x: x['impact_score'])
        
        # Mark recommended option
        if options:
            options[0]['is_recommended'] = True
        
        return options
    
    def _assess_risk(self, process_type):
        """Assess risk level of terminating a process"""
        if process_type == 'critical':
            return 'critical', '⚠️ CRITICAL: Terminating this process may cause system crash or instability!'
        elif process_type == 'system':
            return 'high', '⚠️ WARNING: This is a system process. Termination may affect system functionality.'
        else:
            return 'low', '✓ Safe: User process, minimal system impact.'
    
    def _calculate_impact(self, process):
        """Calculate impact score (0-100, lower is better)"""
        impact = 0
        
        process_type = process.get('type', 'user')
        
        # Type impact
        if process_type == 'critical':
            impact += 100
        elif process_type == 'system':
            impact += 50
        else:
            impact += 10
        
        # Memory usage impact
        memory_percent = process.get('memory_percent', 0)
        impact += memory_percent * 0.5
        
        # CPU usage impact
        cpu_percent = process.get('cpu_percent', 0)
        impact += cpu_percent * 0.3
        
        # Thread count impact (more threads = more impact)
        num_threads = process.get('num_threads', 0)
        impact += num_threads * 0.5
        
        return round(impact, 2)
    
    def _get_recommendation(self, process_type, impact_score):
        """Get recommendation text"""
        if process_type == 'critical':
            return '🚫 NOT RECOMMENDED: Do not terminate critical system processes!'
        elif process_type == 'system':
            return '⚠️ Use with caution: Try other options first'
        elif impact_score < 20:
            return '✓ RECOMMENDED: Minimal impact, safe to terminate'
        else:
            return '✓ Safe: Can be terminated if necessary'
    
    def _get_pros(self, action, process_type):
        """Get pros for an action"""
        if action == 'terminate':
            if process_type == 'user':
                return [
                    'Immediately breaks deadlock',
                    'Frees up resources',
                    'Simple and effective'
                ]
            else:
                return [
                    'Breaks deadlock',
                    'Frees system resources'
                ]
        return []
    
    def _get_cons(self, action, process_type):
        """Get cons for an action"""
        if action == 'terminate':
            cons = ['Unsaved work may be lost']
            if process_type == 'system':
                cons.append('May affect system stability')
                cons.append('Dependent processes may fail')
            elif process_type == 'critical':
                cons.append('⚠️ SYSTEM CRASH RISK')
                cons.append('⚠️ May corrupt system files')
            return cons
        return []
    
    def execute_action(self, action, process_id, deadlock_detector=None):
        """
        Execute recovery action
        
        Args:
            action: 'terminate' or 'suspend'
            process_id: Process ID to act upon (can be string like 'P1' or integer PID)
            deadlock_detector: Reference to deadlock detector for manual mode
        
        Returns:
            Result dictionary with success status
        """
        # Check if it's a manual mode process (string ID like 'P1')
        if isinstance(process_id, str) or (isinstance(process_id, int) and process_id < 100):
            # Manual mode - simulate the action and update the system
            if deadlock_detector:
                # Actually remove the process from the system
                success = deadlock_detector.remove_process(str(process_id))
                if success:
                    return {
                        'success': True,
                        'message': f'Process {process_id} removed from system. Deadlock resolved!',
                        'action': action,
                        'note': 'Process removed from simulation. System state updated.'
                    }
                else:
                    return {
                        'success': False,
                        'message': f'Failed to remove process {process_id}.',
                        'action': action
                    }
            else:
                # Fallback: just simulate
                return {
                    'success': True,
                    'message': f'Simulated {action} for process {process_id}.',
                    'action': action,
                    'note': 'This is a simulation. No actual process was terminated.'
                }
        
        # Real-time mode - actually terminate/suspend the process
        try:
            process = psutil.Process(int(process_id))
            process_name = process.name()
            
            if action == 'terminate':
                # Terminate process
                process.terminate()
                
                # Wait for process to terminate
                try:
                    process.wait(timeout=5)
                except psutil.TimeoutExpired:
                    # Force kill if not terminated
                    process.kill()
                
                return {
                    'success': True,
                    'message': f'Process {process_name} (PID: {process_id}) terminated successfully',
                    'action': 'terminate'
                }
            
            elif action == 'suspend':
                # Suspend process (POSIX only, limited Windows support)
                if os.name == 'posix':
                    process.suspend()
                    return {
                        'success': True,
                        'message': f'Process {process_name} (PID: {process_id}) suspended',
                        'action': 'suspend'
                    }
                else:
                    return {
                        'success': False,
                        'message': 'Suspend not fully supported on Windows. Use terminate instead.',
                        'action': 'suspend'
                    }
            
            elif action == 'resume':
                # Resume suspended process
                if os.name == 'posix':
                    process.resume()
                    return {
                        'success': True,
                        'message': f'Process {process_name} (PID: {process_id}) resumed',
                        'action': 'resume'
                    }
                else:
                    return {
                        'success': False,
                        'message': 'Resume not fully supported on Windows.',
                        'action': 'resume'
                    }
            
            return {
                'success': False,
                'message': f'Unknown action: {action}',
                'action': action
            }
        
        except psutil.NoSuchProcess:
            return {
                'success': False,
                'message': f'Process {process_id} not found',
                'action': action
            }
        except psutil.AccessDenied:
            return {
                'success': False,
                'message': f'Access denied. Cannot {action} process {process_id}. Try running as administrator.',
                'action': action
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'action': action
            }
