import argparse
import datetime
import os
import re
import subprocess
import shutil
import torch
from typing import List
from multiprocessing import Semaphore
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import multilingual_cleaners, normalize_audio, read_json, get_audio_length
from tqdm import tqdm


AUDIO_FILES_LIST = "list_of_audio_files.txt"
JOINED_AUDIO_FILE = "joined_audio.wav"


def main(filepath, name_run="run", language="es"):
    time = datetime.datetime.now()
    original_filepath = filepath
    # Check if filename is a folder
    if os.path.isdir(filepath):
        # Check if folder contains audio files
        if len(os.listdir(filepath)) == 0:
            raise Exception("The folder {0} is empty. Please check the path and try again.".format(filepath))
        # Check there is at least one wav file in the folder
        if not any([filename.endswith(".wav") for filename in os.listdir(filepath)]):
            raise Exception(
                "The folder {0} does not contain any wav files. Please check the path and try again.".format(filepath))
        os.mkdir(os.path.join(filepath, "TEMP"))
        # Normalize all the audio files in the folder
        print("Normalizing all the audio files in the folder {0}...".format(filepath))
        for filename in tqdm(os.listdir(filepath)):
            if filename.endswith(".wav") or filename.endswith(".WAV") \
                    and not filename.endswith(JOINED_AUDIO_FILE):
                shutil.copy(os.path.join(filepath, filename), os.path.join(filepath, "TEMP", filename))
                normalize_audio(os.path.join(filepath, "TEMP", filename))
        print("Joining normalised audio files into a single file...")
        with open(os.path.join(filepath, "TEMP", AUDIO_FILES_LIST), "w") as f:
            for filename in os.listdir(filepath):
                if filename.endswith(".wav") and not filename.endswith(JOINED_AUDIO_FILE):
                    f.write("file '" + os.path.join(filepath, filename) + "'\n")
        # Create the joined audio file:
        subprocess.run(
            ["ffmpeg", "-f", "concat", "-safe", "0", "-i", os.path.join(filepath, "TEMP", AUDIO_FILES_LIST), "-c",
             "copy", os.path.join(filepath, JOINED_AUDIO_FILE), "-y", "-loglevel", "error", "-hide_banner"])
        # Set filepath to the joined audio file
        shutil.rmtree(os.path.join(filepath, "TEMP"))
        filepath = os.path.join(filepath, JOINED_AUDIO_FILE)
    # Check that the audio file exists
    if not os.path.exists(filepath):
        raise Exception("The file {0} does not exist. Please check the path and try again.".format(filepath))

    # Create a folder to store the audio clips and the transcription
    tmp_name = filepath.replace(".wav", "") if name_run == "run" else name_run
    out_folder = tmp_name + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    if not os.path.exists(out_folder):
        os.makedirs(os.path.join(out_folder, "wavs"))

    # Get audio file duration
    duration = get_audio_length(filepath)
    # Transcribe the audio file using OpenAI Whisper
    print(f"Transcribing audio file: {filepath} to output folder: {out_folder}...")
    subprocess.run(
        ["whisperx", filepath, "--model", "medium", "--align_model", "VOXPOPULI_ASR_BASE_10K_ES", "--language",
         language,
         "--output_format", "json", "--output_dir", out_folder])

    filename = os.path.basename(filepath)
    json_path = os.path.join(out_folder, filename.replace(".wav", ".json"))
    results = read_json(json_path)
    results = remove_end_hallucinations(results)

    # Check segments duration and split them if they are longer than 10 seconds
    checked_segments = check_segments(results["segments"])
    # Cut original audio file into clips using the custom segments
    print("Cutting audio file into clips...")
    cut_audio_and_generate_metadata(out_folder, filepath, checked_segments)
    print("Done! Check the folder {0} for the audio clips and the metadata file.".format(out_folder))
    #Format the time in MM:SS format
    seconds = datetime.datetime.now().timestamp() - time.timestamp()
    timeMMSS = str(datetime.timedelta(seconds=seconds))
    print("Total time: {0}. Audio duration: {1}. Processing speed: {2}".format(timeMMSS, str(datetime.timedelta(seconds=duration)), str(duration / seconds)[:4] + "x"))


    # Remove the joined audio file if it was created
    if original_filepath != filepath:
        os.remove(os.path.join(filepath))
    # Remove joined_audio
    if os.path.exists(os.path.join(out_folder, JOINED_AUDIO_FILE)):
        os.remove(os.path.join(out_folder, JOINED_AUDIO_FILE))
    return out_folder


