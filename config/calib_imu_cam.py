import math

# les mesures suivantes ont été calculées à la main

image_taille = 640

ANGLE = math.radians(120)

camera_hoz = math.radians(62.2)
cemera_ver = math.radians(48.8)

fx = (image_taille / 2) / math.tan(camera_hoz/2)

cx = image_taille/2

tx = 0.143 # en mètres
ty = 0.060 # en mètres