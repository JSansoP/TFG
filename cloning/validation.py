import argparse
import os
import shutil
import subprocess
import random
import datetime

import torch
import datasets
from transformers import AutoFeatureExtractor, WavLMForXVector

try:
    import tqdm
except ImportError:
    tqdm = None

# CONSTANTS

N_RUNS = 100


def main(fakefiles, realfiles):
    datasets.utils.logging.set_verbosity(datasets.logging.CRITICAL)
    datasets.disable_progress_bar()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    feature_extractor = AutoFeatureExtractor.from_pretrained("microsoft/wavlm-base-plus-sv")
    model = WavLMForXVector.from_pretrained("microsoft/wavlm-base-plus-sv").to(device)
    similarities = []
    for _ in range(N_RUNS):
        compare_folder = generate_compare_folders(fakefiles, realfiles)
        similarities.append(get_similarity(compare_folder, feature_extractor, model, device))
    print("Average similarity: ", sum(similarities) / len(similarities))

    # Calculate standard deviation
    sum_squares = 0
    for sim in similarities:
        sum_squares += (sim - sum(similarities) / len(similarities)) ** 2
    print("Standard deviation: ", (sum_squares / len(similarities)) ** 0.5)


def generate_compare_folders(folder, realfiles):
    shutil.rmtree(os.path.abspath("tmp"), ignore_errors=True)
    os.makedirs(os.path.abspath("tmp"))
    # copy all folder wav files into tmp/i folder
    n_files = 0
    for file in os.listdir(os.path.abspath(folder)):
        if file.endswith(".wav"):
            shutil.copy(os.path.join(folder, file), os.path.join(os.path.abspath("tmp"), file))
            n_files += 1
    # copy a random sample of size n_files from realfiles into tmp/i folder
    for _ in range(n_files):
        file = random.choice(os.listdir(realfiles))
        # Make sure the file has not been copied already
        while os.path.exists(os.path.join(os.path.abspath("tmp"), file)):
            file = random.choice(os.listdir(realfiles))
        shutil.copy(os.path.join(realfiles, file), os.path.join(os.path.abspath("tmp"), file))
    convert_to_16k(os.path.join(os.path.abspath("tmp")))
    return os.path.abspath("tmp")


def convert_to_16k(folder):
    for file in os.listdir(os.path.abspath(folder)):
        if file.endswith(".wav"):
            subprocess.run(["ffmpeg", "-i", os.path.join(folder, file), "-ar", "16000",
                            os.path.join(folder, file.replace(".wav", "tmp.wav")), "-y", "-loglevel", "error",
                            "-hide_banner"])
            os.remove(os.path.join(folder, file))
            os.rename(os.path.join(folder, file.replace(".wav", "tmp.wav")), os.path.join(folder, file))


def get_similarity(folder, feature_extractor, model, device):
    # Create dataset with audiofolder mode, pass the folder dir and make it silent
    dataset = datasets.load_dataset("audiofolder", data_dir=folder)
    sampling_rate = dataset["train"]["audio"][0]["sampling_rate"]

    # audio file is decoded on the fly
    inputs = feature_extractor(
        [d["array"] for d in dataset["train"]["audio"]], sampling_rate=sampling_rate, return_tensors="pt",
        padding=True
    ).to(device)

    with torch.no_grad():
        embeddings = model(**inputs).embeddings

    embeddings = torch.nn.functional.normalize(embeddings, dim=-1).cpu()

    # the resulting embeddings can be used for cosine similarity-based retrieval
    cosine_sim = torch.nn.CosineSimilarity(dim=-1)
    similarity = cosine_sim(embeddings[0], embeddings[1])
    return similarity.item()


def get_folder_similarity(folder):
    shutil.rmtree(os.path.abspath("tmp"), ignore_errors=True)
    shutil.copytree(folder, os.path.join(os.path.abspath("tmp"), "realfiles"))
    convert_to_16k(os.path.join(os.path.abspath("tmp"), "realfiles"))
    folder_similarity = get_similarity(os.path.join(os.path.abspath("tmp"), "realfiles"))
    shutil.rmtree(os.path.join(os.path.abspath("tmp"), "realfiles"), ignore_errors=True)
    print("Folder similarity: ", folder_similarity)

def force_cudnn_initialization():
    s = 32
    dev = torch.device('cuda')
    torch.nn.functional.conv2d(torch.zeros(s, s, s, s, device=dev), torch.zeros(s, s, s, s, device=dev))

if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description='Speaker Recognition')
    #Make it so there are two options: pass both -s and -r or pass -f
    argparser.add_argument('-s', '--sinteticfiles', type=str, help='Path to folder containing sintetic audio files',
                           required=False)
    argparser.add_argument('-r', '--realfiles', type=str,
                           help='Path to folder containing real audio files (ground truth)', required=False)
    argparser.add_argument('-f', '--folder', type=str, help='Path to folder containing real files to compare',
                           required=False)
    args = argparser.parse_args()

    shutil.rmtree(os.path.abspath("tmp"), ignore_errors=True)
    force_cudnn_initialization()
    # Make sure that if folder is passed, sinteticfiles and realfiles are not passed
    if args.folder is not None:
        if args.sinteticfiles is not None or args.realfiles is not None:
            print("Error: cannot pass both -f and -s or -r")
            exit(1)
        else:
            # Check that folder exists and is a directory
            if not os.path.isdir(args.folder):
                print("Error: folder does not exist")
                exit(1)
            get_folder_similarity(os.path.abspath(args.folder))
    else:
        if args.sinteticfiles is None or args.realfiles is None:
            print("Error: must pass both -s and -r or -f")
            exit(1)
        else:
            # Check that folder exists and is a directory
            if not os.path.isdir(os.path.normpath(args.sinteticfiles)):
                print(f"Error: {args.sinteticfiles} folder does not exist")
                exit(1)
            if not os.path.isdir(os.path.normpath(args.realfiles)):
                print("Error: real files folder does not exist")
                exit(1)
            args.sinteticfiles = os.path.abspath(args.sinteticfiles)
            args.realfiles = os.path.abspath(args.realfiles)
            main(args.sinteticfiles, args.realfiles)
            shutil.rmtree(os.path.abspath("tmp"))
