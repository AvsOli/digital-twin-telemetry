# HIL Digital Twin & Industrial Telemetry Bridge

A lightweight, containerized Hardware-in-the-Loop (HIL) Digital Twin and telemetry pipeline demonstrating OT/IT convergence. This project simulates an industrial robotic cell, exposes operational metrics via an OPC UA server, streams time-series data through a gateway daemon, and visualizes live telemetry on a Grafana SCADA dashboard.

---

## System Architecture

```text
[Kinematic Simulation Engine] 
             │ (20 Hz Loop)
             ▼
   [Async OPC UA Server] 
   (opc.tcp://localhost:4840)
             │
             ▼
[Gateway Daemon (10 Hz Ingestion)]
             │
             ▼
 [Dockerized InfluxDB v2] <─── [Dockerized Grafana Dashboard]
```

---

## Under-the-Hood Mechanics

The setup consists of three distinct layers handling data generation, industrial transport, and storage/visualization:

### Layer 1: Kinematic & Physical Simulation (`simulation_node.py`)
- **Role:** Software representation of the physical robot arm.
- **Function:** 
  - Simulates a **2-DOF (Two Degrees of Freedom) manipulator**.
  - Updates joint angles ($\theta_1, \theta_2$) using continuous sinusoidal functions.
  - Computes end-effector tip position ($X, Y$) using forward kinematics (trigonometry: $\sin, \cos$).
  - Simulates motor thermal drift (gradual temperature increase due to simulated friction and electrical resistance).

### Layer 2: Asynchronous OPC UA Industrial Server (`opcua_bridge_server.py`)
- **Role:** Universal industrial communication protocol (standard for PLCs and factory SCADA networks).
- **Function:**
  - Organizes variables into a hierarchical tree structure:
    `Root -> Objects -> RoboticCell_1 -> Manipulator_2DOF`
  - Exposes metrics over an asynchronous server using Python's `asyncio` for non-blocking I/O and low-latency dynamic namespace updates.

### Layer 3: Telemetry Pipeline, InfluxDB & Grafana (`opcua_to_influx.py`)
- **Role:** Real-time telemetry ingestion, storage, and visual monitoring.
- **Function:**
  - **Gateway Daemon:** An asynchronous Python daemon polls OPC UA tags at 10 Hz and writes time-series metrics.
  - **InfluxDB v2:** A time-series database running on port `8086`, optimized for high-write, timestamped sensor data.
  - **Grafana:** A web server running on port `3000` that queries InfluxDB via Flux language every 1–2 seconds to render real-time SCADA visualization curves.

---

## Docker Environment

Docker provides environment isolation and simple deployment (`docker compose up -d`) without needing manual system-level software installations on the host OS.

### Programs Running Inside Docker Containers:
1. **InfluxDB Container (`port 8086`):** Database engine storing time-series metrics in persistent volumes.
2. **Grafana Container (`port 3000`):** Web server displaying dashboard UI and executing Flux queries.

### Programs Running Outside Docker (Host OS):
- Python scripts (`opcua_bridge_server.py` and `opcua_to_influx.py`) run directly in host system terminals, communicating with Dockerized services over `localhost`.

---

## Repository Structure

```text
digital-twin-telemetry/
│
├── docker-compose.yaml          # Infrastructure configuration (InfluxDB & Grafana)
├── opcua_bridge_server.py       # Kinematics simulation & Async OPC UA server
├── opcua_to_influx.py           # Ingestion gateway daemon (OPC UA -> InfluxDB)
├── requirements.txt             # Python project dependencies
└── README.md                    # Project documentation
```

---

## Quickstart Guide

### 1. Prerequisites
Ensure you have Docker, Docker Compose, and Python 3.10+ installed.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the Infrastructure (Docker)
Boot up InfluxDB and Grafana using Docker Compose:
```bash
docker compose up -d
```

### 4. Run the OPC UA Server
Start the simulation and industrial protocol server:
```bash
python3 opcua_bridge_server.py
```

### 5. Run the Ingestion Gateway
In a separate terminal, start the collector daemon to stream OPC UA tags into InfluxDB:
```bash
python3 opcua_to_influx.py
```

### 6. Open the Grafana Dashboard
1. Open your browser and navigate to `http://localhost:3000`.
2. Log in (default credentials: `admin` / `admin`).
3. Connect your InfluxDB data source using **Flux**.
4. Import your dashboard panels to visualize joint angles, end-effector coordinates, and motor thermal drift in real time.

---
