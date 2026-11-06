import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core import (
    lidar_to_camera,
    projection_pixel,
    is_in_camera_fov,
    get_roi_from_lidar
)

# --- Test 1 : obstacle droit devant la caméra ---
print("=== Test 1 : obstacle droit devant ===")
pts_min = (0, 1000)   # 1 mètre droit devant en mm
u, in_fov = get_roi_from_lidar(pts_min)
print(f"u = {u:.1f} pixels")
print(f"Dans le champ : {in_fov}")
print(f"Attendu : u proche de cx (320), in_fov = True")
print()

# --- Test 2 : obstacle très à gauche ---
print("=== Test 2 : obstacle hors champ à gauche ===")
pts_min = (-5000, 1000)   # très à gauche
u, in_fov = get_roi_from_lidar(pts_min)
print(f"u = {u:.1f} pixels")
print(f"Dans le champ : {in_fov}")
print(f"Attendu : u < 0, in_fov = False")
print()

# --- Test 3 : obstacle derrière la caméra ---
print("=== Test 3 : obstacle derrière la caméra ===")
pts_min = (0, -500)   # derrière en mm
u, in_fov = get_roi_from_lidar(pts_min)
print(f"u = {u}")
print(f"Dans le champ : {in_fov}")
print(f"Attendu : u = None, in_fov = False")
print()

# --- Test 4 : pas de point détecté ---
print("=== Test 4 : pts_min = None ===")
u, in_fov = get_roi_from_lidar(None)
print(f"u = {u}")
print(f"Dans le champ : {in_fov}")
print(f"Attendu : u = None, in_fov = False")