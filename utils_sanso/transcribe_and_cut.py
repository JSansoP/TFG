import argparse
import re
import subprocess
import os
import datetime
import pandas as pd
import ffmpeg
from TTS.TTS.utils.text.cleaners import multilingual_cleaners
import time
import torch

def main(args):
    #Check that the audio file exists
    original_filename = args.filepath.split("\\")[-1]
    if not os.path.exists(args.filepath):
        raise Exception("The file {0} does not exist. Please check the path and try again.".format(args.filepath))
    
    #Create a folder to store the audio clips and the transcription
    tmp_name = args.filepath.replace(".wav", "") if args.name_run == "run" else args.name_run
    out_folder = tmp_name + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    if not os.path.exists(out_folder):
        os.makedirs(os.path.join(out_folder, "wavs"))
    
    #Get audio file duration
    duration = ffmpeg.probe(args.filepath)['format']['duration']
    #Transcribe the audio file using OpenAI Whisper
    print("Transcribing audio file...")
    print("The duration of the file is {0} seconds, so expect at least a wait of that time.".format(duration))
    time.sleep(1) #Wait 1 second to avoid bad allocation error
    subprocess.run(["whisper", args.filepath,"--model", "medium" ,"--language", args.language, "--output_format", "tsv", "--output_dir", out_folder, "--temperature", "0.1"])

    #Transform audio file into mono, 16 bit 22050 Hz wav file
    print("Transforming audio file into mono, 16 bit 22050 Hz wav file...")
    transformed_audio_path = transform_audio_file(args.filepath, out_folder)

    #Cut the audio file into clips using the transcription
    print("Cutting audio file into clips...")
    cut_audio_and_generate_metadata(out_folder, transformed_audio_path, original_filename.replace(".wav", ".tsv"))




def cut_audio_and_generate_metadata(out_folder: str, transformed_audio_path: str, transcription_file) -> None:
    df = pd.read_csv(os.path.join(out_folder, transcription_file), sep="\t", header=0)
    with open(os.path.join(out_folder, "metadata.txt"), "w", encoding='utf8') as f:
        for index, row in df.iterrows():
            start_ms = row["start"]
            end_ms = row["end"]
            stream = ffmpeg.input(transformed_audio_path)
            stream = ffmpeg.output(stream, os.path.join(out_folder, "wavs", str(index+1) + ".wav"), ss=start_ms/1000, to=end_ms/1000)
            ffmpeg.run(stream)
            cleaned_text = multilingual_cleaners(row["text"])
            f.write('/content/tacotron2/wavs/{0}.wav|{1}\n'.format(str(index+1), cleaned_text))


def transform_audio_file(filepath: str, out_folder: str) -> str:
    #Transform audio file into mono, 16 bit 22050 Hz wav file
    transformed_audio_path = os.path.join(out_folder, "transformed_audio.wav")
    stream = ffmpeg.input(filepath)
    stream = ffmpeg.output(stream, transformed_audio_path, ac=1, ar=22050, acodec="pcm_s16le")
    ffmpeg.run(stream)
    return transformed_audio_path


def force_cudnn_initialization():
    s = 32
    dev = torch.device('cuda')
    torch.nn.functional.conv2d(torch.zeros(s, s, s, s, device=dev), torch.zeros(s, s, s, s, device=dev))



if __name__ == "__main__":
    argparse = argparse.ArgumentParser(description='Script to transcribe and cut long audio files into short clips using OpenAI Whisper and ffmpeg.')
    argparse.add_argument('-f','--filepath', type=str, default=None, required=True, help='Path to the audio file')
    argparse.add_argument('-l', '--language', type=str, default="es", required=False, help='Language of the audio file. Default is Spanish (es). English not supported yet.')
    argparse.add_argument('-n', '--name_run', type=str, default="run", required=False, help='Name of the run. Default is "run". This will be name of the output folder together'
                        +'with the date and time of the run.')
    args = argparse.parse_args()
    #Check that args.filepath file name doesnt contain any spaces or special characters using regex
    filename = args.filepath.split("\\")[-1]
    if re.search(r'[^A-Za-z0-9_\.]+', filename):
        raise Exception("File name contains special characters or spaces. Please rename the file and try again.")
    force_cudnn_initialization() #Trick to avoid CUDNN_STATUS_NOT_INITIALIZED error when running Whisper
    main(args)