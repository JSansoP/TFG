import argparse
import os
import shutil
import subprocess

import torch
from datasets import load_dataset
from transformers import AutoFeatureExtractor, WavLMForXVector


def main(folder, threshold=0.7):
    dataset = load_dataset("audiofolder", data_dir=folder)
    print(type(dataset))
    #dataset = dataset.sort("id")
    sampling_rate = dataset["train"]["audio"][0]["sampling_rate"]


    feature_extractor = AutoFeatureExtractor.from_pretrained("microsoft/wavlm-base-plus-sv")
    model = WavLMForXVector.from_pretrained("microsoft/wavlm-base-plus-sv")

    # audio file is decoded on the fly
    inputs = feature_extractor(
        [d["array"] for d in dataset["train"]["audio"][:2]], sampling_rate=sampling_rate, return_tensors="pt", padding=True
    )

    with torch.no_grad():
        embeddings = model(**inputs).embeddings

    embeddings = torch.nn.functional.normalize(embeddings, dim=-1).cpu()

    # the resulting embeddings can be used for cosine similarity-based retrieval
    cosine_sim = torch.nn.CosineSimilarity(dim=-1)
    similarity = cosine_sim(embeddings[0], embeddings[1])
    threshold = 0.7  # the optimal threshold is dataset-dependent
    if similarity < threshold:
        print("Speakers are not the same!")
    print(round(similarity.item(), 2))


def createTempFolder(folder):
    """
    Creates a temporary folder with the same structure as the original folder
    with the audio files converted to 16kHz sampling rate
    """
    temp_folder = os.path.join(folder, "temp")
    #If exists raise error
    if os.path.isdir(temp_folder):
        raise Exception("Temporary folder already exists, please delete it and try again")
    os.makedirs(os.path.join(temp_folder, "wavs"))
    #Copy txt files
    for file in os.listdir(folder):
        if file.endswith(".txt"):
            shutil.copy(os.path.join(folder, file), os.path.join(temp_folder, file))
    #Convert audio files
    for file in os.listdir(os.path.join(folder, "wavs")):
        if file.endswith(".wav"):
            subprocess.run(["ffmpeg", "-i", os.path.join(folder,"wavs" , file), "-ar", "16000", os.path.join(temp_folder, "wavs", file), "-y", "-loglevel", "error", "-hide_banner"])

    return temp_folder

if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description='Speaker Recognition')
    argparser.add_argument('-f', '--folder', type=str, help='Path to folder containing audio files', required=True)
    argparser.add_argument('-t', '--threshold', type=float, help='Threshold for similarity', default=0.7)
    args = argparser.parse_args()
    #Check that folder exists and is a directory
    if not os.path.isdir(args.folder):
        print("Error: folder does not exist")
        exit(1)
    args.folder = os.path.abspath(args.folder)
    tmp_folder = createTempFolder(args.folder)
    main(tmp_folder, args.threshold)
    shutil.rmtree(tmp_folder)

