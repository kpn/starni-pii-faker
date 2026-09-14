import pandas as pd
import json
import anonymization_functions
import ast

# Read recipe inputs
input_data_df = pd.read_csv("data/input.dat", sep="|")

anonymized_transcripts = []
anonymized_labels = []

def parse_labels(value):
    """Parse labels stored as list, JSON string, or Python literal."""
    if value is None or pd.isna(value):
        return []

    if isinstance(value, list):
        return value

    try:
        return json.loads(value)
    except Exception:
        return ast.literal_eval(value)
    
for original_transcript, original_annotations_str in zip(input_data_df["transcript"], input_data_df["human_annotated_labels"]):
    original_annotations = parse_labels(original_annotations_str)
    fake_piis = anonymization_functions.create_fake_pii_from_annotations(original_annotations)
    anonymized_transcript, anonymized_label = anonymization_functions.create_anonymized_transcript_and_labels(original_transcript, original_annotations, fake_piis)
    anonymized_transcripts.append(anonymized_transcript)
    anonymized_labels.append(anonymized_label)

input_data_df["anonymized_transcript"] = anonymized_transcripts
input_data_df["anonymized_labels"] = anonymized_labels

# Write recipe outputs
input_data_df.to_csv(
    "data/output.dat", sep="|", index=False
)