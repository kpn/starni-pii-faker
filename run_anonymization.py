import pandas as pd
import json
import anonymization_functions
import ast
from pathlib import Path
import replace_non_pii


# Read recipe inputs
input_path = Path(__file__).resolve().parent / "data" / "input.dat"
input_data_df = pd.read_csv(input_path, sep="|")
BASE_SEED = 42


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


anonymized_transcripts, anonymized_labels = [], []
for original_transcript, original_annotations_str, transcription_id in zip(input_data_df["transcript"], input_data_df["human_annotated_labels"]):
    original_annotations = parse_labels(original_annotations_str)
    try:
        fake_piis = anonymization_functions.create_fake_pii_from_annotations(original_annotations, seed=BASE_SEED)
    except Exception as e:
        print(f"Error creating fake PII for transcript:", original_transcript, "with annotations:", original_annotations)
        raise e

    anonymized_transcript, anonymized_label = anonymization_functions.create_anonymized_transcript_and_labels(original_transcript, original_annotations, fake_piis)
    anonymized_transcripts.append(anonymized_transcript)
    anonymized_labels.append(anonymized_label)

input_data_df["anonymized_transcript"] = anonymized_transcripts
input_data_df["anonymized_labels"] = anonymized_labels

# Write recipe outputs
output_path = Path(__file__).resolve().parent / "data" / "output.dat"
input_data_df.to_csv(
    output_path, sep="|", index=False
)