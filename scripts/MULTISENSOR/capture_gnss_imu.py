import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import time
import shutil
import argparse
import traceback
import threading
from pathlib import Path

from sensors.GNSS import GNSS
from sensors.IMU import read_IMU, initialize_sensors
from utils import Button, LED, create_acquisition_directory, CSVHandler
from config import (
    PORT_BUTTON,
    PORT_LED,
    ACQUISITION_ROOT,
    GNSS_DEVICE_ADDR,
    LSM6DSO_ADDR,
    LIS3MDL_ADDR,
    ACCEL_RANGE,
    ACCEL_FREQ,
    GYRO_RANGE,
    GYRO_FREQ,
    MAGNETO_RANGE,
    MAGNETO_FREQ,
)


ACQUISITION_PATH = Path(ACQUISITION_ROOT)
GNSS_BUS = 1  # Bus I2C standard pour Raspberry Pi


def start_acquisition(state, led, calibration=False, session_dir=None):
    """
    Lance une acquisition multicapteur GPS/IMU :
    - création du dossier session si nécessaire
    - création des CSV de timestamps pour GPS et IMU
    """
    if session_dir is None:
        session_dir, subdirs = create_acquisition_directory(
            root_dir=ACQUISITION_ROOT,
            prefix="acquisition",
            subdirs=["data"]
        )
        global acquisition_dir
        acquisition_dir = session_dir
    else:
        subdirs = {"data": session_dir / "data"}
        subdirs["data"].mkdir(parents=True, exist_ok=True)

    state["is_acquiring"] = True
    state["session_dir"] = session_dir
    state["data_dir"] = subdirs["data"]
    state["gps_index"] = 0
    state["imu_index"] = 0

    # Copie du fichier config/parameters.py dans le dossier d'acquisition si nécessaire
    params_target = state["session_dir"] / "parameters.py"
    if not params_target.exists():
        shutil.copyfile("config/parameters.py", str(params_target))

    # Création des fichiers CSV pour GPS et IMU
    # GPS: timestamp, UTC, latitude, longitude, altitude
    if calibration:
        csv_file_gps = CSVHandler(str(state["session_dir"] / "calibration_gps_scan.csv"))
    else:
        csv_file_gps = CSVHandler(str(state["session_dir"] / "gps_scan.csv"))
    csv_file_gps.create_csv_with_header(["Timestamp", "UTC", "Latitude", "Longitude", "Altitude"])

    # IMU: timestamp, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, magneto_x, magneto_y, magneto_z
    if calibration:
        csv_file_imu = CSVHandler(str(state["session_dir"] / "calibration_imu_scan.csv"))
    else:
        csv_file_imu = CSVHandler(str(state["session_dir"] / "imu_scan.csv"))
    csv_file_imu.create_csv_with_header([
        "Timestamp", "Accel X", "Accel Y", "Accel Z",
        "Gyro X", "Gyro Y", "Gyro Z",
        "Magneto X", "Magneto Y", "Magneto Z"
    ])

    # Ajout des CSVHandlers créés dans state (pour y accéder en dehors de la fonction)
    state["csv_gps"] = csv_file_gps
    state["csv_imu"] = csv_file_imu

    if calibration == False:
        led.on()
    print(f"Acquisition démarrée : {session_dir}")


def stop_acquisition(state, led, reason=None, clear_session=True):
    """
    Arrête l'acquisition en cours et remet l'état session à zéro.
    """
    if reason is not None:
        print(f"Acquisition interrompue : {reason}")
    elif state["session_dir"] is not None:
        print(f"Acquisition arrêtée : {state['session_dir']}")

    state["is_acquiring"] = False
    state["csv_gps"] = None
    state["csv_imu"] = None
    state["gps_index"] = 0
    state["imu_index"] = 0

    if clear_session:
        state["session_dir"] = None
        state["data_dir"] = None

    led.off()


def toggle_acquisition(state, led, lock):
    """
    Démarre ou arrête une acquisition.
    """
    with lock:
        if not state["is_acquiring"]:
            start_acquisition(state, led)
        else:
            stop_acquisition(state, led)


def gnss_worker(gnss, state, lock, stop_event):
    """
    Thread d'acquisition GNSS/GPS.
    """
    while not stop_event.is_set():
        try:
            # Lecture des données GPS
            gnss.update()
            
            timestamp = time.time()

            with lock:
                if state["is_acquiring"] and gnss.reception_ok:
                    # Enregistrement des données GPS
                    utc_str = str(gnss.utc)
                    latitude = gnss.latitude.coordinates_DD
                    longitude = gnss.longitude.coordinates_DD
                    altitude = gnss.altitude

                    # Mise à jour du fichier CSV GPS
                    state["csv_gps"].append_row([
                        timestamp,
                        utc_str,
                        latitude,
                        longitude,
                        altitude
                    ])
                    state["gps_index"] += 1

        except Exception as error:
            traceback.print_exc()
            with lock:
                state["is_acquiring"] = False
                state["session_dir"] = None
                state["data_dir"] = None
                state["gps_index"] = 0
                state["imu_index"] = 0
                state["csv_gps"] = None
                state["csv_imu"] = None
            time.sleep(0.1)

        time.sleep(0.01)


