import pandas as pd
from fuzzywuzzy import fuzz
import re

def normalize_text(text):
    if pd.isna(text):
        return ""
    # Lowercase, remove all spaces and special whitespaces
    return re.sub(r'\s+', '', str(text).lower().strip())

# Load the CSV
df = pd.read_csv("ocr_results_default.csv")

# Prediction columns to evaluate
model_columns = [
    # "trocr-base-handwritten",
    # "trocr-large-handwritten",
    # "trocr-base-stage1",
    # "trocr-large-stage1",
    # "trocr-large-printed"
    "extracted_text"
]

# Normalize the 'OriginalText' once
df["NormalizedOriginal"] = df["OriginalText"].apply(normalize_text)

# Compute normalized score for each model column
for col in model_columns:
    score_col = f"score_{col}"
    df[score_col] = df.apply(
        lambda row: fuzz.ratio(normalize_text(row[col]), row["NormalizedOriginal"]) / 100.0,
        axis=1
    )

# Optionally drop helper column
df.drop(columns=["NormalizedOriginal"], inplace=True)

# Save output
df.to_csv("ocr_results_normalized_scoring.csv", index=False)
