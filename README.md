# Itinéraire — fusion multi-capteurs

## Présentation

Ce projet regroupe deux fonctions :

- fusionner les données GPS et IMU pour estimer une trajectoire plus précise ;
- utiliser un LiDAR pour déclencher la caméra et détecter la présence d'une personne.

## Installation

Le projet est prévu pour une Raspberry Pi. Depuis la racine du dépôt, installez les dépendances système et créez un environnement virtuel :

```bash
sudo apt update
sudo apt install -y python3-numpy python3-opencv python3-simplejpeg python3-picamera2 libcamera-apps
python3 -m venv --system-site-packages ~/env_capteurs
source ~/env_capteurs/bin/activate
pip install numpy pandas pandas-stubs matplotlib folium evdev RPLCD scipy
```

Les paramètres des capteurs sont configurables dans le dossier `config/`.

## Utilisation

Les commandes suivantes sont à lancer depuis la racine du dépôt, avec l'environnement virtuel activé.

### Traitement d'une trajectoire

Pour effectuer l'acquisition puis traiter la trajectoire :

```bash
python3 Trajectoire.py
```

Pour traiter un dossier d'acquisition existant sans effectuer de nouvelle acquisition :

```bash
python3 Trajectoire.py --acquisition_folder data/acquisition_YYYYMMDD_HHMMSS
```

Le traitement produit les fichiers CSV pré-traités, le résultat du filtre de Kalman et deux cartes HTML dans le dossier d'acquisition.

### Acquisition GPS et IMU uniquement

```bash
python3 scripts/MULTISENSOR/capture_gnss_imu.py normal
```

Modes disponibles :

- `normal` : démarre et arrête l'acquisition à l'aide du bouton ;
- `calibration` : effectue une acquisition de calibration de 10 secondes ;
- `trajectoire` : effectue la calibration, puis l'acquisition de la trajectoire.

Les acquisitions sont enregistrées dans un nouveau dossier horodaté sous `data/`.

### Étapes de traitement séparées

Pour pré-traiter un dossier contenant `gps_scan.csv`, `imu_scan.csv` et `calibration_imu_scan.csv` :

```bash
python3 postprocessing/pre_traitement.py data/acquisition_YYYYMMDD_HHMMSS
```

Appliquez ensuite le filtre de Kalman :

```bash
python3 postprocessing/kalman_filter.py data/acquisition_YYYYMMDD_HHMMSS
```

Pour générer une carte à partir du résultat de Kalman :

```bash
python3 postprocessing/plot_gnss.py data/acquisition_YYYYMMDD_HHMMSS trajectoire --mode kalman
```

L'option `--strava` permet également d'afficher `strava_scan.csv`, si ce fichier est présent dans le dossier d'acquisition.