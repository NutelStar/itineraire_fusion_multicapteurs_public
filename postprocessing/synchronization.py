import shutil
import argparse
from pathlib import Path
from utils import CSVHandler
import numpy as np

def read_timestamp_csv(csv_path):
    """
    Lit un CSV de timestamps au format :
    timestamp, chemin

    Returns
    -------
    list[dict]
        Liste de dictionnaires :
        - "timestamp"
        - "path"
    """
    rows = CSVHandler(str(csv_path)).read_dict_rows()
    entries = []

    for row in rows:
        try:
            keys = list(row.keys())
            if len(keys) < 2:
                continue

            timestamp = float(row[keys[0]])
            path = row[keys[1]]

            entries.append({
                "timestamp": timestamp,
                "path": path,
            })

        except (ValueError, TypeError):
            continue
    return entries

def read_timestamp_gps_csv(csv_path):
    """
    Lit un CSV de timestamps au format :
    timestamp, UTC, latitude, longitude
    """
    rows = CSVHandler(str(csv_path)).read_dict_rows()
    entries = []

    for row in rows:
        try:
            keys = list(row.keys())
            if len(keys) < 2:
                continue

            timestamp = float(row[keys[0]])
            UTC = row[keys[1]]
            latitude = float(row[keys[2]])
            longitude = float(row[keys[3]])
            altitude = float(row[keys[4]])

            entries.append({
                "timestamp": timestamp,
                "UTC": UTC,
                "latitude": latitude,
                "longitude": longitude,
                "altitude": altitude
            })

        except (ValueError, TypeError):
            continue
    return entries

def read_timestamp_imu_csv(csv_path):
    """
    Lit un CSV de timestamps au format :
    timestamp, UTC, latitude, longitude
    """
    rows = CSVHandler(str(csv_path)).read_dict_rows()
    entries = []

    for row in rows:
        try:
            keys = list(row.keys())
            if len(keys) < 2:
                continue

            timestamp = float(row[keys[0]])
            acx = float(row[keys[1]])
            acy = float(row[keys[2]])
            acz = float(row[keys[3]])
            gyrox = float(row[keys[4]])
            gyroy = float(row[keys[5]])
            gyroz = float(row[keys[6]])

            entries.append({
                "timestamp": timestamp,
                "accel_x": acx,
                "accel_y": acy,
                "accel_z": acz,
                "gyro_x": gyrox,
                "gyro_y": gyroy,
                "gyro_z": gyroz
            })

        except (ValueError, TypeError):
            continue
    return entries


def create_output_directory(raw_acquisition_dir, output1 = "images", output2 = "scans", suffix="_synced"):
    """
    Crée le dossier de sortie de la synchro offline.
    """
    raw_acquisition_dir = Path(raw_acquisition_dir)
    output_dir = raw_acquisition_dir.parent / f"{raw_acquisition_dir.name}{suffix}"

    output_dir.mkdir(parents=True, exist_ok=True)
    if output1 != None:
        (output_dir / output1).mkdir(exist_ok=True)
    if output2 != None:
        (output_dir / output2).mkdir(exist_ok=True)

    parameters_file = raw_acquisition_dir / "parameters.py"
    if parameters_file.exists():
        shutil.copy2(parameters_file, output_dir / "parameters.py")

    return output_dir


