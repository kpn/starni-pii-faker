# starni-pii-faker
Given a text containing tagged PII, it replaces their values according to their tags, using the faker python package (https://faker.readthedocs.io/en/master/). 

Currently for Dutch, but very easily extendable to other languages, as the Faker package supports many of them.

## Testing Instructions

1. Create a virtual env with python 3.12 and the packages specified in the requirements.txt file

2. Have a "data" folder at the same level of run_faker.py. In the data folder put your test file "faker_input.dat" a pipeline separated text file with the following structure:

```json
labeling_task_id: alphanumeric string identifying your labeling task. Example: ZxY69aV3BHNo

ao_conversation_id: alphanumeric string identifying your data asset. Example: 370ed2cc-80e4-4ce6-9717-5f9ed26f6123

cleaned_contact_text: The raw text containing some PII. Example: 
"[agent]: Goedemorgen, KPN spreekt met Jan.
[customer]: Hallo goedendag Max. Ik heb een vraag, Ik had gister, telefoon paar keer uit en aangezet, want ik wel lekker liep en nu heb ik alles weer. Ik weer Alleen krijg geen sms berichten meer binnen."

human_annotated_labels: text array of JSON dictionaries containing the PII tag specification for the text in cleaned_contact_text. Example:
""[{"text":""KPN"",""beginningIndex"":22,""endIndex"":25,""category"":""ORGANIZATION_NON-PII""},{""text"":""Jan"",""beginningIndex"":38,""endIndex"":41,""category"":""NAME_GIVEN_PII""},{""text"":""Max"",""beginningIndex"":70,""endIndex"":73,""category"":""NAME_GIVEN_PII""}]""
```

Each JSON dictionary contains the following keys:
```json
text: the PII value recognized by a human during the indicated labeling task;
beginningIndex: the position of the first character of the recognized PII value (from the beginning of the cleaned_contact_text, 0-index);
endIndex: the position of the last character of the recognized PII value + 1 (from the beginning of the cleaned_contact_text, 0-index);
category: the tag defining the PII type. The supported PII types are described in the table below.
```
**TODO** add PII tag table</code>

3. Activate the virtual env you have created earlier and run on the terminal:
<code>python run_faker.py</code>

4. Verify that in the data folder the file output_faker.dat has been created. The layout of such file is the very same of the input one, **except for the two additional columns**:

```json
anonymized_transcripts: Contains a copy of the cleaned_contact_text but the values of all the PIIs - as specified in human_annotated_labels - have been replaced with other values of the same type, aligned with the specified language. 
anonymized_labels: Indicates the updated positions of the value of the substituted PII values, using the same layout of human_annotated_labels.
```

To support another language specify it when you instantiate the Faker object (see Faker documentation) and update the files in deidentify/surrogates/generators/resources folder.

Please submit a pull request for any improvement you see fit.
Thanks

kpn STA Research & Innovation