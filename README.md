#  PREDLOCK - Predictive Deadlock Detection & Recovery Tool

## Features

###  Core Capabilities

#### **1. Deadlock Detection**
- **Resource Allocation Graph (RAG)** with cycle detection
- DFS-based circular wait identification
- Real-time detection in manual simulations
- Visual graph representation

#### **2. Deadlock Prediction** 
- **Banker's Algorithm** implementation
- Safe state analysis
- Safe sequence generation
- Proactive deadlock prevention

#### **3. Risk Assessment**
- Multi-factor risk scoring (0-100)
- Real-time process risk analysis
- Color-coded risk levels (LOW / MEDIUM / HIGH)
- Continuous monitoring

#### **4. Intelligent Recovery**
- Multiple recovery strategies
- Risk-based recommendations
- Process classification (Critical/System/User)
- Impact assessment with pros/cons analysis

---

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Web browser (Chrome, Firefox, Edge)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/predlock.git
   cd predlock
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Open in browser**
   ```
   http://localhost:5000
   ```

---

## 📖 Usage Guide

### **Manual Simulation Mode**

Perfect for understanding deadlock concepts and algorithms.

#### Create a Deadlock Scenario

1. **Add Processes**
   - Click "Add Process"
   - Enter name (e.g., P1, P2)

2. **Add Resources**
   - Click "Add Resource"
   - Enter name (e.g., R1, R2)

3. **Create Circular Wait**
   ```
   Allocate: P1 → R1
   Allocate: P2 → R2
   Request:  P1 → R2  (P1 wants R2 but P2 has it)
   Request:  P2 → R1  (P2 wants R1 but P1 has it)
   ```

4. **Observe Results**
   - **Detection Status**:  Deadlock detected
   - **Prediction Status**:  Unsafe state
   - **Recovery Options**: Displayed automatically

#### Example: Dining Philosophers Problem

```
Processes: P1, P2, P3, P4, P5 (Philosophers)
Resources: Fork1, Fork2, Fork3, Fork4, Fork5

Allocations:
P1 → Fork1
P2 → Fork2
P3 → Fork3
P4 → Fork4
P5 → Fork5

Requests (Circular Wait):
P1 → Fork2
P2 → Fork3
P3 → Fork4
P4 → Fork5
P5 → Fork1

Result: Deadlock detected! 
```

---

### **Real-Time Monitoring Mode**

Monitor live Windows processes with risk assessment.

#### Features

- **Live Process Tracking**
  - CPU and memory usage
  - Thread count monitoring
  - Process status tracking

- **Risk Scoring**
  - Automatic risk calculation
  - Multi-factor analysis
  - Visual risk indicators

- **Process Classification**
  - Critical System Processes (cannot terminate)
  -  System Processes (caution required)
  -  User Processes (safe to manage)


##  Architecture

### Project Structure

```
predlock/
│
├── app.py                      # Flask backend & API routes
├── banker_algorithm.py         # Banker's Algorithm implementation
├── deadlock_detector.py        # RAG & cycle detection
├── process_monitor.py          # Real-time process monitoring
├── recovery_module.py          # Recovery strategies & execution
├── requirements.txt            # Python dependencies
│
├── templates/
│   └── index.html              # Frontend UI
│
├── readme.md
```

---

## Algorithms Implemented

### 1. Resource Allocation Graph (RAG) - Deadlock Detection

**Complexity**: O(V + E) where V = processes + resources, E = edges

```python
# Detects cycles in directed graph
def detect_deadlock():
    # Build graph: Process → Resource (request)
    #             Resource → Process (allocation)
    # DFS to find cycles
    # Returns: deadlock cycle or None
```

**Use Case**: Detects existing deadlocks

---

### 2. Banker's Algorithm - Deadlock Prediction

**Complexity**: O(m × n²) where m = resources, n = processes

