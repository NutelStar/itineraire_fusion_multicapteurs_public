import numpy as np
import argparse
from pathlib import Path
import sys
from utils.read_csv_files import read_gps_csv, read_imu_csv

# Add project root to path so utils can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import CSVHandler

def retrait_points_aberrants_gps(data_gps, vitesse_max_kmh=100):
    """
    Nettoie les points aberrants GPS selon la vitesse entre 2 points.
    """
    if not data_gps:
        return data_gps

    data_gps_traite = []
    data_gps_traite.append(data_gps[0])  # On garde le premier point
    for i in range(len(data_gps) - 1):
        latitude1 = np.radians(data_gps[i]['latitude'])
        longitude1 = np.radians(data_gps[i]['longitude'])
        latitude2 = np.radians(data_gps[i + 1]['latitude'])
        longitude2 = np.radians(data_gps[i + 1]['longitude'])

        dlatitude = latitude2 - latitude1
        dlongitude = longitude2 - longitude1

        a = np.sin(dlatitude/2)**2 + np.cos(latitude1) * np.cos(latitude2) * np.sin(dlongitude/2)**2
        dist_km = 6371 * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))

        temps = (data_gps[i + 1]['timestamp'] - data_gps[i]['timestamp']) / 3600
        if temps > 0:
            vitesse = dist_km / temps
            if vitesse < vitesse_max_kmh:
                data_gps_traite.append(data_gps[i+1])

    return data_gps_traite

def retrait_points_aberrants_imu(data_imu, accel_threshold=50, gyro_threshold=1000):
    """
    Nettoie les points aberrants IMU selon des seuils pour les accélérations et gyroscopes.
    """
    if not data_imu:
        return data_imu

    data_imu_traite = []
    for scan in data_imu:
        accel_x = abs(scan["accel_x"])
        accel_y = abs(scan["accel_y"])
        accel_z = abs(scan["accel_z"])
        gyro_x = abs(scan["gyro_x"])
        gyro_y = abs(scan["gyro_y"])
        gyro_z = abs(scan["gyro_z"])

        if (accel_x < accel_threshold and accel_y < accel_threshold and accel_z < accel_threshold and
            gyro_x < gyro_threshold and gyro_y < gyro_threshold and gyro_z < gyro_threshold):
            data_imu_traite.append(scan)

    return data_imu_traite

def main(data_dir):
    data_dir = Path(data_dir)
    gps_path = data_dir / "gps_scan.csv"
    imu_path = data_dir / "imu_scan.csv"

    if not gps_path.exists():
        print(f"Fichier GPS non trouvé : {gps_path}")
        return
    if not imu_path.exists():
        print(f"Fichier IMU non trouvé : {imu_path}")
        return

    # Lire les données
    data_gps = read_gps_csv(gps_path)
    data_imu = read_imu_csv(imu_path)

    # Retirer les points aberrants
    data_gps_clean = retrait_points_aberrants_gps(data_gps)
    data_imu_clean = retrait_points_aberrants_imu(data_imu)

    # Sauvegarder les données nettoyées (écraser les fichiers originaux)
    if gps_path.exists():
        gps_path.unlink()
    gps_handler = CSVHandler(str(gps_path))
    gps_handler.create_csv_with_header([
        "Timestamp",
        "Latitude",
        "Longitude",
        "Altitude"
    ])
    for scan in data_gps_clean:
        gps_handler.append_row([scan["timestamp"], scan["latitude"], scan["longitude"], scan["altitude"]])

    if imu_path.exists():
        imu_path.unlink()
    imu_handler = CSVHandler(str(imu_path))
    imu_header = [
        "Timestamp",
        "Accel X",
        "Accel Y",
        "Accel Z",
        "Gyro X",
        "Gyro Y",
        "Gyro Z"
    ]
    if data_imu_clean and "magneto_x" in data_imu_clean[0]:
        imu_header.extend(["Magneto X", "Magneto Y", "Magneto Z"])

    imu_handler.create_csv_with_header(imu_header)
    for scan in data_imu_clean:
        row = [
            scan["timestamp"], scan["accel_x"], scan["accel_y"], scan["accel_z"],
            scan["gyro_x"], scan["gyro_y"], scan["gyro_z"]
        ]
        if "magneto_x" in scan:
            row.extend([scan["magneto_x"], scan["magneto_y"], scan["magneto_z"]])
        imu_handler.append_row(row)

    print(f"Points aberrants retirés. GPS: {len(data_gps)} -> {len(data_gps_clean)}, IMU: {len(data_imu)} -> {len(data_imu_clean)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retirer les points aberrants des fichiers GPS et IMU.")

    parser.add_argument(
        "data_dir", 
        type=str, 
        help="Dossier contenant gps_scan.csv et imu_scan.csv"
    )
    
    args = parser.parse_args()

    main(args.data_dir)