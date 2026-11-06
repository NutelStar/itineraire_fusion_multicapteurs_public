import numpy as np
from config.calib_imu_cam import ANGLE, tx, ty, fx, cx, image_taille

def lidar_to_camera(X_lidar, Y_lidar):

    R = np.array([[np.cos(ANGLE), -np.sin(ANGLE)], [np.sin(ANGLE), np.cos(ANGLE)]])

    t = np.array([tx, ty])

    #renvoyer par le lidar
    pts_lidar = np.array([X_lidar, Y_lidar])

    pts_camera = R @ pts_lidar + t
    return pts_camera

#détecttion de la colonne à la quelle le pixel apprtient

def projection_pixel(pts_camera):

    #check si le point y de camera est <= à 0
    if pts_camera[1] <= 0 :
        return None

    u = fx * (pts_camera[0] / pts_camera[1]) + cx

    return u

def is_in_camera_fov(u) :

    if u is None :
        return False

    return 0<= u <= image_taille

def get_roi_from_lidar(pts_min, image_width=640):
    if pts_min is None :
        return None, False


    x_lidar = pts_min[0]
    y_lixar = pts_min[1]

    x_lidar_m = x_lidar / 1000
    y_lidar_m = y_lixar / 1000

    pts_camera = lidar_to_camera(x_lidar_m, y_lidar_m)

    u = projection_pixel(pts_camera)

    in_camera = is_in_camera_fov(u)

    return u, in_camera