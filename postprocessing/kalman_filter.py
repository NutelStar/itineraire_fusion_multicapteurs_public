import numpy as np
import csv
import os
import argparse

from config.calib_bruit import BRUIT_GPS, BRUIT_GYROSCOPE, BRUIT_VITESSE
from config.calib_offset import BIAIS_IMU

from utils.read_csv_files import read_processed_gps_csv, read_imu_csv
from utils.path import Path
from utils.CSVHandler import CSVHandler

G = 9.81

def wrap_angle(angle):
    """
    Contraint un angle (en radians) dans l'intervalle [-pi, pi].
    """
    return (angle + np.pi) % (2 * np.pi) - np.pi

def preprocess_data(gps_data, imu_data):
    """
    Aligne les échelles de temps et convertit les unités directement.
    """
    if not gps_data or not imu_data:
        raise ValueError("Les listes de données GPS ou IMU sont vides.")

    # Trouver le temps initial minimum
    min_gps_t = min(scan["timestamp"] for scan in gps_data)
    min_imu_t = min(scan["timestamp"] for scan in imu_data)
    t0 = min(min_gps_t, min_imu_t)

    # Traitement des données IMU
    for scan in imu_data:
        scan["time"] = scan["timestamp"] - t0

        # Conversion des accélérations en m/s²
        scan["gX"] = scan["accel_x"] * G
        scan["gY"] = scan["accel_y"] * G
        scan["gZ"] = scan["accel_z"] * G
        
        # Conversion des vitesses angulaires en rad/s
        scan["rX"] = np.deg2rad(scan["gyro_x"])
        scan["rY"] = np.deg2rad(scan["gyro_y"])
        scan["rZ"] = np.deg2rad(scan["gyro_z"])

    # Traitement des données GPS
    for scan in gps_data:
        scan["time"] = scan["timestamp"] - t0

    return gps_data, imu_data

