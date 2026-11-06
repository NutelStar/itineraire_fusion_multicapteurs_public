import argparse
import sys
from pathlib import Path
import copy

# Add project root to path so utils can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import CSVHandler
import numpy as np
import pandas as pd

from postprocessing.changement_base import changement_de_base, redresser_axes_imu
from postprocessing.retrait_points_aberrants import retrait_points_aberrants_gps, retrait_points_aberrants_imu
from utils.read_csv_files import read_gps_csv, read_imu_csv
from postprocessing.calibration_IMU import normalize_imu_data
import copy

ALPHA = 0.05

def calcul_roll_pitch_yaw(data_imu):
    """
    Calcule les angles de roll, pitch et yaw à partir des données IMU.
    Orientation d'entrée attendue : X=Avant, Y=Droite, Z=Haut.
    """
    roll_gyro = 0.0
    pitch_gyro = 0.0
    
    prev_timestamp = data_imu[0]["timestamp"]

    for i, scan in enumerate(data_imu):
        accel_x = scan["accel_x"]
        accel_y = scan["accel_y"]
        accel_z = scan["accel_z"]
        
        # 1) Conversion des gyroscopes en rad/s
        gyro_x = np.radians(scan["gyro_x"])             # Roll  (autour de l'axe X)
        gyro_y = np.radians(scan["gyro_y"])             # Pitch (autour de l'axe Y)
        gyro_z = np.radians(scan["gyro_z"])             # Yaw   (autour de l'axe Z)
        
        magneto_x = scan["magneto_x"]
        magneto_y = scan["magneto_y"]
        magneto_z = scan["magneto_z"]
        
        # Gestion du temps dt
        if i > 0:
            dt = scan["timestamp"] - prev_timestamp
        else:
            dt = 0.0
        prev_timestamp = scan["timestamp"]
        
        # 2) Angles via l'Accéléromètre
        pitch_accel = np.arctan2(accel_x, np.sqrt(accel_y**2 + accel_z**2))
        roll_accel = np.arctan2(-accel_y, accel_z)

        # 3) Intégration des Gyroscopes
        roll_gyro  += gyro_x * dt 
        pitch_gyro += gyro_y * dt 
        roll = ALPHA * roll_accel + (1 - ALPHA) * roll_gyro
        pitch = ALPHA * pitch_accel + (1 - ALPHA) * pitch_gyro

        # 4) Projection du Magnétomètre à plat (Plan horizontal perpendiculaire à la gravité Z)
        cos_p, sin_p = np.cos(pitch), np.sin(pitch)
        cos_r, sin_r = np.cos(roll),  np.sin(roll)
        xh = magneto_x * cos_p + magneto_y * sin_p * sin_r + magneto_z * sin_p * cos_r
        yh = magneto_y * cos_r - magneto_z * sin_r
        
        # Le yaw: donne l'angle par rapport au nord magnétique
        yaw = np.arctan2(-yh, xh)
        
        # Stockage des angles en radians
        scan["roll"] = roll
        scan["pitch"] = pitch
        scan["yaw"] = yaw
        
        data_imu[i] = scan

    return data_imu

def calibrer_magnetometre(data_calib_imu, data_imu):
    """
    Calcule les offsets du magnétomètre à partir de la calibration (mouvement en 8)
    et les applique sur le jeu de données final.
    """
    # Récupération du centre de la sphère
    max_x, min_x = data_calib_imu[0]["magneto_x"], data_calib_imu[0]["magneto_x"]
    max_y, min_y = data_calib_imu[0]["magneto_y"], data_calib_imu[0]["magneto_y"]
    max_z, min_z = data_calib_imu[0]["magneto_z"], data_calib_imu[0]["magneto_z"]
    
    for scan in data_calib_imu:
        if scan["magneto_x"] > max_x: max_x = scan["magneto_x"]
        if scan["magneto_x"] < min_x: min_x = scan["magneto_x"]
        if scan["magneto_y"] > max_y: max_y = scan["magneto_y"]
        if scan["magneto_y"] < min_y: min_y = scan["magneto_y"]
        if scan["magneto_z"] > max_z: max_z = scan["magneto_z"]
        if scan["magneto_z"] < min_z: min_z = scan["magneto_z"]
        
    offsets = {
        'x': (max_x + min_x) / 2,
        'y': (max_y + min_y) / 2,
        'z': (max_z + min_z) / 2
    }

    print(f"Magnétomètre calibration:\n \
    offsetx = {offsets["x"]}\n \
    offsety = {offsets["y"]}\n \
    offsetz = {offsets["z"]}\n")

    for scan in data_imu:
        scan['magneto_x'] -= offsets['x']
        scan['magneto_y'] -= offsets['y']
        scan['magneto_z'] -= offsets['z']

    return data_imu

