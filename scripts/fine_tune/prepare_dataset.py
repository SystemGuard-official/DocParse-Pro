# prepare_dataset.py

from datasets import Dataset
from PIL import Image
import pandas as pd

def load_dataset(csv_path="labels.csv"):
    df = pd.read_csv(csv_path)
    dataset = Dataset.from_pandas(df)

    def load_image(example):
        example["image"] = Image.open(example["image_path"]).convert("RGB")
        return example

    dataset = dataset.map(load_image)
    return dataset
