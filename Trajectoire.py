
import argparse

from postprocessing.plot_gnss import plot_GNSS
from scripts.MULTISENSOR.capture_gnss_imu import acquisition_multisensor, initialisation_capteurs
from postprocessing.pre_traitement import pre_traitement
from postprocessing.kalman_filter import filtre_de_kalman

TRAJECTOIRE_CLASSIQUE_FILE = "trajectoire_classique"
TRAJECTOIRE_KALMAN_FILE = "trajectoire_kalman"

def main(acquisition_dir):

    if not acquisition_dir:
        #  1 - Acquistion multicapteurs des données GPS et IMU
        #    - Active avec un bouton, sort de la fonction au moment de la désactivation
        #    - La fonction renvoit le chemin du dossier d'acquisition
        print("Démarrage de l'acquisition multicapteurs...")
        print("Calibration: appuyez sur le bouton pour démarrer une acquisition de calibration (10 secondes).")
        print("Réalisez des 8s avec le magnétomètre doucement.")
        print("Bon voyage !")
        acquisition_dir = acquisition_multisensor(mode = "trajectoire")

    # 2 - Pré-traitement des données GPS et IMU
    #   - Crée 2 fichiers csv : processed_gps_scan.csv et processed_imu_scan.csv
    #   - Crée un premier fichier html affichant la trajectoire classique
    print("Pré-traitement des données...")
    pre_traitement(acquisition_dir)
    print("Création du fichier de la trajectoire classique...")
    plot_GNSS(acquisition_dir, TRAJECTOIRE_CLASSIQUE_FILE, "cartesian", "processed_gps_scan.csv")

    # 3 - Application d'un filtre de Kalman pour estimer la trajectoire du véhicule à partir des données
    #   - Lit chaque donnée de l'IMU dans le fichier csv une par une, une estimation pour chaque donnée d'IMU 
    #   - Puis, corrige avec les données GPS quand elles sont disponibles (selon le timestamp)
    print("Fusion des données...")
    filtre_de_kalman(acquisition_dir)

    # 4 - Affichage de la trajectoire estimée
    print("Création du fichier de la trajectoire améliorée...")
    plot_GNSS(acquisition_dir, TRAJECTOIRE_KALMAN_FILE, "kalman", False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Principal script d'acquisition de la trajectoire à l'aide de données IMU et GPS."
    )

    parser.add_argument(
        "--acquisition_folder",
        type=str,
        help="Suivie du dossier d'acquisition. Cela sautera l'étape d'acquisition d'une nouvelle trajectoire et traitera directement des données."
    )

    args = parser.parse_args()

    main(args.acquisition_folder)