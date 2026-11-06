import argparse
import csv
import numpy as np
import pandas as pd

def main(csv_file):
    df = pd.read_csv(csv_file, delimiter=',')
    df = df.to_numpy()
    np.savez('npz_file', data=df)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Conversion d'un fichier csv en npz."
    )

    parser.add_argument(
        "csv_file",
        type=str,
        help="Fichier csv."
    )

    args = parser.parse_args()

    main(
        args.csv_file,
    )