import importlib.util
from pathlib import Path

def load_existing_calib(path="config/calib_offset.py"):
    config_path = Path(path)
    if not config_path.exists():
        return {}

    spec = importlib.util.spec_from_file_location("existing_calib", str(config_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    existing = {}
    if hasattr(module, "BIAIS_IMU"):
        existing["BIAIS_IMU"] = module.BIAIS_IMU
    if hasattr(module, "BRUIT_GPS"):
        existing["BRUIT_GPS"] = module.BRUIT_GPS
    if hasattr(module, "BRUIT_GYROSCOPE"):
        existing["BRUIT_GYROSCOPE"] = module.BRUIT_GYROSCOPE
    if hasattr(module, "BRUIT_VITESSE"):
        existing["BRUIT_VITESSE"] = module.BRUIT_VITESSE
    return existing


def save_calib_offset(biais_imu=None, biais_gps=None, path="config/calib_offset.py"):
    existing = load_existing_calib(path)
    if biais_imu is None:
        biais_imu = existing.get("BIAIS_IMU")

    with open(path, 'w', encoding='utf-8') as f:
        if biais_imu is not None:
            f.write("BIAIS_IMU = {\n")
            for axe, values in biais_imu.items():
                f.write(f"    '{axe}': {values},\n")
            f.write("}\n\n")

def save_calib_bruit(bruit_gps=None, bruit_gyroscope=None, bruit_vitesse=None, path="config/calib_bruit.py"):
    existing = load_existing_calib(path)
    if bruit_gps is None:
        bruit_gps = existing.get("BRUIT_GPS")
    if bruit_gyroscope is None:
        bruit_gyroscope = existing.get("BRUIT_GYROSCOPE")
    if bruit_vitesse is None:
        bruit_vitesse = existing.get("BRUIT_VITESSE")

    with open(path, 'w', encoding='utf-8') as f:
        if bruit_gps is not None:
            f.write("BRUIT_GPS = {\n")
            for axe, values in bruit_gps.items():
                f.write(f"    '{axe}': {values},\n")
            f.write("}\n\n")

        if bruit_gyroscope is not None:
            f.write("BRUIT_GYROSCOPE = {\n")
            for axe, values in bruit_gyroscope.items():
                f.write(f"    '{axe}': {values},\n")
            f.write("}\n\n")

        if bruit_vitesse is not None:
            f.write("BRUIT_VITESSE = {\n")
            for axe, values in bruit_vitesse.items():
                f.write(f"    '{axe}': {values},\n")
            f.write("}\n\n")