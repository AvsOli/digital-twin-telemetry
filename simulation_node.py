import time
import math
import numpy as np

class SimulatedManipulator:
    def __init__(self, l1=0.5, l2=0.5):
        self.l1 = l1  # Length of link 1 (meters)
        self.l2 = l2  # Length of link 2 (meters)
        
        # State variables
        self.q = np.array([0.0, 0.0])         # Joint angles (rad)
        self.dq = np.array([0.0, 0.0])        # Joint velocities (rad/s)
        self.torques = np.array([0.0, 0.0])   # Simulated torques (Nm)
        self.temperatures = np.array([25.0, 25.0]) # Motor temps (°C)
        
        self.time = 0.0

    def step(self, dt=0.01):
        """Advances simulation state by dt seconds."""
        self.time += dt
        
        # Generate target sinusoidal trajectories for demonstration
        target_q1 = 0.5 * math.sin(1.0 * self.time)
        target_q2 = 0.8 * math.cos(0.5 * self.time)
        
        # Compute joint velocities via finite differences
        dq1 = (target_q1 - self.q[0]) / dt
        dq2 = (target_q2 - self.q[1]) / dt
        
        self.dq = np.array([dq1, dq2])
        self.q = np.array([target_q1, target_q2])
        
        # Simulate physical motor feedback (rough torque estimate & thermal dissipation)
        self.torques = 2.5 * self.dq + 0.5 * np.sin(self.q)
        self.temperatures += (np.abs(self.torques) * 0.005 - 0.001 * (self.temperatures - 25.0)) * dt

    def get_forward_kinematics(self):
        """Computes end-effector (x, y) position."""
        x = self.l1 * math.cos(self.q[0]) + self.l2 * math.cos(self.q[0] + self.q[1])
        y = self.l1 * math.sin(self.q[0]) + self.l2 * math.sin(self.q[0] + self.q[1])
        return x, y

    def get_telemetry_payload(self):
        """Formats current physical state into an OT-ready dictionary."""
        ee_x, ee_y = self.get_forward_kinematics()
        return {
            "timestamp": time.time(),
            "joint_1_angle": round(float(self.q[0]), 4),
            "joint_2_angle": round(float(self.q[1]), 4),
            "joint_1_vel": round(float(self.dq[0]), 4),
            "joint_2_vel": round(float(self.dq[1]), 4),
            "joint_1_torque": round(float(self.torques[0]), 4),
            "joint_2_torque": round(float(self.torques[1]), 4),
            "motor_1_temp": round(float(self.temperatures[0]), 2),
            "motor_2_temp": round(float(self.temperatures[2] if len(self.temperatures) > 2 else self.temperatures[1]), 2),
            "ee_pos_x": round(ee_x, 4),
            "ee_pos_y": round(ee_y, 4)
        }

if __name__ == "__main__":
    robot = SimulatedManipulator()
    print("Starting Kinematic Simulation Loop (Press Ctrl+C to stop)...")
    try:
        while True:
            robot.step(dt=0.05)
            state = robot.get_telemetry_payload()
            print(f"Time: {robot.time:.2f}s | Q: [{state['joint_1_angle']}, {state['joint_2_angle']}] | EE Pos: ({state['ee_pos_x']}, {state['ee_pos_y']})")
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nSimulation stopped.")