def pre_traitement(acquisition_dir, gps_out = "cartesian"):
    acquisition_dir = Path(acquisition_dir)
    data_gps = read_gps_csv(acquisition_dir / "gps_scan.csv")
    data_imu = read_imu_csv(acquisition_dir / "imu_scan.csv")
    data_calib_imu = read_imu_csv(acquisition_dir / "calibration_imu_scan.csv")

    # Retrait du biais de l'IMU
    print("Normalisation des données...")
    data_imu = normalize_imu_data(data_imu)

    # Retrait des points aberrants de la latitude et longitude
    print("Retrait des points aberrants des données GPS...")
    data_gps = retrait_points_aberrants_gps(data_gps)

    # Retrait des points aberrants des données IMU
    print("Retrait des points aberrants des données IMU...")
    data_imu = retrait_points_aberrants_imu(data_imu)

    # Redressage du repère de l'IMU dans le repère classique
    print("Permutation du repère IMU dans celui standard de la carte...")
    data_imu = redresser_axes_imu(data_imu)
    data_calib_imu = redresser_axes_imu(data_calib_imu)

    # Calibration du magnétomètre
    print("Calibration du magnétomètre...")
    data_imu = calibrer_magnetometre(data_calib_imu, data_imu)

    # Calcule des angles roll, pitch et yaw
    print("Calcul des angles roll, pitch et yaw..")
    data_imu = calcul_roll_pitch_yaw(data_imu)

    # Passage du repère de l'IMU dans le repère GPS
    print("Changement de repère des données IMU sur celui de la carte...")
    data_gps, data_imu = changement_de_base(data_gps, data_imu, gps_out)

    # Sauvegarde des données traitées
    print("Sauvegarde des données pré-traitées...")
    processed_gps_path = acquisition_dir / "processed_gps_scan.csv"
    processed_imu_path = acquisition_dir / "processed_imu_scan.csv"

    processed_gps = CSVHandler(str(processed_gps_path))
    processed_imu = CSVHandler(str(processed_imu_path))

    processed_gps.create_csv_with_header([
        "Timestamp",
        "Latitude",
        "Longitude",
        "Altitude"
    ])
    processed_imu.create_csv_with_header([
        "Timestamp",
        "Accel X",
        "Accel Y",
        "Accel Z",
        "Gyro X",
        "Gyro Y",
        "Gyro Z",
        "Roll",
        "Pitch",
        "Yaw"
    ])

    for scan in data_gps:
        processed_gps.append_row([scan["timestamp"],
                                scan["latitude"], scan["longitude"], scan["altitude"]])
    for scan in data_imu:
        processed_imu.append_row([scan["timestamp"],
                                scan["accel_x"], scan["accel_y"], scan["accel_z"],
                                scan["gyro_x"], scan["gyro_y"], scan["gyro_z"],
                                scan["roll"], scan["pitch"], scan["yaw"]])

def main(raw_acquisition_dir, gps_out = "cartesian"):
    pre_traitement(raw_acquisition_dir, gps_out=gps_out)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pré-traitement des données IMU/GPS synchronisées."
    )

    parser.add_argument(
        "raw_acquisition_dir",
        type=str,
        help="Dossier des données brutes."
    )

    parser.add_argument(
        "--type_gps_output",
        type=str,
        default="cartesian",
        help="Type de sortie pour les données GPS."
    )

    args = parser.parse_args()

    main(
        raw_acquisition_dir=args.raw_acquisition_dir,
        gps_out=args.type_gps_output,
    )