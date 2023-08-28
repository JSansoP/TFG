import argparse
import os
import shutil
import subprocess
from typing import List
import random
import torch
import datasets
from transformers import AutoFeatureExtractor, WavLMForXVector
from datetime import datetime
import numpy as np
try:
    import tqdm
except ImportError:
    tqdm = None

# CONSTANTS

def main(folder_path1, folder_path2, n, mode):
    datasets.utils.logging.set_verbosity(datasets.logging.CRITICAL)
    datasets.disable_progress_bar()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    feature_extractor = AutoFeatureExtractor.from_pretrained("microsoft/wavlm-base-plus-sv")
    model = WavLMForXVector.from_pretrained("microsoft/wavlm-base-plus-sv").to(device) # type: ignore
    similarities = []

    tmp_folder_1 = generate_16k_folder(folder_path1)
    tmp_folder_2 = generate_16k_folder(folder_path2)
    similarities = []
    if mode == "all":
        similarities = get_similarities(tmp_folder_1, tmp_folder_2, feature_extractor, model, device)
    elif mode == "random":
        similarities = get_similarities_random(tmp_folder_1, tmp_folder_2, feature_extractor, model, device, n)

    print("Similarities: ", similarities)
    print("Average similarity: ", np.mean(similarities))
    print("Standard deviation: ", np.std(similarities))
    print("Max: ", np.max(similarities))
    print("Min: ", np.min(similarities))



def generate_16k_folder(folder):
    tmp = os.path.join(os.path.abspath("tmp"), "16k-"+datetime.now().strftime("%Y%m%d-%H%M%S"))
    shutil.copytree(folder, tmp)
    convert_to_16k(tmp)
    return tmp


def convert_to_16k(folder):
    for file in os.listdir(os.path.abspath(folder)):
        if file.endswith(".wav"):
            subprocess.run(["ffmpeg", "-i", os.path.join(folder, file), "-ar", "16000",
                            os.path.join(folder, file.replace(".wav", "tmp.wav")), "-y", "-loglevel", "error",
                            "-hide_banner"])
            os.remove(os.path.join(folder, file))
            os.rename(os.path.join(folder, file.replace(".wav", "tmp.wav")), os.path.join(folder, file))


def get_similarities_random(folder1, folder2, feature_extractor, model, device, number_comparisons) -> List[float]:
    # Create dataset with audiofolder mode, pass the folder dir and make it silent
    dataset1 = datasets.load_dataset("audiofolder", data_dir=folder1)
    dataset2 = datasets.load_dataset("audiofolder", data_dir=folder2)
    sampling_rate = dataset1["train"]["audio"][0]["sampling_rate"] # type: ignore

    similarities = []
    for _ in range(number_comparisons):
        i = random.randint(0, len(dataset1["train"]["audio"]) - 1) # type: ignore
        j = random.randint(0, len(dataset2["train"]["audio"]) - 1) # type: ignore
        # Extract features
        inputs = feature_extractor(
            [dataset1["train"]["audio"][i]["array"], dataset2["train"]["audio"][j]["array"]], # type: ignore
            sampling_rate=sampling_rate, return_tensors="pt", padding=True
        ).to(device)
        # Get embeddings
        with torch.no_grad():
            embeddings = model(**inputs).embeddings
        embeddings = torch.nn.functional.normalize(embeddings, dim=-1).cpu()
        # Calculate similarity
        cosine_sim = torch.nn.CosineSimilarity(dim=-1)
        similarity = cosine_sim(embeddings[0], embeddings[1])
        similarities.append(similarity.item())
    return similarities

def get_similarities(fakefiles, realfiles, feature_extractor, model, device) -> List[float]:
    # Create dataset with audiofolder mode, pass the folder dir and make it silent
    fake_dataset = datasets.load_dataset("audiofolder", data_dir=fakefiles)
    real_dataset = datasets.load_dataset("audiofolder", data_dir=realfiles)
    sampling_rate = fake_dataset["train"]["audio"][0]["sampling_rate"] # type: ignore

    #Now i want to get similarity between each fake and real file
    similarities = []
    number_comparisons = len(fake_dataset["train"]["audio"]) * len(real_dataset["train"]["audio"]) # type: ignore
    print(f"Comparing {number_comparisons} pairs of files")
    for i in range(len(fake_dataset["train"]["audio"])): # type: ignore
        for j in range(len(real_dataset["train"]["audio"])): # type: ignore
            print(f"Comparing {i} and {j}")
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
    argparser = argparse.ArgumentParser(description='Speaker Similarity Validation')
    argparser.add_argument('-p', '--paths', type=str,
                        help='Path to the folders to compare (1 or 2)', required=True, nargs="+")
    argparser.add_argument('-n', '--n', type=int, default=10, help='Number of random comparisons to make. Only works with mode random.', required=False)

    argparser.add_argument('-m', '--mode', type=str, default="random", help='Mode to compare the folders. Options: random, all. When selecting \
                           random, parameter number of comparisons (-n) is used.', required=False)
    args = argparser.parse_args()

    shutil.rmtree(os.path.abspath("tmp"), ignore_errors=True)

    if len(args.paths) > 2:
        print(f"Error: only one or two folders can be passed, {len(args.paths)} were passed.")
        exit(1)
    elif len(args.paths) == 1:
        print("Warning: only one folder was passed. Comparing folder with itself")
        args.paths.append(args.paths[0])
    # Check that folder exists and is a directory
    if not os.path.isdir(os.path.normpath(args.paths[0])):
        print(f"Error: {args.paths[0]} folder does not exist")
        exit(1)
    if not os.path.isdir(os.path.normpath(args.paths[1])):
        print(f"Error: {args.paths[1]} folder does not exist")
        exit(1)
    path1 = os.path.abspath(args.paths[0])
    path2 = os.path.abspath(args.paths[1])


    force_cudnn_initialization()
    main(args.paths[0], args.paths[1], args.n, args.mode)
