#!/usr/bin/env python3
import rospy
import cv2
import numpy as np
from cv_bridge import CvBridge, CvBridgeError
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image
from move_robot import MoveTurtlebot3

#creating a discretized pid controller
kp = 0.4
ki = 0.0
kd = 0.3
k11 = kp + ki + kd
k21 = -kp - 2*kd
k31 = kd
e11,e21,e31 = 0,0,0
u = 0

class LineFollower(object):

    def __init__(self, pub):
        self.bridge_object = CvBridge()
        self.pub = pub
        self.image_sub = rospy.Subscriber("/camera/image",Image,self.camera_callback)
        #self.moveTurtlebot3_object = MoveTurtlebot3()

    def camera_callback(self, data):
        global e11, e21, e31, u, k11, k21, k31
        # We select bgr8 because its the OpneCV encoding by default
        cv_image = self.bridge_object.imgmsg_to_cv2(data, desired_encoding="bgr8")

        # We get image dimensions and crop the parts of the image we dont need
        height, width, channels = cv_image.shape
        crop_img = cv_image[int((height/2)+100):int((height/2)+120)][1:int(width)]
        #crop_img = cv_image[340:360][1:640]

        # Convert from RGB to HSV
        hsv = cv2.cvtColor(crop_img, cv2.COLOR_BGR2HSV)

        # Define the Yellow Colour in HSV

        """
        To know which color to track in HSV use ColorZilla to get the color registered by the camera in BGR and convert to HSV. 
        """

        # Threshold the HSV image to get only yellow colors
        sensitivity = 15
        lower_yellow = np.array([20,100,100])
        upper_yellow = np.array([50,255,255])
        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

        # Calculate centroid of the blob of binary image using ImageMoments
        m = cv2.moments(mask, False)

        try:
            cx, cy = m['m10']/m['m00'], m['m01']/m['m00']
        except ZeroDivisionError:
            cx, cy = height/2, width/2
        
        # Draw the centroid in the resultut image
        # cv2.circle(img, center, radius, color[, thickness[, lineType[, shift]]]) 
        cv2.circle(mask,(int(cx), int(cy)), 10,(0,0,255),-1)
        cv2.imshow("Original", cv_image)
        cv2.imshow("MASK", mask)
        cv2.waitKey(1)

        #################################
        ###   ENTER CONTROLLER HERE   ###
        #################################

        '''twist_object = Twist()

        #computing error
        err = cx - height/2
        rospy.loginfo("Error is===>"+str(err))

        e31 = e21
        e21 = e11
        e11 = err
        u = u + k11*e11 + k21*e21 + k31*e31

        twist_object.angular.z = -u/100
        twist_object.linear.x = 0.2

        #rospy.loginfo("ANGULAR VALUE SENT===>"+str(twist_object.angular.z))
        # Make it start turning
        #self.moveTurtlebot3_object.move_robot(twist_object)
        self.pub.publish(twist_object)'''
        pub_= rospy.Publisher('/cmd_vel', Twist, queue_size=1)
        msg=Twist()
        k = 0.001/1.5
        angular_z = -k*(cx-width/2)
        linear_x = 0.1 

        thresh = 1.5
        if angular_z > thresh:
            angular_z = thresh
        elif angular_z < -thresh:
            angular_z = -thresh
        print("Errors:")
        print([cx,cy,width/2,height/2])
        print("Controls")
        print([angular_z,linear_x])
        msg.linear.x = linear_x
        msg.angular.z = angular_z
        #rospy.loginfo("ANGULAR VALUE SENT===>"+str(twist_object.angular.z))
        pub_.publish(msg)

    def clean_up(self):
        #self.moveTurtlebot3_object.clean_class()
        cv2.destroyAllWindows()

def main():
    rospy.init_node('line_following_node', anonymous=True)
    pub = rospy.Publisher("/cmd_vel", Twist, queue_size=10)
    line_follower_object = LineFollower(pub)
    rate = rospy.Rate(5)
    ctrl_c = False
    def shutdownhook():
        # Works better than rospy.is_shutdown()
        line_follower_object.clean_up()
        rospy.loginfo("Shutdown time!")
        ctrl_c = True
    rospy.on_shutdown(shutdownhook)
    while not ctrl_c:
        rate.sleep()

if __name__ == '__main__':
        main()
