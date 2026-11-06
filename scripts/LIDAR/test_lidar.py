import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sensors.LIDAR.lidar import LIDAR
import math

# Instancie la classe sans connexion série
lidar_instance = LIDAR.__new__(LIDAR)

# Données simulées — pas besoin du vrai LiDAR
points_simules = [
    (500.0, 100.0),   # distance = 510 mm
    (-80.0, 210.0),   # distance = 225 mm  ← le plus proche
    (120.0, 340.0),   # distance = 362 mm
]

# Test get_pts_proche
pts_min, distance = lidar_instance.get_pts_proche(points_simules)
print(f"Point le plus proche : {pts_min}")
print(f"Distance : {distance:.1f} mm")

# Test obstacle_detecte
danger = lidar_instance.obstacle_detecte(distance, seuil_mm=300)
print(f"Obstacle détecté (seuil 300mm) : {danger}")

danger2 = lidar_instance.obstacle_detecte(distance, seuil_mm=200)
print(f"Obstacle détecté (seuil 200mm) : {danger2}")

# Test liste vide
pts_min_vide, distance_vide = lidar_instance.get_pts_proche([])
print(f"Liste vide — pts_min : {pts_min_vide}, distance : {distance_vide}")