# starni-pii-faker
This repository contains the code for creating an anonymized vesion of an input text containing PII annotations, using the Faker python package (https://faker.readthedocs.io/en/master/) for most PII categories. 

Currently for Dutch, but can be very easily extended to other languages, as the Faker package supports many of them.

## Supported PII categories
| PII category | Definition |
|---|---|
| NAME_GIVEN | Given name of a person, not including personal titles such as ‘Mrs.’ or ‘Mr.’ |
| NAME_FAMILY | Family name of a person, not including personal titles such as ‘Mrs.’ or ‘Mr.’ |
| DATE_OF_BIRTH | - |
| LOCATION_ADDRESS | Includes street names and/or house numbers, as well as any other secondary unit indicators such as apartement number, office number,  floor number, and building names. |
| LOCATION_ZIP | Postal code / ZIP code |
| LOCATION_CITY | Any kind of human settlement, such as cities, towns, villages, municipalities, etc. Includes both references to the settlement itself as well as references to individual boroughs or districts. |
| LOCATION_OTHER | Remaining location-related entities, such as countries, provinces, states or continents. |
| EMAIL_ADDRESS | - |
| AGE | - |
| ORGANIZATION | Organisation or company names |
| PHONE_NUMBER | - |

## Usage

1. Create a virtual env with python 3.12 and the packages specified in the requirements.txt file

2. Have a "data" folder at the same level of run_anonymization.py. In the data folder put your test file "input.dat" a pipeline separated text file with the following structure:

```json
transcript: The raw text containing some PII. 
Example: 
"[agent]: Goedemorgen, KPN spreekt met Jan.
[customer]: Hallo goedendag Max. Ik heb een vraag, Ik had gister, telefoon paar keer uit en aangezet, want ik wel lekker liep en nu heb ik alles weer. Ik weer Alleen krijg geen sms berichten meer binnen."

human_annotated_labels: text array of JSON dictionaries containing the PII tag specification for the text in cleaned_contact_text. 
Example:
""[{"text":""KPN"",""beginningIndex"":22,""endIndex"":25,""category"":""ORGANIZATION_NON-PII""},{""text"":""Jan"",""beginningIndex"":38,""endIndex"":41,""category"":""NAME_GIVEN_PII""},{""text"":""Max"",""beginningIndex"":70,""endIndex"":73,""category"":""NAME_GIVEN_PII""}]""
```

Each JSON dictionary contains the following keys:
```json
text: the PII value recognized by a human during the indicated labeling task;
beginningIndex: the position of the first character of the recognized PII value (from the beginning of the cleaned_contact_text, 0-index);
endIndex: the position of the last character of the recognized PII value + 1 (from the beginning of the cleaned_contact_text, 0-index);
category: the tag defining the PII type. The supported PII types are described in the table below.
```

3. Activate the virtual env you have created earlier and run on the terminal:
<code>python run_anonymization.py</code>

4. Verify that in the data folder the file "output.dat" has been created. The layout of this file is the same as the input one, **except for two additional columns**:

```json
anonymized_transcript: Is a copy of the transcript but with all the PIIs - as specified in human_annotated_labels - replaced by other values of the same PII category, aligned with the specified language. 
anonymized_labels: Indicates the updated positions of the value of the substituted PII values, using the same layout of human_annotated_labels.
```

## Examples
```python 
transcript = "Hello my name is Tom, I live in Amsterdam"
annotations = [{"text":"Tom","beginningIndex":17,"endIndex":20,"category":"NAME_GIVEN_PII"},{"text":"Amsterdam","beginningIndex":31,"endIndex":40,"category":"LOCATION_CITY_PII"}]

print(anonymized_transcript)
# Hello my name is Julius I live in Gronsveld

print(anonymized_labels)
# [{'text': 'Julius', 'beginningIndex': 17, 'endIndex': 23, 'category': 'NAME_GIVEN_PII'}, {'text': 'Gronsveld', 'beginningIndex': 34, 'endIndex': 43, 'category': 'LOCATION_CITY_PII'}]

```

For PII categories such as zip codes, date of births, and addresses, the pipeline returns a fake PII in the same format as the real (input) PII:

```python
transcript = "1022AB is my postal code"
annotations = [{"text":"1022AB","beginningIndex":0,"endIndex":6,"category":"LOCATION_ZIP_PII"}]

print(anonymized_transcript)
# 2224JM is my postal code
```

```python
transcript = "1022 Arnold Berend is my postal code"
annotations = [{"text":"1022 Arnold Berend","beginningIndex":0,"endIndex":17,"category":"LOCATION_ZIP_PII"}]

print(anonymized_transcript)
# 1061 Wessel Michad is my postal code
```

Moreover, the same or very similar real PII in a transcript are replaced by the same fake PII. We use Levenhstein Distance to compute similarity between PII.
```python
transcript = "My name is berend, Noah Berendse"
annotations = [{"text":"berend","beginningIndex":11,"endIndex":17,"category":"NAME_FAMILY_PII"}, {"text":"Noah","beginningIndex":19,"endIndex":23,"category":"NAME_GIVEN_PII"}, {"text":"Berendse","beginningIndex":24,"endIndex":33,"category":"NAME_FAMILY_PII"}]

print(anonymized_transcript)
# My name is de bruin, Lisanne De Bruin
```

## Contributing

To support another language, add files in the deidentify/surrogates/generators/resources folder containing the comprehensive given/family names lists for the respective language, and specify a different locale when you instantiate the Faker object in anonymization_functions.py:
```python
fake = Faker('nl_NL')
```
For a list of supported languages (locales) and their acronyms, see the Faker documentation.

However, for comprehensive and fine-grained anonymization support like this repo offers for Dutch, additional contributions should be made to fully support the new language. Please submit a pull request for any improvement you see fit.

KPN STA Research & Innovation