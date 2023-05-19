import argparse
from utils import normalize_folder

#TODO: Add option to create a copy of the original folder and normalize the files in the copy
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script to normalize all wav files from folder')
    parser.add_argument('-f','--folderpath', type=str, default=None, help='Path to the folder containing the wav files', required=True)
    args = parser.parse_args()
    if args.folderpath:
        normalize_folder(args.folderpath, verbose)
    else:
        print("Please provide a folderpath")