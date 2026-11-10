import asyncio
import sys
from asyncua import Client
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Configuration Parameters (Matching docker-compose setup)
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "aflabs_super_secret_token_123"
INFLUX_ORG = "AFlabs"
INFLUX_BUCKET = "telemetry"

OPC_URL = "opc.tcp://localhost:4840/freeopcua/server/"

async def main():
    print(f"Connecting to OPC UA Server at {OPC_URL}...")
    
    # Initialize InfluxDB Client
    influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    write_api = influx_client.write_api(write_options=SYNCHRONOUS)

    async with Client(url=OPC_URL) as opc_client:
        objects = opc_client.nodes.objects
        
        # Look up namespace index for custom nodes
        idx = await opc_client.get_namespace_index("http://aflabs.digitaltwin.simulation")
        
        # Locate target OPC UA variable nodes
        j1_angle_node = await objects.get_child([f"{idx}:RoboticCell_1", f"{idx}:Manipulator_2DOF", f"{idx}:Joint1_Angle"])
        j2_angle_node = await objects.get_child([f"{idx}:RoboticCell_1", f"{idx}:Manipulator_2DOF", f"{idx}:Joint2_Angle"])
        m1_temp_node  = await objects.get_child([f"{idx}:RoboticCell_1", f"{idx}:Manipulator_2DOF", f"{idx}:Motor1_Temperature"])
        m2_temp_node  = await objects.get_child([f"{idx}:RoboticCell_1", f"{idx}:Manipulator_2DOF", f"{idx}:Motor2_Temperature"])
        ee_x_node     = await objects.get_child([f"{idx}:RoboticCell_1", f"{idx}:Manipulator_2DOF", f"{idx}:EndEffector_X"])
        ee_y_node     = await objects.get_child([f"{idx}:RoboticCell_1", f"{idx}:Manipulator_2DOF", f"{idx}:EndEffector_Y"])

        print("Gateway connected successfully! Streaming OPC UA data to InfluxDB (10 Hz)...")

        while True:
            # Fetch all variable values concurrently
            j1, j2, t1, t2, x, y = await asyncio.gather(
                j1_angle_node.read_value(),
                j2_angle_node.read_value(),
                m1_temp_node.read_value(),
                m2_temp_node.read_value(),
                ee_x_node.read_value(),
                ee_y_node.read_value()
            )

            # Build time-series data point
            point = Point("manipulator_state") \
                .tag("cell_id", "Cell_1") \
                .tag("device", "Manipulator_2DOF") \
                .field("joint_1_angle", float(j1)) \
                .field("joint_2_angle", float(j2)) \
                .field("motor_1_temp", float(t1)) \
                .field("motor_2_temp", float(t2)) \
                .field("ee_x", float(x)) \
                .field("ee_y", float(y))

            # Write to InfluxDB bucket
            write_api.write(bucket=INFLUX_BUCKET, record=point)
            
            await asyncio.sleep(0.1)  # Ingestion rate of 10 Hz

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGateway stopped.")
    except Exception as e:
        print(f"\n[ERROR] Gateway execution failed: {e}")