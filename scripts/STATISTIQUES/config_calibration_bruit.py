import pandas as pd
import argparse
import numpy as np
from pathlib import Path
from scipy import stats
import matplotlib.pyplot as plt
from utils.save_in_file import save_calib_bruit
from postprocessing.changement_base import gps_to_cartesian

IMU_CALIBRATION_PATH = "data/calibration/acq_imu_ligne_droite/imu_scan.csv"
GPS_CALIBRATION_PATH = "data/calibration/acq_gps_immobile/gps_scan.csv"
G = 9.81

def retrait_points_aberrants_gps_pour_dataframe(df_gps, vitesse_max_kmh=100):
    """
    Nettoie de manière étanche les points aberrants GPS (Formule Haversine).
    Garantit qu'aucun point ne crée de saut physique impossible par rapport au dernier point SAIN.
    """
    indices_valides = [df_gps.index[0]]
    last_valid_idx = df_gps.index[0]
    
    for i in range(len(df_gps) - 1):
        indice_suivant = df_gps.index[i + 1]
        
        latitude1 = np.radians(df_gps.loc[last_valid_idx, 'Latitude'])
        longitude1 = np.radians(df_gps.loc[last_valid_idx, 'Longitude'])
        latitude2 = np.radians(df_gps.loc[indice_suivant, 'Latitude'])
        longitude2 = np.radians(df_gps.loc[indice_suivant, 'Longitude'])

        dlatitude = latitude2 - latitude1
        dlongitude = longitude2 - longitude1

        a = np.sin(dlatitude/2)**2 + np.cos(latitude1) * np.cos(latitude2) * np.sin(dlongitude/2)**2
        a = max(0.0, min(1.0, a))

        dist_km = 6371.0 * 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
        temps_h = (df_gps.loc[indice_suivant, "Timestamp"] - df_gps.loc[last_valid_idx, "Timestamp"]) / 3600.0
        
        if temps_h <= 0:
            if dist_km > 0.001: 
                continue
            else:
                indices_valides.append(indice_suivant)
                continue

        vitesse = dist_km / temps_h
        if vitesse < vitesse_max_kmh:
            indices_valides.append(indice_suivant)
            last_valid_idx = indice_suivant
            
    return df_gps.loc[indices_valides].copy()

def calculer_bruit(df_gps, df_imu):
    """
    Calcule les bruits du GPS et de l'IMU.
    """
    # === Bruit GPS ===
    # Retrait des points aberrants
    print(f"Taille DataFrame avant: {len(df_gps)}")
    df_gps = retrait_points_aberrants_gps_pour_dataframe(df_gps, vitesse_max_kmh=100)
    print(f"Taille DataFrame après: {len(df_gps)}")

    # Passage en mètres (cartésien)
    latitude0 = df_gps['Latitude'].iloc[0]
    df_gps_cartesien = df_gps.apply(
        lambda row: gps_to_cartesian(row['Latitude'], row['Longitude'], row['Altitude'], latitude0),
        axis=1
    )
    df_metres = pd.DataFrame(df_gps_cartesien.tolist(), columns=['x', 'y', 'z'], index=df_gps.index)
    df_gps['x'] = df_metres['x']
    df_gps['y'] = df_metres['y']
    df_gps['z'] = df_metres['z']

    BRUIT_GPS = {}
    gps_x = df_gps['x'].to_numpy()
    gps_y = df_gps['y'].to_numpy()
    var_gps_x = float(df_gps['x'].var())
    var_gps_y = float(df_gps['y'].var())
    sigma_gps_moyen = float(np.sqrt((var_gps_x + var_gps_y) / 2.0))
    BRUIT_GPS['var_x'] = var_gps_x
    BRUIT_GPS['var_y'] = var_gps_y
    BRUIT_GPS['sigma_moyen'] = sigma_gps_moyen
    
    # === Bruit gyroscope ===
    BRUIT_GYROSCOPE = {}
    imu_w = np.deg2rad(df_imu['Gyro X'].to_numpy())
    var_w = float(imu_w.var())
    sigma_w = float(np.sqrt(var_w))
    BRUIT_GYROSCOPE['var_w'] = var_w
    BRUIT_GYROSCOPE['sigma_w'] = sigma_w

    # === Bruit accélération ===
    BRUIT_VITESSE = {}
    imu_ax = df_imu['Accel Z'].to_numpy() * G
    var_ax = float(imu_ax.var())
    imu_ay = df_imu['Accel Y'].to_numpy() * G
    var_ay = float(imu_ay.var())
    sigma_ax = float(np.sqrt(var_ax))
    sigma_ay = float(np.sqrt(var_ay))
    BRUIT_VITESSE['var_ax'] = var_ax
    BRUIT_VITESSE['var_ay'] = var_ax
    BRUIT_VITESSE['sigma_ax'] = sigma_ax
    BRUIT_VITESSE['sigma_ay'] = sigma_ay

    save_calib_bruit(bruit_gps=BRUIT_GPS, bruit_gyroscope=BRUIT_GYROSCOPE, bruit_vitesse=BRUIT_VITESSE, path="config/calib_bruit.py")
    print("Configuration bruit du GPS et de l'IMU enregistrée dans config/calib_bruit.py")

    plt.figure(figsize=(12, 4))
    plt.subplot(1, 4, 1)
    plt.scatter(gps_x - gps_x.mean(), gps_y - gps_y.mean(), alpha=0.5, color='red')
    plt.title(f"GPS\nsigma moyen = {sigma_gps_moyen} m")
    plt.xlabel("Erreur X (m)")
    plt.ylabel("Erreur Y (m)")
    plt.grid(True)
    
    plt.subplot(1, 4, 2)
    plt.hist(imu_w, bins=30, density=True, alpha=0.6, color='blue')
    plt.title(f"Gyroscope\nsigma = {sigma_w} rad/s")
    plt.grid(True)
    
    plt.subplot(1, 4, 3)
    plt.hist(imu_ax, bins=30, density=True, alpha=0.6, color='green')
    plt.title(f"Acéléromètre\nsigma = {sigma_ax} m/s^2")
    plt.grid(True)

    plt.subplot(1, 4, 4)
    plt.hist(imu_ay, bins=30, density=True, alpha=0.6, color='yellow')
    plt.title(f"Acéléromètre\nsigma = {sigma_ay} m/s^2")
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()

def main(csv_imu, csv_gps):
    if csv_imu == "":
        csv_imu = IMU_CALIBRATION_PATH
    if csv_gps == "":
        csv_gps = GPS_CALIBRATION_PATH

    data_imu = pd.read_csv(csv_imu)
    data_gps = pd.read_csv(csv_gps)

    calculer_bruit(data_gps, data_imu)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calcul des bruits des capteurs GPS et IMU pour préparer la calibration.")
    
    parser.add_argument(
        "-s_imu","--source_imu",
        type=str,
        default="",
        help="Chemin vers le fichier CSV de calibration du IMU (IMU en ligne droite)."
    )

    parser.add_argument(
        "-s_gps","--source_gps",
        type=str,
        default="",
        help="Chemin vers le fichier CSV de calibration du GPS (GPS immobile)."
    )


    args = parser.parse_args()

    main(args.source_imu, args.source_gps)