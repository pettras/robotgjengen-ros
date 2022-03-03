#Node that has to subscribe to /gripper_status, /robot_status, /CV_image topics and
# publishes to /robot_pos and /gripper_pos after calling tha policy.

from argparse import Action
from turtle import position
import rclpy
from rclpy.node import Node

from master_interfaces.msg import GripperStatus   
from master_interfaces.msg import GripperPos    
from master_interfaces.msg import RobotStatus    
from master_interfaces.msg import RobotPos   

import numpy as np
import time
from stable_baselines3 import PPO

def conv_between_0_and_7(num):
    if num < 8:
        return num
    else:
        return num - int(num/8)*8

def dummyPPO(obs):
    obs = conv_between_0_and_7(obs)
    action = np.zeros(8)
    action[obs] = 1
    return action

class PublishingSubscriber(Node):

    def __init__(self):
        super().__init__('policy_node')                 #node name
        self.subscription = self.create_subscription(
            GripperStatus,                              #interface name from master_interfaces.msg
            'gripper_status',                           #topic name
            self.gripper_listener_callback,             #callback function
            1)                                          #queue size
        
        self.subscription2 = self.create_subscription(
            RobotStatus,
            'robot_status',
            self.robot_listener_callback,
            1)
        
        self.subscription  # prevent unused variable warning
        self.subscription2

        # Set up publisher to gripper and robot pos
        self.publisher_ = self.create_publisher(GripperPos, 'gripper_pos', 1)
        self.publisher2 = self.create_publisher(RobotPos, 'robot_pos',1)
        timer_period = 2  # seconds
        self.timer = self.create_timer(
            timer_period, 
            self.talker_callback) #sends gripper pos accorting to timer
        self.i = 0

        np.set_printoptions(formatter={'float': lambda x: "{0:0.2f}".format(x)})
        self.current_status = np.empty(15, np.float)

    def gripper_listener_callback(self, msg): #gripper_callback
        self.current_status[14] = float(msg.status)
        #print(self.current_status)
        #self.get_logger().info('I heard: "%s"' % msg)


    def robot_listener_callback(self, msg): #full_callback
        msg_vector = np.array([msg.joint1, msg.joint2, msg.joint3, msg.joint4, msg.joint5,
        msg.joint6, msg.joint7, msg.x, msg.y, msg.z, msg.a, msg.b, msg.c, float(msg.running)])
        self.current_status[:14] = msg_vector
        print("current_status",self.current_status)
        print("\n")

            
    def talker_callback(self): # Member function that makes the gripper_status information
        #model=PPO.load("...zip")
        #chosen_action = model.predict(obs)
        chosen_action = dummyPPO(self.i)

        msg = GripperPos()
        msg.pos = int(chosen_action[7])
        
        msg2 = RobotPos()
        msg2.joint1 = chosen_action[0]
        msg2.joint2 = chosen_action[1]
        msg2.joint3 = chosen_action[2]
        msg2.joint4 = chosen_action[3]
        msg2.joint5 = chosen_action[4]
        msg2.joint6 = chosen_action[5]
        msg2.joint7 = chosen_action[6]

        self.publisher_.publish(msg)
        self.publisher2.publish(msg2)
        
        print(msg, "\n", msg2)
        #self.get_logger().info('Publishing: "%s"' % msg.pos)
        self.i += 1

    



def main(args=None):

    rclpy.init(args=args)

    publisher_and_subscriber = PublishingSubscriber()

    rclpy.spin(publisher_and_subscriber)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    publisher_and_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