def synchronize_offline_camera_LiDAR(raw_acquisition_dir, threshold=0.10, suffix="_synced"):
    """
    Calcule les paires caméra/LiDAR synchronisées à partir d'une acquisition brute
    et les enregistre dans un nouveau dossier.

    Parameters
    ----------
    raw_acquisition_dir : str | Path
        Dossier de l'acquisition brute.
    threshold : float
        Seuil maximal |t_cam - t_lidar| en secondes.
    suffix : str
        Suffixe ajouté au nom du dossier de sortie.
    """
    raw_acquisition_dir = Path(raw_acquisition_dir)

    # Lecture des fichiers timestamps de la caméra et du LiDAR
    frames_csv = raw_acquisition_dir / "timestamps_frames.csv"
    scans_csv = raw_acquisition_dir / "timestamps_scans.csv"

    if not frames_csv.exists():
        raise FileNotFoundError(f"Fichier absent : {frames_csv}")
    if not scans_csv.exists():
        raise FileNotFoundError(f"Fichier absent : {scans_csv}")

    frame_entries = read_timestamp_csv(frames_csv)
    scan_entries = read_timestamp_csv(scans_csv)

    if not frame_entries:
        raise RuntimeError("Aucune frame trouvée dans timestamps_frames.csv")
    if not scan_entries:
        raise RuntimeError("Aucun scan trouvé dans timestamps_scans.csv")

    print("Données caméras : [")
    for f in frame_entries:
        print(f)
    print(']')
    print("Données LiDAR : [")
    for s in scan_entries:
        print(s)
    print(']')
    
    # Création du dossier d'acquisition syncrhonisée
    output_dir = create_output_directory(raw_acquisition_dir, suffix=suffix)
    output_images_dir = output_dir / "images"
    output_scans_dir = output_dir / "scans"

    # Création du fichier CSV indiquant les appariements réalisés
    synced_csv_path = output_dir / "synced_cam_lidar.csv"
    synced_csv = CSVHandler(str(synced_csv_path))
    # Header du CSV :
    # - pair_id : Identifiant de la paire
    # - frame_id : Identifiant de l'image dans le dossier d'acquisition brut (frame_xxxxxx.jpg)
    # - t_frame : Timestamp de l'image
    # - scan_id : Identifiant du scan dans le dossier d'acquisition brut (scan_xxxxxx.csv)
    # - t_scan : Timestamp du scan
    # - dt_s : Différence absolue entre les deux timestamps
    # - image_file : Chemin du fichier image    
    # - scan_file : Chemin du fichier scan

    synced_csv.create_csv_with_header([
        "pair_id",
        "frame_id",
        "t_camera",
        "scan_id",
        "t_lidar",
        "dt_s",
        "image_file",
        "scan_file",
    ])

    synced_count = 0
    used_scan_indices = set()

    for frame_id, frame_entry in enumerate(frame_entries):
        # A COMPLETER
        # Récupération du timestamp de l'image
        timestamp_img = frame_entry["timestamp"]
        #print(scan_entries)

        best_scan_indice = np.argmin(np.abs(np.array([entry["timestamp"] for entry in scan_entries]) - timestamp_img))
        # Recherche du scan avec le timestamp le plus proche
        np_scan_entries = np.array(scan_entries)
        best_timestamp = np_scan_entries[best_scan_indice]["timestamp"]
        

        # Récupération du timestamp du scan le plus proche temporellement
        best_scan = np_scan_entries[best_scan_indice]["path"]
        
        # Calcul de la différence absolue entre les deux timestamps
        diff = abs(best_timestamp-timestamp_img)

        # Sélection de la paire si la différence de temps est inférieure à un seuil prédéfini
        if diff > threshold: # Condition pour éliminer une paire
            continue

        # Récupération de l'index du scan le plus proche (dans le dossier d'acquisition)
        best_scan_indice

        # Sélection de la paire si le scan appairé n'a pas déjà été précédemment utilisé
        if best_scan_indice in used_scan_indices: # Condition pour éliminer une paire
            continue

        # Ajout de l'identifiant du scan dans le set des scans déjà utilisés
        used_scan_indices.add(best_scan_indice)

        # Copie des fichiers images et scans dans le dossier d'acquisition synchronisé 
        # ATTENTION : l'identifiant des nouveaux fichiers est différents des identifiants dans l'acquisition brute
        shutil.copyfile(frame_entry["path"], output_images_dir / f"frame_{synced_count:06d}.jpg" )
        
        shutil.copyfile(best_scan, output_scans_dir / f"scans_{synced_count:06d}.csv" )

        # Ecriture de la paire dans le fichier d'appariement CSV
        synced_csv.append_row([frame_id, frame_id, timestamp_img,
                               best_scan_indice, best_timestamp, diff,
                               frame_entry["path"], best_scan])
        

        synced_count += 1

    print(f"Dossier brut        : {raw_acquisition_dir}")
    print(f"Dossier synchronisé : {output_dir}")
    print(f"Seuil utilisé       : {threshold * 1000:.1f} ms")
    print(f"Paires conservées   : {synced_count}")


