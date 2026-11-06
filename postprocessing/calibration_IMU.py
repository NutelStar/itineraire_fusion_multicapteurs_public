import pandas as pd
import numpy as np
import argparse
from config.calib_offset import BIAIS_IMU
from utils.read_csv_files import read_imu_csv
from utils.path import Path
from utils.CSVHandler import CSVHandler

def normalize_imu_data(data_imu):
    """
    Normalise les données IMU à partir d'un fichier CSV et enregistre le résultat.

    Arguments:
        input_csv_path : Chemin vers le fichier CSV à calibrer.
        output_csv_path : Chemin vers le fichier CSV calibré à créer.
    """
    for i, scan in enumerate(data_imu):
        scan["accel_x"] -= BIAIS_IMU["Accel X"]["biais"]
        scan["accel_y"] -= BIAIS_IMU["Accel Y"]["biais"]
        scan["accel_z"] -= BIAIS_IMU["Accel Z"]["biais"]
        scan["gyro_x"] -= BIAIS_IMU["Gyro X"]["biais"]
        scan["gyro_y"] -= BIAIS_IMU["Gyro Y"]["biais"]
        scan["gyro_z"] -= BIAIS_IMU["Gyro Z"]["biais"]

        scan["accel_x"] -= 1. # Retrait de 1g

        data_imu[i] = scan

    return data_imu

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calcule les données IMU calibrées à partir d'un fichier CSV.")
    parser.add_argument(
        "-s","--source",
        type=str,
        required=True,
        help="Chemin vers le fichier CSV à calibrer."
    )

    # Analyse des arguments
    args = parser.parse_args()

    acquisition_dir = Path(args.source)
    data_imu = read_imu_csv(acquisition_dir / "imu_scan.csv")

    # Appel de la fonction avec le fichier source
    data_imu = normalize_imu_data(data_imu)

    normalized_imu_path = acquisition_dir / "normalized_imu_scan.csv"
    normalized_imu = CSVHandler(str(normalized_imu_path))
    normalized_imu.create_csv_with_header([
        "Timestamp",
        "Accel X",
        "Accel Y",
        "Accel Z",
        "Gyro X",
        "Gyro Y",
        "Gyro Z",
        "Magneto X",
        "Magneto Y",
        "Magneto Z"
    ])
    for scan in data_imu:
        normalized_imu.append_row([scan["timestamp"],
                                scan["accel_x"], scan["accel_y"], scan["accel_z"],
                                scan["gyro_x"], scan["gyro_y"], scan["gyro_z"],
                                scan["magneto_x"], scan["magneto_y"], scan["magneto_z"]])