def fusion_donnees_kalman_EKF(gps_data, imu_data, sigma_gps = 1.5, sigma_ax = 0.5, sigma_ay = 0.5, sigma_w = 0.05):
    """
    EKF complet prenant en compte l'accélération ax et ay de l'IMU.
    """
    entries = []
    for scan in imu_data:
        entries.append({
            'time': scan['time'], 
            'type': 'IMU', 
            'ax': scan['gX'],
            'ay': scan['gY'],
            'w': scan['rZ']
        }) 
        
    for scan in gps_data:
        entries.append({
            'time': scan['time'], 
            'type': 'GPS', 
            'x': scan['longitude'], 
            'y': scan['latitude']
        })
    
    entries.sort(key=lambda e: e['time'])

    # Etat: [X, Y, Theta, Vx, Vy]
    first_gps = gps_data[0]
    x = np.array([[first_gps['longitude']], [first_gps['latitude']], [0.0], [0.0], [0.0]])
    
    # Covariance initiale
    sigma_gps = BRUIT_GPS['sigma_moyen']
    P = np.array([
        [sigma_gps**2, 0.0, 0.0, 0.0, 0.0],
        [0.0, sigma_gps**2, 0.0, 0.0, 0.0],
        [0.0, 0.0, np.deg2rad(45)**2, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 1.0]
    ])
    
    sigma_ax = BRUIT_VITESSE['sigma_ax']
    sigma_ay = BRUIT_VITESSE['sigma_ay']
    sigma_w = BRUIT_GYROSCOPE['sigma_w'] 
    Q_u = np.array([
        [sigma_ax**2, 0.0, 0.0],
        [0.0, sigma_ay**2, 0.0],
        [0.0, 0.0, sigma_w**2]
    ])
    
    H = np.array([[1.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 1.0, 0.0, 0.0, 0.0]])
    
    gps_var_x = BRUIT_GPS['var_x']
    gps_var_y = BRUIT_GPS['var_y']
    R = np.array([
        [gps_var_x, 0.0],
        [0.0, gps_var_y]
    ])

    history_t, history_x, history_y = [], [], []
    last_time = entries[0]['time']

    for entry in entries:
        t = entry['time']
        dt = t - last_time
        if dt < 0: dt = 0
            
        theta = float(x[2, 0])
        vx = float(x[3, 0])
        vy = float(x[4, 0])


        if entry['type'] == 'IMU':
            # --- PRÉDICTION ---
            ax = entry['ax']
            ay = entry['ay']
            w = entry['w']

            ax_global = ax * np.cos(theta) - ay * np.sin(theta)
            ay_global = ax * np.sin(theta) + ay * np.cos(theta)

            x_pred = np.array([
                [float(x[0, 0]) + vx * dt],
                [float(x[1, 0]) + vy * dt],
                [wrap_angle(theta + w * dt)],
                [vx + ax_global * dt],
                [vy + ay_global * dt]
            ])

            # Jacobienne
            F = np.array([
                [1.0, 0.0, 0, dt, 0.0],
                [0.0, 1.0, 0, 0.0, dt ],
                [0.0, 0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, dt * (-ax * np.sin(theta) - ay * np.cos(theta)), 1.0, 0.0],
                [0.0, 0.0, dt * ( ax * np.cos(theta) - ay * np.sin(theta)), 0.0, 1.0]
            ])

            # Matrice Gamma pour propager les bruits [ax, ay, w]
            Gamma = np.array([
                [ 0.0, 0.0, 0.0],
                [ 0.0, 0.0, 0.0],
                [ 0.0, 0.0, dt ],
                [ dt * np.cos(theta), -dt * np.sin(theta), 0.0],
                [ dt * np.sin(theta),  dt * np.cos(theta), 0.0]
            ])

            Q = Gamma @ Q_u @ Gamma.T
            P = F @ P @ F.T + Q
            x = x_pred

        elif entry['type'] == 'GPS':
            # --- CORRECTION ---
            z = np.array([[entry['x']], [entry['y']]])

            # Innovation
            nu = z - H @ x  

            # Covariance de l'innovation
            S = H @ P @ H.T + R

            # Gain de Kalman
            K = P @ H.T @ np.linalg.inv(S) 

            x = x + K @ nu
            x[2, 0] = wrap_angle(x[2, 0])
            P = (np.eye(5) - K @ H) @ P

        history_t.append(t)
        history_x.append(float(x[0, 0]))
        history_y.append(float(x[1, 0]))
        last_time = t

    return history_t, history_x, history_y

def export_donnees_kalman(t, x, y, acquisition_dir):
    """Exporte la trajectoire calculée dans un fichier CSV standard."""

    # Sauvegarde des données traitées
    processed_gps_path = acquisition_dir / "kalman_resultats.csv"

    data_kalman = CSVHandler(str(processed_gps_path))

    data_kalman.create_csv_with_header([
        "t",
        "x",
        "y",
        "z"
    ])

    for t_scan, x_scan, y_scan in zip(t, x, y):
        data_kalman.append_row([t_scan, x_scan, y_scan])

    print(f"Fichier exporté avec succès avec {len(t)} lignes")

def filtre_de_kalman(acquisition_dir):
    """
    Fonction principale prenant en paramètre le chemin du dossier d'acquisition.
    Charge, traite et fusionne les données sans utiliser Pandas.
    """
    print(f"--- Début du traitement Kalman pour: {acquisition_dir} ---")
    acquisition_dir = Path(acquisition_dir)
    data_gps = read_processed_gps_csv(acquisition_dir / "processed_gps_scan.csv")
    data_imu = read_imu_csv(acquisition_dir / "processed_imu_scan.csv")
    
    # Conversion des unités
    data_gps, data_imu = preprocess_data(data_gps, data_imu)
    
    # Filtre EKF
    t_filt, x_filt, y_filt = fusion_donnees_kalman_EKF(
        data_gps, data_imu
    )

    export_donnees_kalman(t_filt, x_filt, y_filt, acquisition_dir)
    print("--- Fin du traitement avec succès ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pré-traitement des données IMU/GPS synchronisées."
    )

    parser.add_argument(
        "raw_acquisition_dir",
        type=str,
        help="Dossier des données brutes."
    )
        
    args = parser.parse_args()

    filtre_de_kalman(args.raw_acquisition_dir)