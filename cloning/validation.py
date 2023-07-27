import argparse
import os
import shutil
import subprocess
import random
import datetime
from typing import List

import torch
import datasets
from transformers import AutoFeatureExtractor, WavLMForXVector
import numpy as np
try:
    import tqdm
except ImportError:
    tqdm = None

# CONSTANTS

def main(fakefiles, realfiles):
    datasets.utils.logging.set_verbosity(datasets.logging.CRITICAL)
    datasets.disable_progress_bar()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    feature_extractor = AutoFeatureExtractor.from_pretrained("microsoft/wavlm-base-plus-sv")
    model = WavLMForXVector.from_pretrained("microsoft/wavlm-base-plus-sv").to(device) # type: ignore
    similarities = []

    fakefiles_tmp, realfiles_tmp = generate_compare_folders(fakefiles, realfiles)
    similarities = get_similarity(fakefiles_tmp, realfiles_tmp, feature_extractor, model, device)

    print("Similarities: ", similarities)
    print("Average similarity: ", np.mean(similarities))
    print("Standard deviation: ", np.std(similarities))



def generate_compare_folders(fakefiles, realfiles):
    fakefiles_tmp = os.path.join(os.path.abspath("tmp"), "fakefiles")
    realfiles_tmp = os.path.join(os.path.abspath("tmp"), "realfiles")
    shutil.copytree(fakefiles, fakefiles_tmp)
    shutil.copytree(realfiles, realfiles_tmp)
    convert_to_16k(fakefiles_tmp)
    convert_to_16k(realfiles_tmp)
    return fakefiles_tmp, realfiles_tmp


def convert_to_16k(folder):
    for file in os.listdir(os.path.abspath(folder)):
        if file.endswith(".wav"):
            subprocess.run(["ffmpeg", "-i", os.path.join(folder, file), "-ar", "16000",
                            os.path.join(folder, file.replace(".wav", "tmp.wav")), "-y", "-loglevel", "error",
                            "-hide_banner"])
            os.remove(os.path.join(folder, file))
            os.rename(os.path.join(folder, file.replace(".wav", "tmp.wav")), os.path.join(folder, file))


def get_similarity(fakefiles, realfiles, feature_extractor, model, device) -> List[float]:
    # Create dataset with audiofolder mode, pass the folder dir and make it silent
    fake_dataset = datasets.load_dataset("audiofolder", data_dir=fakefiles)
    real_dataset = datasets.load_dataset("audiofolder", data_dir=realfiles)
    sampling_rate = fake_dataset["train"]["audio"][0]["sampling_rate"] # type: ignore

    #Now i want to get similarity between each fake and real file
    similarities = []
    for i in range(len(fake_dataset["train"]["audio"])): # type: ignore
        for j in range(len(real_dataset["train"]["audio"])): # type: ignore
            inputs = feature_extractor(
                [fake_dataset["train"]["audio"][i]["array"], real_dataset["train"]["audio"][j]["array"]], # type: ignore
                sampling_rate=sampling_rate, return_tensors="pt", padding=True
            ).to(device)
            with torch.no_grad():
                embeddings = model(**inputs).embeddings
            embeddings = torch.nn.functional.normalize(embeddings, dim=-1).cpu()
            # the resulting embeddings can be used for cosine similarity-based retrieval
            cosine_sim = torch.nn.CosineSimilarity(dim=-1)
            similarity = cosine_sim(embeddings[0], embeddings[1])
            similarities.append(similarity.item())
    return similarities


def force_cudnn_initialization():
    s = 32
    dev = torch.device('cuda')
    torch.nn.functional.conv2d(torch.zeros(s, s, s, s, device=dev), torch.zeros(s, s, s, s, device=dev))

if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description='Speaker Recognition')
    #Make it so there are two options: pass both -s and -r or pass -f
    argparser.add_argument('-s', '--sinteticfiles', type=str, help='Path to folder containing sintetic audio files',
                           required=True)
    argparser.add_argument('-r', '--realfiles', type=str,
                           help='Path to folder containing real audio files (ground truth)', required=True)
    args = argparser.parse_args()

    shutil.rmtree(os.path.abspath("tmp"), ignore_errors=True)
    force_cudnn_initialization()

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
