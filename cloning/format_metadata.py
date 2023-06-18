import argparse
from utils import multilingual_cleaners


def format_local(filepath, save_name):
    if not save_name:
        save_name = filepath.replace(".txt", "_formatted.txt")
    with open(filepath, "r", encoding='utf8') as f:
        with open(save_name, "w",encoding='utf8') as f2:
            for index, line in enumerate(f):
                #Line must end in "." and "\n" to be a valid line:
                cleaned_line = multilingual_cleaners(line)
                f2.write('{0}|{1}|{2}\n'.format(str(index+1), line if not line.endswith("\n") else line[:-1], cleaned_line))

def format_vits(filepath, save_name):
    if not save_name:
        save_name = filepath.replace(".txt", "_vits.txt")
    with open(filepath, "r", encoding='utf8') as f:
        with open(save_name , "w",encoding='utf8') as fn:
                for index, line in enumerate(f):
                    cleaned_line = multilingual_cleaners(line)
                    fn.write('{0}|{1}|{2}\n'.format(str(index+1), line if not line.endswith("\n") else line[:-1], cleaned_line))


def format_tacotron2(filepath, save_name):
    if not save_name:
        save_name = filepath.replace(".txt", "_tacotron2.txt")
    with open(filepath, "r", encoding='utf8') as f:
        with open(save_name , "w",encoding='utf8') as fn:
                for index, line in enumerate(f):
                    cleaned_line = multilingual_cleaners(line)
                    fn.write('/content/tacotron2/wavs/{0}.wav|{1}\n'.format(str(index+1), cleaned_line))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script to format metadata file')
    parser.add_argument('-f','--filepath', type=str, default=None, help='Path to the metadata file', required=True)
    parser.add_argument('-s','--save_name', type=str, default=None, help='Name of the output file. If not provided, "_formatted", "_vits", or "_tacotron2" will be added to the original filename')
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('-t','--tacotron_format', action='store_true', help='If true, the output file will be in the format required by the tacotron2 notebook')
    group.add_argument('-v','--vits_format', action='store_true', help='If true, the output file will be in the format required by the vits notebook')
    args = parser.parse_args()
    if args.tacotron_format:
        format_tacotron2(args.filepath, args.save_name)
    elif args.vits_format:
        format_vits(args.filepath, args.save_name)
    else:
        format_local(args.filepath, args.save_name)
