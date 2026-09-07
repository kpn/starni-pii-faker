# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
import json
import faker_anonymization

# Read recipe inputs
golden_dataset_round1_df = pd.read_csv("data/golden_dataset_round1.dat", sep="|")

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
    
for original_transcript, original_annotations_str in zip(golden_dataset_round1_df["cleaned_contact_text"], golden_dataset_round1_df["human_annotated_labels"]):
    original_annotations = parse_labels(original_annotations_str)
    all_replacements = faker_anonymization.create_fake_pii_from_annotations(original_annotations)
    fake_piis = [replacement[2] for replacement in all_replacements]
    anonymized_transcript, anonymized_label = faker_anonymization.create_anonymized_transcript_and_labels(original_transcript, original_annotations, fake_piis)
    anonymized_transcripts.append(anonymized_transcript)
    anonymized_labels.append(anonymized_label)

golden_dataset_round1_df["anonymized_transcripts"] = anonymized_transcripts
golden_dataset_round1_df["anonymized_labels"] = anonymized_labels


golden_dataset_round1_original_and_anonymized_df = golden_dataset_round1_df 

# Write recipe outputs
golden_dataset_round1_original_and_anonymized_df.to_csv(
    "data/faker_output.dat", sep="|", index=False
)
