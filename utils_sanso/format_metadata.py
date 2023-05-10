import sys
import os
from TTS.TTS.utils.text.cleaners import multilingual_cleaners

def main(filepath):
    with open(filepath, "r", encoding='utf8') as f:
        with open(filepath + "dummy", "w",encoding='utf8') as f2:
            for index, line in enumerate(f):
                #Line must end in "." and "\n" to be a valid line:
                cleaned_line = multilingual_cleaners(line)
                f2.write('{0}|{1}|{2}\n'.format(str(index+1), line if not line.endswith("\n") else line[:-1], cleaned_line))
    #Delete original file and rename dummy file to original file:
    os.remove(filepath)
    os.rename(filepath + "dummy", filepath)

if __name__ == "__main__":
    main(sys.argv[1])
