To re-launch the application:
1. docker compose up -d
2. python3 opcua_bridge_server.py
3. python3 opcua_to_influx.py
4. open "http://localhost:3000" in browser (user:admin, pass:admin)

To shutdown the application:
1. Cancel/Close both python scripts (CTRL + C)
2. Shutdown the docker with: "docker compose stop"


digital-twin-telemetry/
│
├── docker-compose.yaml          # Brings up InfluxDB & Grafana
├── simulation_node.py           # Physics & kinematics simulation
├── opcua_bridge_server.py       # Asynchronous OPC UA server
├── opcua_to_influx.py           # Ingestion gateway daemon
├── requirements.txt             # Python dependencies (asyncua, influxdb-client, etc.)
└── README.md                    # Documentation & setup guide
