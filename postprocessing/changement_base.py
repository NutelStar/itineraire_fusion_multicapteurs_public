"""
Chargement des librairies
"""

RAYON_TERRE = 6378137.0

import numpy as np
import os
from scipy.spatial.transform import Rotation as R

#%%
def load_oxts(filepath):
    data = np.loadtxt(filepath)

    return {
        "lat": data[0],
        "lon": data[1],
        "alt": data[2],
        "roll": data[3],
        "pitch": data[4],
        "yaw": data[5],
    }

def gps_to_cartesian(latitude, longitude, altitude, latitude0):
    """
    Convertit les coordonnées GPS en coordonnées cartésiennes en utilisant la projection plane de Mercator.
    """
    lat_rad = np.radians(latitude)
    lon_rad = np.radians(longitude)
    scale = np.cos(np.radians(latitude0))
    
    x = RAYON_TERRE * lon_rad * scale
    y = RAYON_TERRE * np.log(np.tan(np.pi/4 + lat_rad/2)) * scale
    z = 0 # On reset l'altitude à 0 pour ne pas la gérer étant donné qu'on est sur une carte 2D
    
    return np.array([x, y, z])

def cartesian_to_gps(x, y, z, origine_latitude, origine_longitude, origine_altitude):
    """
    Convertit des coordonnées cartésiennes locales (X=Est/Ouest, Y=Nord/Sud) en coordonnées GPS.
    Méthode des approximations locales (Equirectangular / ENU), parfaite pour un repère local (0,0).
    """
    lat0_rad = np.radians(origine_latitude)
    
    # Nombre de mètres par degré pour la latitude (Nord-Sud)
    metres_par_degre_lat = (np.pi * RAYON_TERRE) / 180.0
    
    # Nombre de mètres par degré pour la longitude (Est-Ouest), dépend de la latitude
    metres_par_degre_lon = metres_par_degre_lat * np.cos(lat0_rad)
    
    # Conversion directe des mètres en delta de degrés
    delta_latitude = y / metres_par_degre_lat
    delta_longitude = x / metres_par_degre_lon
    
    # Calcul des coordonnées finales
    latitude = origine_latitude + delta_latitude
    longitude = origine_longitude + delta_longitude
    altitude = origine_altitude + z
    
    return latitude, longitude, altitude

def matrice_rotation(roll, pitch, yaw):
    """
    Crée une matrice de rotation 3x3 à l'aide des angles roll, pitch et yaw.
    """

    cos_roll, sin_roll = np.cos(roll),  np.sin(roll)    # cos(phi),   sin(phi)
    cos_pitch, sin_pitch = np.cos(pitch), np.sin(pitch)   # cos(theta), sin(theta)
    cos_yaw, sin_yaw = np.cos(yaw),   np.sin(yaw)     # cos(psi),   sin(psi)
    
    rotation_mat = np.array([
        [cos_yaw*cos_pitch,  cos_yaw*sin_pitch*sin_roll - sin_yaw*cos_roll,  cos_yaw*sin_pitch*cos_roll + sin_yaw*sin_roll],
        [sin_yaw*cos_pitch,  sin_yaw*sin_pitch*sin_roll + cos_yaw*cos_roll,  sin_yaw*sin_pitch*cos_roll - cos_yaw*sin_roll],
        [-sin_pitch,         cos_pitch*sin_roll,                             cos_pitch*cos_roll]
    ])
    
    return rotation_mat

def redresser_axes_imu(data_imu):
    """
    Bascule les données brutes de l'IMU (X=Haut, Y=Droite, Z=Arrière) 
    vers le repère standard (X=Avant, Y=Droite, Z=Bas).
    """
    P = np.array([
        [0,  0,  1],  # X_imu (Avant)
        [0,  1,   0],  # Y_imu (Droite)
        [-1,  0,   0]   # Z_imu (Bas)
    ])

    for i in range(len(data_imu)):
        acc_raw = np.array([data_imu[i]["accel_x"], data_imu[i]["accel_y"], data_imu[i]["accel_z"]])
        gyro_raw = np.array([data_imu[i]["gyro_x"], data_imu[i]["gyro_y"], data_imu[i]["gyro_z"]])
        mag_raw = np.array([data_imu[i]["magneto_x"], data_imu[i]["magneto_y"], data_imu[i]["magneto_z"]])

        data_imu[i]["accel_x"], data_imu[i]["accel_y"], data_imu[i]["accel_z"] = P @ acc_raw
        data_imu[i]["gyro_x"],  data_imu[i]["gyro_y"],  data_imu[i]["gyro_z"]  = P @ gyro_raw
        data_imu[i]["magneto_x"], data_imu[i]["magneto_y"], data_imu[i]["magneto_z"] = P @ mag_raw

    return data_imu

def changement_de_base(data_gps, data_imu, gps_out = "cartesian"):
    """
    Transforme le GPS en coordonnées locales et projette l'accélération dans le monde.
    """

    # 1) Passage dans un repère local
    latitude0 = data_gps[0]["latitude"]
    longitude0 = data_gps[0]["longitude"]
    altitude0 = data_gps[0]["altitude"]
    origine = gps_to_cartesian(latitude0, longitude0, altitude0, latitude0)

    for i in range(len(data_gps)):
        scan = gps_to_cartesian(data_gps[i]["latitude"], data_gps[i]["longitude"], data_gps[i]["altitude"], latitude0)
        scan_local = scan - origine
        data_gps[i]["longitude"], data_gps[i]["latitude"], data_gps[i]["altitude"] = scan_local
        
    """
    # 2) Projection des accélérations du repère imu vers le repère carte
    # DEPRECIEE: nous utilisons désormais Kalman afin de changer le repère de l'IMU dans le repère locale du GPS.
    for i in range(len(data_imu)):
        acc_imu = np.array([data_imu[i]["accel_x"], 
                            data_imu[i]["accel_y"], 
                            data_imu[i]["accel_z"]]
                            )
        
        rot_matrix = matrice_rotation(
            data_imu[i]["roll"], 
            data_imu[i]["pitch"], 
            data_imu[i]["yaw"]
        )
        
        accel_world = rot_matrix @ acc_imu

        accel_world[2] -= 1.0 # Retire 1g (la gravitation de la Terre)
        
        data_imu[i]["accel_x"], data_imu[i]["accel_y"], data_imu[i]["accel_z"] = accel_world
    """

    if not gps_out == "cartesian":
        for i, scan in enumerate(data_gps):
            latitude, longitude, altitude = cartesian_to_gps(scan["latitude"], scan["longitude"], scan["altitude"], latitude0, longitude0, altitude0)
            data_gps[i]["latitude"], data_gps[i]["longitude"], data_gps[i]["altitude"] = latitude, longitude, altitude

    return data_gps, data_imu