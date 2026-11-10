import asyncio
import math
import time
import numpy as np
from asyncua import Server, ua

# Reuse our core kinematic model logic
class SimulatedManipulator:
    def __init__(self, l1=0.5, l2=0.5):
        self.l1 = l1
        self.l2 = l2
        self.q = np.array([0.0, 0.0])
        self.dq = np.array([0.0, 0.0])
        self.torques = np.array([0.0, 0.0])
        self.temperatures = np.array([25.0, 25.0])
        self.time = 0.0

    def step(self, dt=0.05):
        self.time += dt
        target_q1 = 0.5 * math.sin(1.0 * self.time)
        target_q2 = 0.8 * math.cos(0.5 * self.time)
        
        dq1 = (target_q1 - self.q[0]) / dt
        dq2 = (target_q2 - self.q[1]) / dt
        
        self.dq = np.array([dq1, dq2])
        self.q = np.array([target_q1, target_q2])
        
        self.torques = 2.5 * self.dq + 0.5 * np.sin(self.q)
        self.temperatures += (np.abs(self.torques) * 0.005 - 0.001 * (self.temperatures - 25.0)) * dt

    def get_forward_kinematics(self):
        x = self.l1 * math.cos(self.q[0]) + self.l2 * math.cos(self.q[0] + self.q[1])
        y = self.l1 * math.sin(self.q[0]) + self.l2 * math.sin(self.q[0] + self.q[1])
        return x, y


async def main():
    # Initialize OPC UA Server
    server = Server()
    await server.init()
    
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    server.set_server_name("AFlabs Digital Twin Manipulator Server")

    # Setup Namespace
    uri = "http://aflabs.digitaltwin.simulation"
    idx = await server.register_namespace(uri)

    # Build Object Node Structure
    objects = server.nodes.objects
    cell = await objects.add_folder(idx, "RoboticCell_1")
    robot_node = await cell.add_object(idx, "Manipulator_2DOF")

    # Define OPC UA Variables under the Manipulator Object
    joint1_q = await robot_node.add_variable(idx, "Joint1_Angle", 0.0)
    joint2_q = await robot_node.add_variable(idx, "Joint2_Angle", 0.0)
    
    joint1_tau = await robot_node.add_variable(idx, "Joint1_Torque", 0.0)
    joint2_tau = await robot_node.add_variable(idx, "Joint2_Torque", 0.0)
    
    motor1_temp = await robot_node.add_variable(idx, "Motor1_Temperature", 25.0)
    motor2_temp = await robot_node.add_variable(idx, "Motor2_Temperature", 25.0)
    
    ee_x_var = await robot_node.add_variable(idx, "EndEffector_X", 0.0)
    ee_y_var = await robot_node.add_variable(idx, "EndEffector_Y", 0.0)

    # Set Variables as Readable by OPC UA Clients
    nodes_to_write = [
        joint1_q, joint2_q, joint1_tau, joint2_tau, 
        motor1_temp, motor2_temp, ee_x_var, ee_y_var
    ]
    for var in nodes_to_write:
        await var.set_writable(False)  # Telemetry nodes are read-only from client view

    robot = SimulatedManipulator()
    print("OPC UA Server started at opc.tcp://localhost:4840/freeopcua/server/")

    async with server:
        dt = 0.05  # 20 Hz update loop
        while True:
            # 1. Step physical simulation
            robot.step(dt=dt)
            ee_x, ee_y = robot.get_forward_kinematics()

            # 2. Update OPC UA Node values concurrently
            await joint1_q.write_value(float(robot.q[0]))
            await joint2_q.write_value(float(robot.q[1]))
            await joint1_tau.write_value(float(robot.torques[0]))
            await joint2_tau.write_value(float(robot.torques[1]))
            await motor1_temp.write_value(float(robot.temperatures[0]))
            await motor2_temp.write_value(float(robot.temperatures[1]))
            await ee_x_var.write_value(float(ee_x))
            await ee_y_var.write_value(float(ee_y))

            await asyncio.sleep(dt)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOPC UA Server stopped.")