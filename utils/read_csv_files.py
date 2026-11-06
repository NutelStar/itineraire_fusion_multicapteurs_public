from pathlib import Path
import sys

# Add project root to path so utils can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import CSVHandler

def read_gps_csv(csv_path):
    """
    Lit un CSV des données GPS.
    """
    rows = CSVHandler(str(csv_path)).read_dict_rows()
    entries = []

    for row in rows:
        try:
            keys = list(row.keys())
            if len(keys) < 2:
                continue

            timestamp = float(row[keys[0]])
            latitude = float(row[keys[2]])
            longitude = float(row[keys[3]])
            altitude = float(row[keys[4]])

            entries.append({
                "timestamp": timestamp,
                "latitude": latitude,
                "longitude": longitude,
                "altitude": altitude
            })

        except (ValueError, TypeError):
            continue
    return entries

def read_processed_gps_csv(csv_path):
    """
    Lit un CSV des données GPS traitées.
    """
    rows = CSVHandler(str(csv_path)).read_dict_rows()
    entries = []

    for row in rows:
        try:
            keys = list(row.keys())
            if len(keys) < 2:
                continue

            timestamp = float(row[keys[0]])
            latitude = float(row[keys[1]])
            longitude = float(row[keys[2]])
            altitude = float(row[keys[3]])

            entries.append({
                "timestamp": timestamp,
                "latitude": latitude,
                "longitude": longitude,
                "altitude": altitude
            })

        except (ValueError, TypeError):
            continue
    return entries

def read_imu_csv(csv_path):
    """
    Lit un CSV des données IMU.
    """
    rows = CSVHandler(str(csv_path)).read_dict_rows()
    entries = []

    for row in rows:
        try:
            keys = list(row.keys())
            if len(keys) < 2:
                continue

            timestamp = float(row[keys[0]])
            accel_x = float(row[keys[1]])
            accel_y = float(row[keys[2]])
            accel_z = float(row[keys[3]])
            gyro_x = float(row[keys[4]])
            gyro_y = float(row[keys[5]])
            gyro_z = float(row[keys[6]])

            if len(row) >= 7:
                magneto_x = float(row[keys[7]])
                magneto_y = float(row[keys[8]])
                magneto_z = float(row[keys[9]])

            if len(row) > 7:
                entry = {
                "timestamp": timestamp,
                "accel_x": accel_x,
                "accel_y": accel_y,
                "accel_z": accel_z,
                "gyro_x": gyro_x,
                "gyro_y": gyro_y,
                "gyro_z": gyro_z,
                "magneto_x": magneto_x,
                "magneto_y": magneto_y,
                "magneto_z": magneto_z
            }
            else:
                entry = {
                    "timestamp": timestamp,
                    "accel_x": accel_x,
                    "accel_y": accel_y,
                    "accel_z": accel_z,
                    "gyro_x": gyro_x,
                    "gyro_y": gyro_y,
                    "gyro_z": gyro_z
                }
            
            entries.append(entry)

        except (ValueError, TypeError):
            continue
    return entries

def read_kalman_csv(csv_path):
    """
    Lit un CSV des données du filtre de Kalman.
    """
    rows = CSVHandler(str(csv_path)).read_dict_rows()
    entries = []

    for row in rows:
        try:
            keys = list(row.keys())
            if len(keys) < 2:
                continue

            t = float(row[keys[0]])
            x = float(row[keys[1]])
            y = float(row[keys[2]])

            entry = {
                "t": t,
                "x": x,
                "y": y,
            }

            entries.append(entry)

        except (ValueError, TypeError):
            continue
    return entries