def synchronize_offline_GPS_IMU(raw_acquisition_dir, threshold=0.10, suffix="_synced"):
    """
    Calcule les paires GPS/IMU synchronisées à partir d'une acquisition brute
    et les enregistre dans un nouveau dossier.

    Parameters
    ----------
    raw_acquisition_dir : str | Path
        Dossier de l'acquisition brute.
    threshold : float
        Seuil maximal |t_cam - t_lidar| en secondes.
    suffix : str
        Suffixe ajouté au nom du dossier de sortie.
    """
    raw_acquisition_dir = Path(raw_acquisition_dir)

    # Lecture des fichiers timestamps de la caméra et du LiDAR
    gps_csv = raw_acquisition_dir / "gps_scan.csv"
    imu_csv = raw_acquisition_dir / "imu_scan.csv"

    if not gps_csv.exists():
        raise FileNotFoundError(f"Fichier absent : {gps_csv}")
    if not imu_csv.exists():
        raise FileNotFoundError(f"Fichier absent : {imu_csv}")

    gps_entries = read_timestamp_gps_csv(gps_csv)
    imu_entries = read_timestamp_imu_csv(imu_csv)

    if not gps_entries:
        raise RuntimeError("Aucune scan trouvée dans gps_scan.csv")
    if not imu_entries:
        raise RuntimeError("Aucun scan trouvé dans imu_scan.csv")

    print("Données GPS : [")
    for f in gps_entries:
        print(f)
    print(']')
    print("Données IMU : [")
    for s in imu_entries:
        print(s)
    print(']')
    
    # Création du dossier d'acquisition syncrhonisée
    output_dir = create_output_directory(raw_acquisition_dir, None, None, suffix=suffix)

    # Création du fichier CSV indiquant les appariements réalisés
    synced_csv_path = output_dir / "synced_gps_imu.csv"
    synced_csv = CSVHandler(str(synced_csv_path))

    synced_csv.create_csv_with_header([
        "t_gps",
        "t_imu",
        "dt_s",
        "latitude",
        "longitude",
        "altitude",
        "accel x",
        "accel y",
        "accel z",
        "gyro x",
        "gyro y",
        "gyro z"
    ])

    synced_count = 0
    used_imu_indices = set()
    imu_timestamps = np.array([e["timestamp"] for e in imu_entries])

    for gps_id, gps_entry in enumerate(gps_entries):
        # Récupération du timestamp du gps
        timestamp_gps = gps_entry["timestamp"]

        # Recherche du imu avec le timestamp le plus proche
        best_imu_indice = np.argmin(np.abs(imu_timestamps - timestamp_gps))
        best_timestamp = imu_timestamps[best_imu_indice]

        # Récupération du timestamp du imu le plus proche temporellement
        # Calcul de la dimu_csv = fférence absolue entre les deux timestamps
        diff = abs(best_timestamp-timestamp_gps)

        # Sélection de la paire si la différence de temps est inférieure à un seuil prédéfini
        if diff > threshold: # Condition pour éliminer une paire
            continue

        # Récupération de l'index du imu le plus proche (dans le dossier d'acquisition)
        # Sélection de la paire si le imu appairé n'a pas déjà été précédemment utilisé
        if best_imu_indice in used_imu_indices: # Condition pour éliminer une paire
            continue

        # Ajout de l'identifiant du imu dans le set des imu déjà utilisés
        used_imu_indices.add(best_imu_indice)
        imu_entry = imu_entries[best_imu_indice]

        # Ecriture de la paire dans le fichier d'appariement CSV
        synced_csv.append_row([timestamp_gps, best_timestamp, diff,
                               gps_entry["latitude"], gps_entry["longitude"], gps_entry["altitude"],
                               imu_entry["accel_x"], imu_entry["accel_y"], imu_entry["accel_z"],
                               imu_entry["gyro_x"], imu_entry["gyro_y"], imu_entry["gyro_z"]])

        synced_count += 1

    print(f"Dossier brut        : {raw_acquisition_dir}")
    print(f"Dossier synchronisé : {output_dir}")
    print(f"Seuil utilisé       : {threshold * 1000:.1f} ms")
    print(f"Paires conservées   : {synced_count}")


def main(raw_acquisition_dir, threshold, suffix):
    synchronize_offline_GPS_IMU(
        raw_acquisition_dir=raw_acquisition_dir,
        threshold=threshold,
        suffix=suffix,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Synchronisation offline IMU/GPS à partir d'une acquisition brute."
    )

    parser.add_argument(
        "raw_acquisition_dir",
        type=str,
        help="Dossier de l'acquisition brute."
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=0.10,
        help="Seuil maximal |t_cam - t_lidar| en secondes (défaut: 0.10)."
    )

    parser.add_argument(
        "--suffix",
        type=str,
        default="_synced",
        help="Suffixe du dossier de sortie (défaut: _synced)."
    )

    args = parser.parse_args()

    main(
        raw_acquisition_dir=args.raw_acquisition_dir,
        threshold=args.threshold,
        suffix=args.suffix,
    )