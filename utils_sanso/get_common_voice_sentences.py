import sys
import os
import argparse
import pandas as pd

def main(filepath, save_name):
    if not save_name:
        save_name = filepath.replace(".tsv", "_sentences.txt")
    df = pd.read_csv(filepath, sep='\t')
    with open(save_name, "w", encoding='utf8') as f:
        df.apply(lambda x: f.write(x["sentence"] + "\n"), axis=1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script to format metadata file')
    parser.add_argument('-f','--filepath', type=str, default=None, help='Path to the metadata file', required=True)
    parser.add_argument('-s','--save_name', type=str, default=None, help='Name of the output file. If not provided, "_formatted" or "_notebook" will be added to the original filename')
    args = parser.parse_args()
    main(args.filepath, args.save_name)
