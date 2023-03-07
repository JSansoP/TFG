import sys
import os
import pandas as pd
import subprocess
import json
import codecs
import unidecode

# TO RUN: python3 convert_tsv_to_manifest_es.py [train|dev]

def normalize_str(txt) -> str:
    valid_chars = (" ", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "'", "á", "é", "í", "ó", "ú", "ñ", "ü")
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
    for index, row in dt.iterrows():
      try:
        entry = {}
        os.system("mkdir -p wavs/{0}".format(prefix))
        mp3_file = "clips/" + row['path'] # + ".mp3"
        wav_file = "wavs/{0}/".format(prefix) + row['path'] + ".wav"
        subprocess.check_output("sox {0} -c 1 -r 16000 {1}".format(mp3_file, wav_file), shell=True)
        duration = subprocess.check_output(
          "soxi -D {0}".format(wav_file), shell=True)
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
  tsv_to_manifest([prefix + ".tsv"], prefix+".json", prefix)
  

if __name__ == "__main__":
    main()
