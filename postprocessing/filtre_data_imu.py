import pandas as pd
import os

def filter_imu_data(source_file, out_file, size = 5) :
    #chercher le fichier existanto ou non
    file = pd.read_csv(source_file)

    #récupèrer les colonnes à filtrer
    cols = [c for c in file.columns if 'acc' in c.lower() or 'gyro' in c.lower()]
    #filtrer
    for col in cols :
        file[col] = file[col].rolling(window=5, center=True).median()

    #remplacement des bords -> NaN
    file = file.ffill().bfill()
    #sortir le nouveau fichier
    file.to_csv(out_file, index=False)