import argparse
import re
import subprocess
import os
import datetime
import torch
import statistics

from __init__ import normalize_audio, read_json, multilingual_cleaners
try:
    from tqdm import tqdm
except ImportError:
    print("Tqdm not found, install it for progress bars")
    tqdm = lambda x: x

def main(filepath, name_run, language):
    #Check if filename is a folder
    if os.path.isdir(filepath):
        #Check if folder contains audio files
        if len(os.listdir(filepath)) == 0:
            raise Exception("The folder {0} is empty. Please check the path and try again.".format(filepath))
        #Check there is at least one wav file in the folder
        if not any([filename.endswith(".wav") for filename in os.listdir(filepath)]):
            raise Exception("The folder {0} does not contain any wav files. Please check the path and try again.".format(filepath))
        with open(os.path.join(filepath, "list_of_audio_files.txt"), "w") as f:
            for filename in os.listdir(filepath):
                if filename.endswith(".wav"):
                    f.write("file '" + os.path.join(filepath, filename)+"'\n")
        #Create the joined audio file:
        subprocess.run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", os.path.join(filepath, "list_of_audio_files.txt"), "-c", "copy", os.path.join(filepath, "joined_audio.wav"), "-y", "-loglevel", "error", "-hide_banner"])
        #Set filepath to the joined audio file
        filepath = os.path.join(filepath, "joined_audio.wav")
    #Check that the audio file exists
    original_filename = filepath.split("\\")[-1]
    if not os.path.exists(filepath):
        raise Exception("The file {0} does not exist. Please check the path and try again.".format(filepath))
    
    #Create a folder to store the audio clips and the transcription
    tmp_name = filepath.replace(".wav", "") if name_run == "run" else name_run
    out_folder = tmp_name + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    if not os.path.exists(out_folder):
        os.makedirs(os.path.join(out_folder, "wavs"))
    
    #Get audio file duration
    #Transcribe the audio file using OpenAI Whisper
    print("Transcribing audio file...")
    subprocess.run(["whisper", filepath,"--model", "medium" ,"--language", language, "--word_timestamps", "True" ,"--output_format", "json", "--output_dir", out_folder])

    results = read_json(os.path.join(out_folder, original_filename.replace(".wav", ".json")))
    results = remove_end_hallucinations(results)
    
    #Cut original audio file into clips using the custom segments
    print("Cutting audio file into clips...")
    cut_audio_and_generate_metadata(out_folder, filepath, results["segments"])
    print("Done! Check the folder {0} for the audio clips and the metadata file.".format(out_folder))



def cut_audio_and_generate_metadata(out_folder: str, audio_path: str, segments) -> None:
    with open(os.path.join(out_folder, "metadata.txt"), "w", encoding='utf8') as f:
        index = 1
        for segment in tqdm(segments):
            start = segment["start"]
            end = segment["end"]
            outfile = os.path.join(out_folder, "wavs", str(index) + ".wav")
            subprocess.run(['ffmpeg', '-i', audio_path, '-ss', str(start), '-to', str(end), outfile, '-loglevel', 'error', '-y', '-hide_banner', ])
            #Normalize audio file
            normalize_audio(outfile)
            cleaned_text = multilingual_cleaners(segment["text"])
            #Make sure cleaned_text ends with a period or comma (add it if it doesn't)
            cleaned_text = cleaned_text if cleaned_text[-1] in [".", ","] else cleaned_text + "."
            f.write('/content/tacotron2/wavs/{0}.wav|{1}\n'.format(str(index), cleaned_text))
            index +=1



#TODO: could modify easily by iterating over copy of results and discard each segment that is a hallucination
def remove_end_hallucinations(results): #https://github.com/openai/whisper/discussions/928
    hallucinations_file = set(read_json(os.path.abspath("hallucination_sentences.json"))['hallucinations'])
    if results["segments"][len(results["segments"])-1]["text"] in hallucinations_file:
        del results["segments"][len(results["segments"])-1]
    return results

def force_cudnn_initialization():
    s = 32
    dev = torch.device('cuda')
    torch.nn.functional.conv2d(torch.zeros(s, s, s, s, device=dev), torch.zeros(s, s, s, s, device=dev))



if __name__ == "__main__":
    argparse = argparse.ArgumentParser(description='Script to transcribe and cut long audio files into short clips using OpenAI Whisper and ffmpeg.')
    argparse.add_argument('-f','--filepath', type=str, default=None, required=True, help='Path to the audio file, or folder if multiple files.')
    argparse.add_argument('-l', '--language', type=str, default="es", required=False, help='Language of the audio file. Default is Spanish (es). English not supported yet.')
    argparse.add_argument('-n', '--name_run', type=str, default="run", required=False, help='Name of the run. Default is filename+timestamp. This will be name of the output folder together'
                        +'with the date and time of the run.')
    args = argparse.parse_args()
    #Check that args.filepath file name doesnt contain any spaces or special characters using regex
    filename = args.filepath.split("\\")[-1]
    if re.search(r'[^A-Za-z0-9_\.]+', filename):
        raise Exception("File name contains special characters or spaces. Please rename the file and try again.")
    if not os.path.isabs(args.filepath):
        args.filepath = os.path.abspath(args.filepath)
    force_cudnn_initialization() #Trick to avoid CUDNN_STATUS_NOT_INITIALIZED error when running Whisper
    main(args.filepath, args.language, args.name_run)
