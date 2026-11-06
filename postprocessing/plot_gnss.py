import argparse
import pandas as pd
import folium
import os
from utils.path import Path
from utils.read_csv_files import read_gps_csv, read_kalman_csv, read_processed_gps_csv

from postprocessing.changement_base import cartesian_to_gps

def plot_GNSS(file_path, output, mode = "kalman", strava = False):
    """
    Fonction pour tracer les données GNSS d'un parcours sur une carte OpenStreetMap, enregistrée dans un fichier HTML.
    
    Arguments:
    - file_path: Le chemin du fichier CSV contenant les données GNSS.
    """

    # Vérifie quel fichier de données lire
    acquisition_dir = Path(file_path)
    # Lire les données selon le mode
    if mode == "kalman":
        data = read_kalman_csv(acquisition_dir / "kalman_resultats.csv")

    data_base = read_processed_gps_csv(acquisition_dir / "processed_gps_scan.csv")
    if strava:
        data_strava = read_gps_csv(acquisition_dir / "strava_scan.csv")

    # Passage en coordonnées GPS si nécessaire
    if mode == "kalman":
        data_gps = read_gps_csv(acquisition_dir / "gps_scan.csv")

        latitude0 = data_gps[0]["latitude"]
        longitude0 = data_gps[0]["longitude"]
        altitude0 = data_gps[0]["altitude"]

        for i, scan in enumerate(data):
            latitude, longitude, altitude = cartesian_to_gps(float(scan["x"]), float(scan["y"]), 0, latitude0, longitude0, altitude0)
            data[i]["latitude"] = latitude
            data[i]["longitude"] = longitude
            data[i]["altitude"] = altitude

        for i, scan in enumerate(data_base):
            x_cartesian = float(scan["longitude"])
            y_cartesian = float(scan["latitude"])
            
            latitude, longitude, altitude = cartesian_to_gps(x_cartesian, y_cartesian, scan["altitude"], latitude0, longitude0, altitude0)
            
            data_base[i]["latitude"] = latitude
            data_base[i]["longitude"] = longitude
            data_base[i]["altitude"] = altitude

    m = folium.Map(location=[data[0]['latitude'], data[0]['longitude']], zoom_start=12)

    # On regroupe les éléments index par index pour faire des paires [lat, lon]
    # Trajectoire Kalman
    if mode == "kalman":
        lat_list = []
        lon_list = []
        for scan in data:
            lat_list.append(scan["latitude"])
            lon_list.append(scan["longitude"])

        points_kalman = list(zip(lat_list, lon_list))
        folium.PolyLine(points_kalman, color="blue", weight=2.5, opacity=1).add_to(m)

    # Trajectoire originale (GPS pure)
    lat_list = []
    lon_list = []
    for scan in data_base:
        lat_list.append(scan["latitude"])
        lon_list.append(scan["longitude"])
    points = list(zip(lat_list, lon_list))
    folium.PolyLine(points, color="red", weight=2.5, opacity=1).add_to(m)

    # Trajectoire Strava
    if strava:
        lat_list = []
        lon_list = []
        for scan in data_strava:
            lat_list.append(scan["latitude"])
            lon_list.append(scan["longitude"])
        points = list(zip(lat_list, lon_list))
        folium.PolyLine(points, color="yellow", weight=2.5, opacity=1).add_to(m)

    m.save(os.path.join(file_path, output + ".html"))
    print("Carte générée")

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument('acquisition_dir', type=str, help="Dossier d'acquisition.")

    parser.add_argument('output', type=str, help="Nom du fichier de sortie.")

    parser.add_argument(
        '--mode',
        type=str,
        choices=["kalman", "latitude"],
        default="kalman",
        help="- kalman: l'entrée utilise le fichier 'kalman_resultats.csv'. \
        - latitude: données GPS, pas de conversion."
    )

    parser.add_argument(
        '--strava',
        action='store_true',
        help="Ajouter la trajectoire contenue dans 'strava_scan.csv' si présente."
    )

    args = parser.parse_args()

    plot_GNSS(args.acquisition_dir, args.output, args.mode, args.strava)
