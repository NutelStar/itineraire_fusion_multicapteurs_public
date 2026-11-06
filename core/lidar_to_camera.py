
import math

import numpy as np

from config.calib_camera_lidar import ANGLE, TX, TY

def lidar_to_camera(dist, angle):

    if abs(dist) > 10:
        dist_m = dist / 1000.0
    else:
        dist_m = float(dist)

    angle_rad = math.radians(angle)

    x_lidar = dist_m * math.sin(angle_rad)
    y_lidar = dist_m * math.cos(angle_rad)

    x_cam = math.cos(ANGLE) * x_lidar - math.sin(ANGLE) * y_lidar + TX
    z_cam = math.sin(ANGLE) * x_lidar + math.cos(ANGLE) * y_lidar + TY

    return x_cam, z_cam

def projection_pixel(x_cam, z_cam, fx, cx):
        pixel = fx * (x_cam / z_cam) + cx
        return int(round(pixel))

def angle_to_pixel(angle_deg, image_width, min_angle=-30.0, max_angle=30.0):

    if angle_deg < min_angle:
        angle_deg = min_angle
    if angle_deg > max_angle:
        angle_deg = max_angle

    ratio = (angle_deg - min_angle) / (max_angle - min_angle)
    return int(round(ratio * (image_width - 1)))
