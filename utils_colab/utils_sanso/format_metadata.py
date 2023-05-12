import sys
import os
import argparse
from TTS.TTS.utils.text.cleaners import multilingual_cleaners

def format_local(filepath, save_name):
    if not save_name:
        save_name = filepath.replace(".txt", "_formatted.txt")
    with open(filepath, "r", encoding='utf8') as f:
        with open(save_name, "w",encoding='utf8') as f2:
            for index, line in enumerate(f):
                #Line must end in "." and "\n" to be a valid line:
                cleaned_line = multilingual_cleaners(line)
                f2.write('{0}|{1}|{2}\n'.format(str(index+1), line if not line.endswith("\n") else line[:-1], cleaned_line))

def format_notebook(filepath, save_name):
    if not save_name:
        save_name = filepath.replace(".txt", "_notebook.txt")
    with open(filepath, "r", encoding='utf8') as f:
        with open(save_name , "w",encoding='utf8') as fn:
                for index, line in enumerate(f):
                    cleaned_line = multilingual_cleaners(line)
                    fn.write('/content/tacotron2/wavs/{0}.wav|{1}\n'.format(str(index+1), cleaned_line))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script to format metadata file')
    parser.add_argument('-f','--filepath', type=str, default=None, help='Path to the metadata file', required=True)
    parser.add_argument('-n','--notebook_format', action='store_true', help='If true, the output file will be in the format required by the notebook')
    parser.add_argument('-s','--save_name', type=str, default=None, help='Name of the output file. If not provided, "_formatted" or "_notebook" will be added to the original filename')
    args = parser.parse_args()
    if args.notebook_format:
        format_notebook(args.filepath, args.save_name)
    else:
        format_local(args.filepath, args.save_name)
