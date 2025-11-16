"""
Detectable Deadlock Test - Optimized for Predlock Detection
This script creates a deadlock that's easier to detect in real-time monitoring
"""

import threading
import time
import os
import sys

# Set process name to make it easier to find
import setproctitle
try:
    setproctitle.setproctitle("PREDLOCK_DEADLOCK_TEST")
except:
    pass  # setproctitle not available on all systems

lock1 = threading.Lock()
lock2 = threading.Lock()

print("\n" + "="*70)
print(" " * 20 + "DETECTABLE DEADLOCK TEST")
print("="*70)
print(f"  Process PID: {os.getpid()}")
print(f"  Process Name: {os.path.basename(sys.argv[0])}")
print()
print("  This script creates a deadlock optimized for detection.")
print("  It will have:")
print("    - 2+ threads")
print("    - Waiting/sleeping status")
print("    - Low CPU usage")
print("    - Circular wait condition")
print()
print("  Monitor in Predlock Real-Time Mode!")
print("="*70)
print()

# Counter to keep threads busy initially
counter = 0

def thread1_deadlock():
    """Thread 1: Busy work, then deadlock"""
    global counter
    thread_name = threading.current_thread().name
    
    # Do some initial work to show activity
    print(f"[{thread_name}] Starting initial work...")
    for i in range(5):
        counter += 1
        time.sleep(0.2)
    
    print(f"[{thread_name}] Acquiring LOCK-1...")
    lock1.acquire()
    print(f"[{thread_name}] ✓ Got LOCK-1")
    
    # Small delay to ensure both threads get their first lock
    time.sleep(1)
    
    print(f"[{thread_name}] Now waiting for LOCK-2... 🔒")
    lock2.acquire()  # Will wait forever - DEADLOCK!
    
    # Never reaches here
    print(f"[{thread_name}] Got both locks!")
    lock1.release()
    lock2.release()

def thread2_deadlock():
    """Thread 2: Busy work, then deadlock"""
    global counter
    thread_name = threading.current_thread().name
    
    # Do some initial work
    print(f"[{thread_name}] Starting initial work...")
    for i in range(5):
        counter += 1
        time.sleep(0.2)
    
    print(f"[{thread_name}] Acquiring LOCK-2...")
    lock2.acquire()
    print(f"[{thread_name}] ✓ Got LOCK-2")
    
    # Small delay
    time.sleep(1)
    
    print(f"[{thread_name}] Now waiting for LOCK-1... 🔒")
    lock1.acquire()  # Will wait forever - DEADLOCK!
    
    # Never reaches here
    print(f"[{thread_name}] Got both locks!")
    lock2.release()
    lock1.release()

def monitor_thread():
    """Thread to keep process active and reportable"""
    global counter
    time.sleep(3)
    
    print("\n" + "="*70)
    print(" " * 25 + "⚠️  DEADLOCK STATUS ⚠️")
    print("="*70)
    print(f"  Process PID: {os.getpid()}")
    print(f"  Status: DEADLOCKED")
    print(f"  Active Threads: {threading.active_count()}")
    print()
    print("  Deadlock Cycle:")
    print("    Thread-1: Holds LOCK-1 → Waiting for LOCK-2")
    print("    Thread-2: Holds LOCK-2 → Waiting for LOCK-1")
    print()
    print("  Detection Indicators:")
    print("    ✓ Multiple threads (3)")
    print("    ✓ Low CPU usage (~0%)")
    print("    ✓ Waiting/Sleeping status")
    print("    ✓ Threads blocked on locks")
    print()
    print("  CHECK PREDLOCK NOW:")
    print(f"    1. Go to Real-Time Monitoring")
    print(f"    2. Refresh Processes")
    print(f"    3. Find PID: {os.getpid()}")
    print(f"    4. Look for 'python.exe' or '{os.path.basename(sys.argv[0])}'")
    print(f"    5. Status should detect potential deadlock")
    print("="*70)
    print()
    
    # Keep updating status
    while True:
        time.sleep(5)
        print(f"  [Monitor] Still deadlocked... PID: {os.getpid()}, Threads: {threading.active_count()}")

# Create threads
print("Creating threads...")
t1 = threading.Thread(target=thread1_deadlock, name="DeadlockThread-1", daemon=False)
t2 = threading.Thread(target=thread2_deadlock, name="DeadlockThread-2", daemon=False)
monitor = threading.Thread(target=monitor_thread, name="MonitorThread", daemon=False)

print("Starting threads...")
t1.start()
t2.start()
monitor.start()

# Main thread keeps process alive
print("\nMain thread running... Press Ctrl+C to exit\n")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\nExiting... (Threads will be forcefully terminated)")
    print("Deadlock was never resolved - this is expected!")
    sys.exit(0)