def check_segments(segments, max_segment_duration=10):


    segments_to_remove = []

    for s, segment in enumerate(segments):
        for i in range(len(segment["words"])):
            if "start" not in segment["words"][i].keys() or "end" not in segment["words"][i].keys():
                for j in range(i-1, -1, -1):
                    if "start" in segment["words"][j].keys() and "end" in segment["words"][j].keys():
                        segment["words"][i]["start"] = segment["words"][j]["start"]
                        segment["words"][i]["end"] = segment["words"][j]["end"]
                        print(f"Word {segment['words'][i]['word']} does not have start and end keys. Using word \"{segment['words'][j]['word']}\" timestamps.")
                        break
                segments_to_remove.append(s)
                break
    
    segments = [segment for i, segment in enumerate(segments) if i not in segments_to_remove]

    new_segments = []
    for segment in segments:
        if segment["end"] - segment["start"] > max_segment_duration:
            # Split the segment into smaller segments using the word timestamps to fill the new segment
            segment_duration = segment["end"] - segment["start"]
            n_splits = int(segment_duration / max_segment_duration)
            # Now we find the middle points of the segment where we must split
            splits_duration = segment_duration / (n_splits + 1)
            split_points = [segment["start"] + splits_duration * (i + 1) for i in range(n_splits)]
            # Now we create the new segments
            new_segment = dict()
            new_segment["start"] = segment["start"]
            new_segment["end"] = 0
            new_segment["text"] = ""
            new_segment["words"] = []
            current_split = 0
            for word in segment["words"]:
                # We keep adding words to the new segment until we reach a split point
                if current_split == len(split_points):  # If we are on the last segment simply add the remaining words
                    new_segment["words"].append(word)
                    new_segment["text"] += word["word"] + " "
                    new_segment["end"] = word["end"]
                elif word["end"] < split_points[current_split]:  # Keep adding words that fit in the segment
                    new_segment["words"].append(word)
                    new_segment["text"] += word["word"] + " "
                    new_segment["end"] = word["end"]
                else:  # If we reached the end of the segment, add the segment to the list and start a new one
                    new_segments.append(new_segment)
                    new_segment = dict()
                    new_segment["start"] = word["start"]
                    new_segment["text"] = ""
                    new_segment["words"] = []
                    new_segment["words"].append(word)
                    new_segment["text"] += word["word"] + " "
                    new_segment["end"] = word["end"]
                    current_split += 1
            new_segments.append(new_segment)
        else:
            new_segments.append(segment)

    # Remove segments with only one word
    new_segments = [segment for segment in new_segments if len(segment["words"]) > 1]
    #if a segment has their two last words with the same timestamp, remove the segment:
    new_segments = [segment for segment in new_segments if segment["words"][len(segment["words"]) - 1]["end"] != segment["words"][len(segment["words"]) - 2]["end"]]
    #repeat the same for the start of the segment
    new_segments = [segment for segment in new_segments if segment["words"][0]["start"] != segment["words"][1]["start"]]
    return new_segments


def cut_and_normalize_segment(audiopath, text, start, end, outfile, index ,fileObject, semaphore):
        subprocess.run(
                ['ffmpeg', '-i', audiopath, '-ss', str(start), '-to', str(end), outfile, '-loglevel', 'error', '-y',
                 '-hide_banner'])
        normalize_audio(outfile)
        cleaned_text = multilingual_cleaners(text)
        semaphore.acquire()
        fileObject.write('/content/tacotron2/wavs/{0}.wav|{1}\n'.format(str(index), cleaned_text))
        semaphore.release()


def cut_audio_and_generate_metadata(out_folder: str, audio_path: str, segments) -> None:
    sem = Semaphore(1)

    work_list = []
    index = 1
    f = open(os.path.join(out_folder, "metadata.txt"), "w", encoding='utf8')
    for segment in segments:
        start = segment["start"]
        end = (segment["words"][len(segment["words"]) - 1]["end"] + segment["end"]) / 2
        outfile = os.path.join(out_folder, "wavs", str(index) + ".wav")
        work_list.append((audio_path, segment["text"], start, end, outfile, index, f, sem))
        index += 1

    with tqdm(total=len(work_list)) as pbar: # type: ignore
        with ThreadPoolExecutor(max_workers=8) as ex:
            futures = [ex.submit(cut_and_normalize_segment, *args) for args in work_list]
            for future in as_completed(futures):
                pbar.update(1)
    f.close()


# TODO: could modify easily by iterating over copy of results and discard each segment that is a hallucination
def remove_end_hallucinations(results):  # https://github.com/openai/whisper/discussions/928
    hallucinations = set(read_json(os.path.abspath("hallucination_sentences.json"))['hallucinations'])
    if results["segments"][len(results["segments"]) - 1]["text"] in hallucinations:
        del results["segments"][len(results["segments"]) - 1]
    return results

def copy_audio_list_to_tmp_folder(audio_list):
    #create tmp folder
    if not os.path.exists(os.path.abspath("tmp")):
        os.makedirs(os.path.abspath("tmp"))
    #Delete elements in tmp folder
    for f in os.listdir(os.path.abspath("tmp")):
        #if f is a file
        if os.path.isfile(os.path.join(os.path.abspath("tmp"), f)):
            os.remove(os.path.join(os.path.abspath("tmp"), f))
        else: 
            shutil.rmtree(os.path.join(os.path.abspath("tmp"), f))
    for audio in audio_list:
        shutil.copy(audio, os.path.join(os.path.abspath("tmp"), os.path.basename(audio)))
    return os.path.abspath("tmp")


def force_cudnn_initialization():
    s = 32
    dev = torch.device('cuda')
    torch.nn.functional.conv2d(torch.zeros(s, s, s, s, device=dev), torch.zeros(s, s, s, s, device=dev))


if __name__ == "__main__":
    argparse = argparse.ArgumentParser(
        description='Script to transcribe and cut long audio files into short clips using OpenAI Whisper and ffmpeg.')
    argparse.add_argument('-f', '--filepath', type=str, required=True, help="Path to the audio file or folder to transcribe.")
    
    argparse.add_argument('-l', '--language', type=str, default="es", required=False,
                          help='Language code of the audio file. Default is Spanish (es). English not supported yet.')
    argparse.add_argument('-n', '--name_run', type=str, default="run", required=False,
                          help='Name of the execution. Default is filename+timestamp. This will be name of the output folder together'
                               + ' with the date and time of the execution.')
    args = argparse.parse_args()
    # Check that args.filepath file name does not contain any spaces or special characters using regex
    filename = args.filepath.split("\\")[-1]
    if re.search(r'[^A-Za-z0-9_\.]+', filename):
        raise Exception("File name contains special characters or spaces. Please rename the file and try again.")
    if not os.path.isabs(args.filepath):
        args.filepath = os.path.abspath(args.filepath)
    force_cudnn_initialization()  # Trick to avoid CUDNN_STATUS_NOT_INITIALIZED error when running some models
    main(args.filepath, args.name_run, args.language)
