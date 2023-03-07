import sys
import os
import pandas as pd
import subprocess
import json
import codecs
import unidecode
from tqdm import tqdm

# TO RUN: 
# python tools\convert_tsvs_to_manifest_es.py validated "C:/Program Files (x86)/sox-14-4-2/sox.exe"

SOX_PATH = ""

def normalize_str(txt) -> str:
    valid_chars = (" ", "a", "b", "c", "ç", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "'", "á", "à", "é", "è", "í", "ó", "ò", "ú", "ñ", "ü", "ï")
    new_txt = txt.lower().strip()
    #new_txt = unidecode.unidecode(txt.lower().strip())
    res_arr = []
    for c in new_txt:
        if c in valid_chars:
            res_arr.append(c)
        else:
            # remove accent and see if it is valid
            non_accent_c = unidecode.unidecode(c)
            if non_accent_c in valid_chars:
                res_arr.append(non_accent_c)
            # a character we don't know
            else:
                res_arr.append(' ')
    res = ''.join(res_arr).strip()    
    return ' '.join(res.split())

def tsv_to_manifest(tsv_files, manifest_file, prefix):
  manifests = []
  for tsv_file in tsv_files:
    print('Processing: {0}'.format(tsv_file))
    dt = pd.read_csv(tsv_file, sep='\t', encoding='utf8')
    for index, row in tqdm(dt.iterrows(), total=dt.shape[0]):
      try:
        entry = {}
        if not os.path.exists("wavs/{0}".format(prefix)):
          os.mkdir("wavs/{0}".format(prefix))
        mp3_file = os.path.join(os.getcwd(),"clips",row['path'])
        #mp3_file = "clips/" + row['path'] # + ".mp3"
        #wav_file = "wavs/{0}/".format(prefix) + row['path'] + ".wav"
        wav_file = os.path.join(os.getcwd(),"wavs",prefix,row['path'] + ".wav")
        command = f'"{SOX_PATH}" {mp3_file} -c 1 -r 16000 {wav_file}'
        subprocess.run(command, shell=True)
        command = f'"{SOX_PATH}" --i -D {wav_file}'
        duration = subprocess.run(command, shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
        entry['audio_filepath'] = wav_file
        entry['duration'] = float(duration)
        entry['text'] = normalize_str(row['sentence'])
        manifests.append(entry)
      except:
        print("SOMETHING WENT WRONG - IGNORING ENTRY")

  with codecs.open(manifest_file, 'w', encoding='utf-8') as fout:
    for m in manifests:
      fout.write(json.dumps(m, ensure_ascii=False) + '\n')
  print('Done!')


def main():
  prefix = sys.argv[1]
  global SOX_PATH
  SOX_PATH = sys.argv[2]
  print("SOX_PATH: ", SOX_PATH)
  tsv_to_manifest([prefix + ".tsv"], prefix+".json", prefix)
  

if __name__ == "__main__":
    main()