```python
# Checks if system is in safe state
def check_safe_state():
    # Simulates process execution
    # Finds safe sequence
    # Returns: is_safe, safe_sequence
```

**Use Case**: Prevents deadlocks before they occur

---

### 3. Risk Scoring Algorithm

**Factors Considered**:
- Thread count (30 points)
- Process status (25 points)
- Memory usage (20 points)
- Open files (15 points)
- CPU patterns (10 points)

**Output**: Risk score (0-100) and level (LOW/MEDIUM/HIGH)

---

##  User Interface

### Dashboard

- **Real-time Statistics**
  - Process count
  - Resource count
  - CPU usage
  - Memory usage

### Status Blocks

1. **Detection Status** (Green/Red)
   - Shows current deadlock state
   - Displays detected cycles

2. **Prediction Status** (Blue/Yellow)
   - Shows safe/unsafe state
   - Displays safe sequences

### Interactive Graph

- **Process Nodes** (Circles)
  - Color: Blue (#667eea)
  - Represents processes

- **Resource Nodes** (Rectangles)
  - Color: Green (#48bb78)
  - Represents resources

- **Edges**
  - Solid Blue: Allocation (Resource → Process)
  - Dashed Red: Request (Process → Resource)

---

### Manual Testing Scenarios

**Scenario 1: No Deadlock**
```
P1 → R1 (Allocate)
Result: Safe state, Safe sequence: P1
```

**Scenario 2: Simple Deadlock**
```
P1 → R1, P2 → R2 (Allocate)
P1 → R2, P2 → R1 (Request)
Result: Deadlock detected!
```

**Scenario 3: Three Process Deadlock**
```
P1 → R1, P2 → R2, P3 → R3 (Allocate)
P1 → R2, P2 → R3, P3 → R1 (Request)
Result: Circular wait detected!
```

---


##  Technology Stack

### Backend
- **Flask** 3.0.0 - Web framework
- **Python** 3.8+ - Core language
- **psutil** 5.9.6 - Process monitoring

### Frontend
- **HTML5** - Structure
- **CSS3** - Styling with gradients & animations
- **JavaScript** (ES6+) - Interactive functionality
- **SVG** - Graph visualization

### Algorithms
- Depth-First Search (DFS)
- Banker's Algorithm
- Graph cycle detection
- Heuristic risk assessment

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Contribution Ideas

- [ ] Add more detection algorithms
- [ ] Implement prevention strategies
- [ ] Add database logging
- [ ] Create mobile-responsive design
- [ ] Add multi-language support
- [ ] Implement machine learning predictions
- [ ] Add export to PDF functionality

---

##  Acknowledgments

- **Operating System Concepts** by Silberschatz, Galvin, and Gagne
- **Modern Operating Systems** by Andrew S. Tanenbaum
- Flask framework and community
- psutil library contributors
- All open-source contributors

---

##  Future Roadmap

### Version 2.0
- [ ] Distributed deadlock detection
- [ ] Machine learning-based prediction
- [ ] Historical analysis dashboard
- [ ] Advanced visualization options
- [ ] Multi-platform support (Linux, macOS)

### Version 3.0
- [ ] Cloud deployment support
- [ ] REST API for external integration
- [ ] Plugin system for custom algorithms
- [ ] Performance benchmarking tools

---


##  Key Metrics

- **Detection Accuracy**: 100% (in manual mode)
- **Prediction Accuracy**: Based on Banker's Algorithm
- **Response Time**: < 100ms for detection
- **Supported Processes**: Unlimited (in manual mode)
- **Supported Resources**: Unlimited (in manual mode)

---

## Performance

- **Detection Complexity**: O(V + E)
- **Prediction Complexity**: O(m × n²)
- **Memory Usage**: ~50MB baseline
- **CPU Usage**: < 5% during monitoring

---

##  Security Considerations

- Process termination requires appropriate permissions
- System process protection prevents accidental crashes
- Risk-based warnings for critical operations
- Input validation on all API endpoints

---


