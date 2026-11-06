import math

# Calibration LiDAR/camera mesurée à la main.
# TX/TY sont en mm, ANGLE en radians.

ANGLE = -math.pi/2 # lidar vers caméra
TX = 0.143    # en m
TY = 0.060     # en m

# Seuil simple pour déclencher la camera quand un objet est proche
DISTANCE_DETECTEE_MM = 1000