import sys
from pathlib import Path

# Adjust import path for parent package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import time
import argparse
import shutil
import traceback

from sensors.LIDAR import LIDAR
from utils import Button, LED, create_acquisition_directory, CSVHandler
from core.display import stream_scans
from config import (
    PORT_BUTTON,
    PORT_LED,
    ACQUISITION_ROOT,
    PORT_LIDAR,
    LIDAR_MIN_RANGE,
    LIDAR_MAX_RANGE,
    MIN_DETECTION_ANGLE,
    MAX_DETECTION_ANGLE,
    QUALITY_THRESHOLD,
    MIN_DETECTION_RANGE,
    MAX_DETECTION_RANGE,
)


ACQUISITION_PATH = Path(ACQUISITION_ROOT)


def start_acquisition(state, led):
    """
    Lance l'acquisition LiDAR.
    """
    session_dir, subdirs = create_acquisition_directory(
        root_dir=ACQUISITION_ROOT,
        prefix="acquisition",
        subdirs=["scans"]
    )

    state["is_acquiring"] = True
    state["session_dir"] = session_dir
    state["scans_dir"] = subdirs["scans"]
    state["scan_index"] = 0

    # A COMPLETER
    # Copie du fichier config/parameters.py dans le dossier d'acquisition
    shutil.copyfile("config/parameters.py", str(state["session_dir"] / "parameters.py"))
    
    # Création du fichier CSV timestamp/scans
    csv_file = CSVHandler(str(state["session_dir"] / "timestamps_scans.csv"))
    csv_file.create_csv_with_header(["timestamp", "scans"])
    
    # Ajout du CSVHandler créé dans state (pour y accéder en dehors de la fonction)
    state["csv_file"] = csv_file
    
    led.on()
    print(f"Acquisition démarrée : {session_dir}")


def stop_acquisition(state, led, reason=None):
    """
    Arrête l'acquisition en cours et remet l'état à zéro.
    """
    if reason is not None:
        print(f"Acquisition interrompue : {reason}")
    elif state["session_dir"] is not None:
        print(f"Acquisition arrêtée : {state['session_dir']}")

    state["is_acquiring"] = False
    state["session_dir"] = None
    state["scans_dir"] = None
    state["scan_index"] = 0
    state["csv_file"] = None

    led.off()


def toggle_acquisition(state, led):
    """
    Démarre ou arrête une acquisition de scans.
    """
    if not state["is_acquiring"]:
        start_acquisition(state, led)
    else:
        stop_acquisition(state, led)


def acquisition_scans(lidar, button, led, state):
    """
    Générateur de scans :
    - gère le bouton
    - démarre / arrête l'acquisition
    - lit un scan
    - sauvegarde si nécessaire
    """
    while True:
        if button.is_pressed():
            toggle_acquisition(state, led)
            button.wait_for_release()
            time.sleep(0.05)

        try:
            # A COMPLETER
            # Lecture d'une acquisition LiDAR
            timestamp, measures, points = lidar.read_scan()
            
            if state["is_acquiring"]:
                # A COMPLETER
                # Enregistrement de l'acquisition LiDAR
                lidar.save_scan_sequence(
                    scan=points, #!! a changer ??
                    directory=state["scans_dir"],
                    index=state["scan_index"]
                )

                

                # A COMPLETER
                # Mise à jour du fichier timestamp avec la nouvelle acquisition (timestamp et chemin du fichier)
                state["csv_file"].append_row([time.time(), f"scan_{state['scan_index']:06d}.csv"])
                
                
                
                state["scan_index"] += 1
                

        except Exception as error:
            traceback.print_exc()
            stop_acquisition(state, led, reason=repr(error))
            print("Le programme continue. Appuyez sur le bouton pour relancer une acquisition.")
            time.sleep(0.1)
            continue

        yield timestamp, measures, points
        time.sleep(0.01)


def make_extra_lines_callback(state):
    """
    Fabrique une fonction de callback pour afficher des informations
    dans l'overlay du stream LiDAR.
    """
    def extra_lines_callback(timestamp, scan, points):
        lines = []

        if state["is_acquiring"]:
            lines.append("ACQUISITION: ON")
            if state["session_dir"] is not None:
                lines.append(f"Session: {state['session_dir'].name}")
            lines.append(f"Scan index: {state['scan_index']}")
        else:
            lines.append("ACQUISITION: OFF")

        lines.append(f"Points: {len(points)}")
        lines.append("Appuyer sur le bouton pour start/stop")
        lines.append("Appuyer sur 'q' pour quitter")

        return lines

    return extra_lines_callback


def main(show_point_cloud=True):
    
    # A COMPLETER
    # Initialisation du LiDAR
    lidar = LIDAR(
        PORT_LIDAR,
        quality_threshold=QUALITY_THRESHOLD,
        min_range=MIN_DETECTION_RANGE,
        max_range=MAX_DETECTION_RANGE,
        min_angle=MIN_DETECTION_ANGLE,
        max_angle=MAX_DETECTION_ANGLE,
    )

    button = Button(PORT_BUTTON)
    led = LED(PORT_LED)

    ACQUISITION_PATH.mkdir(parents=True, exist_ok=True)

    state = {
        "is_acquiring": False,
        "session_dir": None,
        "scans_dir": None,
        "scan_index": 0,
        "csv_file": None,
    }

    print("Appuyer sur le bouton pour démarrer / arrêter l'acquisition de nuages de points.")
    print("Ctrl+C pour quitter.")

    try:
        print("Démarrage du LiDAR...")
        
        # A COMPLETER
        # Démarrage du LiDAR
        lidar.start()
        
        # Chauffe du LiDAR (warmup)
        lidar.warmup()

        stream_scans(
            acquisition_scans(lidar, button, led, state),
            min_range=LIDAR_MIN_RANGE,
            max_range=LIDAR_MAX_RANGE,
            extra_lines_callback=make_extra_lines_callback(state),
        )

    except KeyboardInterrupt:
        print("\nAcquisition interrompue par l'utilisateur.")

    finally:
        stop_acquisition(state, led)
        lidar.stop()
        print("Ressources libérées.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Acquisition de scans LiDAR avec démarrage/arrêt par bouton."
    )

    parser.add_argument(
        "--no-point-cloud",
        action="store_true",
        help="Désactive l'affichage du nuage de points."
    )

    args = parser.parse_args()

    main(show_point_cloud=not args.no_point_cloud)
