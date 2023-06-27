import json
import os
import re
import statistics
import subprocess

try:
    from tqdm import tqdm
except:
    print("Tqdm not found, install it for progress bars")
    tqdm = lambda x: x

_whitespace_re = re.compile(r"\s+")


def read_json(path):
    with open(path, 'r', encoding="utf8") as f:
        return json.load(f)


def normalize_audio(filepath):
    """
    Warning: This function will delete the original file
    This function normalizes the audio file and removes silence from the start and end of the file.
    It will also convert the file to mono, 16 bit 22050 Hz wav file.
    """

    # First we transform the audio file into mono, 16 bit 22050 Hz wav file
    # Set outfile to the same as filepath but change the extension to .wav
    filename = os.path.basename(filepath).split(".")[0] + ".wav"
    dirname = os.path.dirname(filepath)
    filepath = os.path.join(dirname, filename)
    subprocess.run(["ffmpeg", "-i", filepath, "-ac", "1", "-ar", "22050", "-acodec", "pcm_s16le",
                    filepath.replace(".wav", "tmp1.wav"), "-y", "-loglevel", "error", "-hide_banner"])

    os.remove(filepath)

    # Now we normalize the audio file
    # command: ffmpeg -i in.wav -filter:a "speechnorm=e=6" out.wav
    subprocess.run(["ffmpeg", "-i", filepath.replace(".wav", "tmp1.wav"), "-filter:a", 'speechnorm=e=6',
                    filepath, "-y", "-loglevel", "error", "-hide_banner"])

    os.remove(filepath.replace(".wav", "tmp1.wav"))
    # Now we remove silence from the start and end of the file
    # command: ffmpeg -i .\recording2_cut.wav -af "silenceremove=start_periods=1:start_silence=0.5:start_threshold=0.001,areverse,silenceremove=start_periods=1:start_silence=0.5:start_threshold=0.001,areverse" silenceremoved.wav
    # subprocess.run(["ffmpeg", "-i", filepath.replace(".wav", "tmp2.wav"), "-af",
    #                 "silenceremove=start_periods=1:start_silence=0.1:start_threshold=0.001,areverse,silenceremove=start_periods=1:start_silence=0.1:start_threshold=0.001,areverse",
    #                 filepath, "-y", "-loglevel", "error", "-hide_banner"])

    # os.remove(filepath.replace(".wav", "tmp2.wav"))


def normalize_folder(folderpath, verbose=False):
    """
    This function normalizes all the audio files in a folder.
    """
    print("Normalizing all wav files in folder {0}".format(folderpath))
    bar = tqdm
    if not verbose:
        bar = lambda x: x
    for filename in bar(os.listdir(folderpath)):
        if filename.endswith(".wav") or filename.endswith(".WAV") \
                or filename.endswith(".mp3") or filename.endswith(".MP3") \
                or filename.endswith(".m4a") or filename.endswith(".M4A") \
                or filename.endswith(".flac") or filename.endswith(".FLAC") \
                or filename.endswith(".ogg") or filename.endswith(".OGG"):
            normalize_audio(os.path.join(folderpath, filename))


def list_audio_lengths(folder_path):
    """
    This function returns a list with the duration of all the audio files in a folder.
    """

    lengths = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".wav"):
            le = get_audio_length(os.path.join(folder_path, filename))
            # print("File {0} has duration {1}".format(filename, le))
            if le > 10:
                print("WARNING: File {0} has duration {1} (greater than 10 seconds)".format(filename, le))
            lengths.append(le)
    print("Average audio length: {0}".format(sum(lengths) / len(lengths)))
    print("Standard deviation: {0}".format(statistics.stdev(lengths)))


def get_audio_length(input_audio):
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
         input_audio], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return float(result.stdout)


def replace_symbols(text):

    text = text.replace(";", ",")
    text = text.replace("-", " ")
    text = text.replace(":", ",")
    return text


def remove_aux_symbols(text):
    text = re.sub(r"[\<\>\(\)\[\]\"]+", "", text)
    return text


def collapse_whitespace(text):
    return re.sub(_whitespace_re, " ", text).strip()


def multilingual_cleaners(text):
    """Pipeline for multilingual text"""
    text = text.lower()
    text = replace_symbols(text)
    text = remove_aux_symbols(text)
    text = collapse_whitespace(text)
    return text
