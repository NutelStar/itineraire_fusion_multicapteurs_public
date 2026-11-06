import pandas as pd
import argparse
import numpy as np
from utils.save_in_file import save_calib_offset
from scipy import stats
import matplotlib.pyplot as plt

IMU_CALIBRATION_PATH = "data/calibration/acq_imu_immobile/imu_scan.csv"
GPS_CALIBRATION_PATH = "data/calibration/acq_gps_immobile/gps_scan.csv"

def calcul_offset_imu(df, seuil = 3.0):
    """
    Détermine le biais et l'écart-type de chaque type de données renvoyés par l'IMU.
    """
    # Colonnes attendues pour l'accélération et le gyroscope
    cols = ['Accel X', 'Accel Y', 'Accel Z','Gyro X', 'Gyro Y', 'Gyro Z']
    
    # Vérifier que les colonnes existent
    for col in cols:
        if col not in df.columns:
            raise ValueError(f"La colonne {col} est manquante dans le fichier source.")

    # Retrait des points aberrants
    z_scores = np.abs(stats.zscore(df[cols]))
    masque = (z_scores < seuil).all(axis=1)
    df_nettoye = df[masque].copy()
    df = df_nettoye

    # Calculer biais (moyenne) et écart type pour chaque axe
    BIAIS_IMU = {}
    for col in cols:
        biais = float(df[col].mean())
        ecart_type = float(df[col].std())
        print(f"Axe : {col}, biais : {biais}, std : {ecart_type}")
        BIAIS_IMU[col] = {'biais': biais, 'ecart_type': ecart_type}

    BIAIS_IMU["Accel X"]["biais"] -= 1.0 # retire la composante g

    save_calib_offset(biais_imu=BIAIS_IMU, path="config/calib_offset.py")
    print("Configuration biais de l'IMU enregistrée dans config/calib_offset.py")

    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    fig.suptitle("Données IMU", fontsize=16, fontweight='bold')
    axes = axes.flatten()
    BIAIS_IMU["Accel X"]["biais"] += 1.0 # remet la composant g TEMPORAIREMENT pour l'affichage
    for i, col in enumerate(cols):
        mu, sigma = BIAIS_IMU[col]['biais'], BIAIS_IMU[col]['ecart_type']
        
        axes[i].hist(df[col], bins=40, alpha=0.65, color='royalblue', edgecolor='black', density=True)
        
        axes[i].axvline(mu, color='red', linestyle='-', linewidth=2, label=f'Moyenne: {mu}')
        axes[i].axvline(mu + sigma, color='purple', linestyle='--', linewidth=1.5, label=f'+sigma: {mu+sigma}')
        axes[i].axvline(mu - sigma, color='purple', linestyle='--', linewidth=1.5, label=f'-sigma: {mu-sigma}')
        
        axes[i].set_title(col, fontsize=12, fontweight='bold')
        axes[i].set_xlabel("Valeur du capteur")
        axes[i].set_ylabel("Densité de probabilité")
        axes[i].grid(True, alpha=0.3)
        axes[i].legend(loc='upper right', fontsize=9)

    plt.tight_layout()
    plt.show()

def main(csv_imu):
    if csv_imu == "":
        csv_imu = IMU_CALIBRATION_PATH
    data_imu = pd.read_csv(csv_imu)

    calcul_offset_imu(data_imu)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calcul des offsets/écarts-types des données IMU pour préparer la calibration.")
    parser.add_argument(
        "-s_imu","--source_imu",
        type=str,
        default="",
        help="Chemin vers le fichier CSV de calibration de l'IMU (IMU immobile)."
    )

    args = parser.parse_args()

    main(args.source_imu)