def imu_worker(state, lock, stop_event):
    """
    Thread d'acquisition IMU.
    """
    while not stop_event.is_set():
        try:
            # Lecture des données IMU
            accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, magneto_x, magneto_y, magneto_z = read_IMU(
                LSM6DSO_ADDR,
                LIS3MDL_ADDR,
                ACCEL_RANGE,
                GYRO_RANGE,
                MAGNETO_RANGE
            )
            
            timestamp = time.time()

            with lock:
                if state["is_acquiring"]:
                    # Enregistrement des données IMU
                    state["csv_imu"].append_row([
                        timestamp,
                        accel_x,
                        accel_y,
                        accel_z,
                        gyro_x,
                        gyro_y,
                        gyro_z,
                        magneto_x,
                        magneto_y,
                        magneto_z
                    ])
                    state["imu_index"] += 1

        except Exception as error:
            traceback.print_exc()
            with lock:
                state["is_acquiring"] = False
                state["session_dir"] = None
                state["data_dir"] = None
                state["gps_index"] = 0
                state["imu_index"] = 0
                state["csv_gps"] = None
                state["csv_imu"] = None
            time.sleep(0.1)

        time.sleep(0.01)

def initialisation_capteurs():
    print("Initialisation du GNSS...")
    # Initialisation du GNSS
    gnss = GNSS(GNSS_BUS, GNSS_DEVICE_ADDR)
    gnss.initialisation(1)  # Mode GPS
    gnss.enable_power()
    
    print("Initialisation de l'IMU...")
    # Initialisation de l'IMU
    initialize_sensors(
        LSM6DSO_ADDR,
        LIS3MDL_ADDR,
        ACCEL_RANGE,
        ACCEL_FREQ,
        GYRO_RANGE,
        GYRO_FREQ,
        MAGNETO_RANGE,
        MAGNETO_FREQ
    )

    print("Initialisation du bouton et de la LED...")
    button = Button(PORT_BUTTON)
    led = LED(PORT_LED)

    return gnss, button, led

def acquisition_multisensor(mode = "normal"):
    """
    Fonction d'acquisition multisenseur GPS/IMU.
    - mode normal : démarre une acquisition au premier appui sur le bouton, et l'arrête au second appui.
    - mode calibration : démarre une acquisition au premier appui sur le bouton, et l'arrête automatiquement après 5 secondes (utile pour les acquisitions de calibration).
    - mode trajectoire : démarre une calibration au premier appuie, puis une acquisition automatiquement, et l'arrête au premier appui.
    """
    # Initialisation des capteurs
    gnss, button, led = initialisation_capteurs()

    ACQUISITION_PATH.mkdir(parents=True, exist_ok=True)

    state = {
        "is_acquiring": False,
        "session_dir": None,
        "data_dir": None,
        "gps_index": 0,
        "imu_index": 0,
        "csv_gps": None,
        "csv_imu": None,
    }

    lock = threading.Lock()
    stop_event = threading.Event()

    gnss_thread = threading.Thread(
        target=gnss_worker,
        args=(gnss, state, lock, stop_event),
        daemon=True
    )

    imu_thread = threading.Thread(
        target=imu_worker,
        args=(state, lock, stop_event),
        daemon=True
    )

    if mode == "normal":
        print("Appuyer sur le bouton pour démarrer / arrêter l'acquisition GPS/IMU.")
        print("Ctrl+C pour quitter.")

    try:
        gnss_thread.start()
        imu_thread.start()

        if mode == "normal":
            while True:
                if button.is_pressed():
                    toggle_acquisition(state, led, lock)
                    button.wait_for_release()
                    time.sleep(0.05)

                time.sleep(0.05)
        elif mode == "calibration": # DEPRECIE: ne s'utilise plus avec l'ajout du magnétomètre
            while not button.is_pressed():
                time.sleep(0.05)
            button.wait_for_release()

            start_acquisition(state, led, calibration=True)

            time.sleep(10)

            stop_acquisition(state, led, reason="Fin de l'acquisition de calibration.", clear_session=False)

        elif mode == "trajectoire":
            print("Appuyez sur le bouton puis faites des 8 avec le magnétomètre pendant 10 secondes afin de le calibrer.")
            while not button.is_pressed():
                time.sleep(0.05)
            button.wait_for_release()
            
            start_acquisition(state, led, calibration=True)
            time.sleep(10)

            stop_acquisition(state, led, reason="Calibration terminée. Démarrage de l'acquisition de trajectoire.", clear_session=False)

            start_acquisition(state, led, calibration=False, session_dir=state["session_dir"])

            print("Acquisition trajectoire démarrée. Appuyez sur le bouton pour arrêter.")
            while not button.is_pressed():
                time.sleep(0.05)
            button.wait_for_release()

            stop_acquisition(state, led, reason="Fin de l'acquisition de trajectoire.")

    except KeyboardInterrupt:
        print("\nArrêt du programme demandé par l'utilisateur.")

    finally:
        stop_event.set()

        gnss_thread.join(timeout=1.0)
        imu_thread.join(timeout=1.0)

        led.off()
        button.cleanup()
        led.cleanup()
        gnss.disable_power()

        print("Ressources libérées.")
    
    return acquisition_dir


def main(mode="normal"):
    acquisition_multisensor(mode=mode)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Acquisition multisenseur GPS/IMU."
    )

    parser.add_argument(
        "mode",
        type=str,
        choices=["normal", "calibration", "trajectoire"],
        help="Mode d'acquisition. - normal : démarre une acquisition au premier appui sur le bouton, et l'arrête au second appui. \
            - calibration : démarre une acquisition au premier appui sur le bouton, et l'arrête automatiquement après 10 secondes. \
                - trajectoire : réalise l'acquisition de la calibration, puis directement l'acquistio de la trajectoire."
    )

    args = parser.parse_args()

    _ = main(
            mode = args.mode
        )
