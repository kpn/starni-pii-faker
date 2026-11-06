from faker import Faker
import random
import re
import string
import unicodedata
from Levenshtein import ratio
from fuzzywuzzy import process
from os.path import dirname, join

from faker.providers.address.nl_NL import Provider as NLLocation


##################################################################################################################################################################
# Adjust values in this section (NLLocation, last/first names text files, 'nl_NL', and constants) to adapt anonymization to different language

# Specify Faker locale
fake = Faker('nl_NL')


references_path= join(dirname(__file__), "deidentify", "surrogates", "generators", "resources")
with open(join(references_path, "last_names.csv"), "r", encoding="utf-8") as f:
    ALL_LAST_NAMES = [line.replace(',', ' ').strip() for line in f.readlines()[1:]]  # Skip the header line

with open(join(references_path, "first_names_male.txt"), "r", encoding="utf-8") as f:
    all_male_names = [line.strip() for line in f.readlines()]

with open(join(references_path, "first_names_female.txt"), "r", encoding="utf-8") as f:
    all_female_names = [line.strip() for line in f.readlines()]

ALL_FIRST_NAMES = all_male_names + all_female_names

ALL_CITIES = list(NLLocation.cities)

# Month number to name mapping
MONTH_MAPPING = {
    '01': 'januari',
    '02': 'februari',
    '03': 'maart',
    '04': 'april',  
    '05': 'mei',
    '06': 'juni',
    '07': 'juli',
    '08': 'augustus',
    '09': 'september',
    '10': 'oktober',
    '11': 'november',
    '12': 'december'
}

EMAIL_DOMAINS = ("gmail.com", "hotmail.com", "outlook.com", "yahoo.com", "icloud.com", "protonmail.com", "aol.com", "zoho.com", "gmx.com", "mail.com", "live.nl", "home.nl")

SPELLED_OUT_NUMBERS = ('nul', 'een', 'twee', 'drie', 'vier', 'vijf', 'zes', 'zeven', 'acht', 'negen')

REGIONS = NLLocation.provinces + ('Twente',)

# Use select set of countries instead of faker to make replacement more realistic
COUNTRIES = [
    'Nederland', 'Duitsland', 'België', 'Frankrijk', 'Luxemburg', 'Spanje',
    'Italië', 'Portugal', 'Polen', 'Denemarken', 'Zwitserland', 'Oostenrijk', 'Griekenland',
    'Turkije', 'Marokko'
]

NATIONALITIES = (
    'Nederlander', 'Duitser', 'Belg', 'Fransman', 'Spanjaard',
    'Italiaan', 'Portugees', 'Brit', 'Ier', 'Pool', 'Zweed',
    'Deen', 'Noor', 'Fin', 'Zwitser', 'Oostenrijker', 'Griek',
    'Turk', 'Marokkaan', 'Amerikaan', 'Canadees', 'Surinamer',
)

ZIP_SPELLING_NAMES = {
    "A": ("Anna", "Anton", "Anne", "Anja", "Arthur", "Alex", "Adam"),
    "B": ("Bernard", "Bert", "Bart", "Bas", "Bram", "Benjamin"),
    "C": ("Cornelis", "Cor", "Cees", "Carla", "Chris", "Charlotte"),
    "D": ("Dirk", "Daan", "David", "Dennis", "Diana", "Daphne"),
    "E": ("Eduard", "Erik", "Eva", "Emma", "Esther", "Ellen"),
    "F": ("Ferdinand", "Frank", "Frans", "Fred", "Fatima", "Femke"),
    "G": ("Gerard", "Gerrit", "Gert", "Geert", "Gerda", "Guus"),
    "H": ("Hendrik", "Henk", "Hans", "Herman", "Harry", "Hanneke"),
    "I": ("Isaak", "Isa", "Iris", "Ingrid", "Irene", "Ilse", "Ivo"),
    "J": ("Jan", "Johan", "Johannes", "Jacob", "Jaap", "Jeroen", "Julia"),
    "K": ("Karel", "Kees", "Klaas", "Koen", "Kevin", "Karin", "Kim"),
    "L": ("Lodewijk", "Leo", "Laura", "Linda", "Lisa", "Lars", "Lucas"),
    "M": ("Maria", "Marie", "Maurits", "Marieke", "Mark", "Martin", "Mohammed"),
    "N": ("Nico", "Niels", "Nick", "Noah", "Nina", "Naomi", "Natasja"),
    "O": ("Otto", "Oscar", "Olaf", "Olivier", "Omar", "Olga"),
    "P": ("Pieter", "Peter", "Piet", "Paul", "Patrick", "Petra", "Paula"),
    "Q": ("Quinten", "Quintijn", "Quincy"),
    "R": ("Rudolf", "Rob", "Robert", "Richard", "Ronald", "Ruben", "Ria"),
    "S": ("Simon", "Sara", "Sophie", "Sandra", "Sander", "Stefan", "Sven"),
    "T": ("Theodoor", "Theo", "Teun", "Tinus", "Thomas", "Tim", "Tom"),
    "U": ("Ursula", "Udo"),
    "V": ("Victor", "Vincent", "Vera", "Valerie"),
    "W": ("Willem", "Wim", "Wouter", "Wilma", "Wendy", "Walter"),
    "X": ("Xander", "Xavier"),
    "Y": ("Yvonne", "Yvette", "Yolanda", "Yannick", "Yusuf"),
    "Z": ("Zara", "Zoe"),
}

###########################################################################################################################################################################

CODE_BASED_CATEGORIES = set(["LOCATION_ZIP_PII", "PHONE_NUMBER_PII", "INTERNAL_ID_PII", "BANK_ACCOUNT_PII", "CREDIT_CARD_PII", "SERIAL_NUMBER_PII", "SECRET_PII", "ICCID_PII", "MISC_PII"])
# For these PII categories, we assume that each appearance of the category in a transcript refers to the same underlying PII (e.g., same email address)
UNIQUE_CATEGORIES = set(["DATE_OF_BIRTH_PII", "LOCATION_ADDRESS_PII", "EMAIL_ADDRESS_PII"])


def pii_category_to_faker(category, levenshtein_treshold=0.79, real_pii=None, alphanumeric_mapping=None):
    # Helper function to map the PII categories to the corresponding faker function

    if category == "NAME_GIVEN_PII":
        return fake.first_name()
    elif category == "NAME_FAMILY_PII":
        return fake.last_name()
    elif category == "DATE_OF_BIRTH_PII":
        return  str(fake.date_of_birth(minimum_age=18, maximum_age=80))
    elif category == "LOCATION_ADDRESS_PII":
        return fake.street_address()
    elif category == "LOCATION_CITY_PII":
        return fake.city()
    elif category == "LOCATION_OTHER_PII":
        return choose_location_other(real_pii, levenshtein_treshold)
    elif category == "EMAIL_ADDRESS_PII":
        fake_email = fake.email()
        return fake_email.split("@")[0] + '@' + random.choice(EMAIL_DOMAINS)
    elif category == "AGE_PII":
        return str(fake.random_int(min=18, max=80))
    elif category == "ORGANIZATION_PII":
        return fake.company()
    elif category == "NATIONALITY_PII":
        return fake.random_element(elements=NATIONALITIES)
    elif category in CODE_BASED_CATEGORIES:
        return replace_alphanumeric_string(category, real_pii, alphanumeric_mapping)
    else:
        raise ValueError(f"PII category not supported:\nCATEGORY: {category}, PII: {real_pii}")


def create_alphanumeric_mapping():
    # Function to randomly create a fixed digit to digit and letter to letter mapping for coherent replacements within one transcript
    digit_mapping = list(range(10))
    random.shuffle(digit_mapping)
    letter_mapping = list(string.ascii_lowercase)
    random.shuffle(letter_mapping)
    return (tuple(digit_mapping), ''.join(letter_mapping))


def replace_alphanumeric_string(category, real_pii, alphanumeric_mapping):
    result = []
    spelled_out_pattern = re.compile(r"(?:" + "|".join(SPELLED_OUT_NUMBERS) + r")", re.IGNORECASE)
    spelled_out_matches = {match.start(): match for match in spelled_out_pattern.finditer(real_pii)}
    preserved_positions = set()
    digit_mapping = alphanumeric_mapping[0]
    letter_mapping = alphanumeric_mapping[1]

    def replace_spelled_out_number(match):
        original = match.group()
        digit = SPELLED_OUT_NUMBERS.index(original.lower())
        replacement = SPELLED_OUT_NUMBERS[digit_mapping[digit]]
        if original.isupper():
            return replacement.upper()
        if original.istitle():
            return replacement.title()
        return replacement

    # Preserve Dutch phone-prefix markers (06 or 6) at the start of the string.
    for token_index, token_match in enumerate(re.finditer(r"[^\W_]+", real_pii)):
        token = token_match.group().lower()
        if (token_index == 0 and token in {"0", "nul"}) or (
            token_index < 2 and token in {"6", "zes"}
        ):
            preserved_positions.update(range(token_match.start(), token_match.end()))

    position = 0
    while position < len(real_pii):
        match = spelled_out_matches.get(position)
        # If we find a spelled out number at the current position, handle it as a whole.
        if match:
            # Make sure to not replace spelled-out phone-prefix numbers.
            if category == "PHONE_NUMBER_PII" and position in preserved_positions:
                result.append(match.group())
            else:
                result.append(replace_spelled_out_number(match))
            position = match.end()
            continue

        # If not spelled-out number (no match), handle the character individually.
        char = real_pii[position]
        # Make sure to not replace phone-prefix digits.
        if category == "PHONE_NUMBER_PII" and position in preserved_positions:
            result.append(char)
        elif char.isdigit():
            result.append(str(digit_mapping[unicodedata.digit(char)]))
        elif char.isalpha():
            lowercase = char.lower()
            if lowercase in string.ascii_lowercase and len(lowercase) == 1:
                index = string.ascii_lowercase.index(lowercase)
            else:
                index = sum(ord(letter) for letter in char.casefold()) % len(letter_mapping)
            replacement = letter_mapping[index]
            result.append(replacement.upper() if char.isupper() else replacement)
        else:
            result.append(char)
        position += 1

    replaced = ''.join(result)
    # For LOCATION_ZIP_PII, names (phonetic spelling) should be replaced by new names instead of random letters
    if category == "LOCATION_ZIP_PII":
        replaced = re.sub(
            r"\b[^\W\d_]{3,}\b",
            lambda match: match.group() if match.group().lower() in SPELLED_OUT_NUMBERS
            else random.choice(ZIP_SPELLING_NAMES[match.group()[0].upper()]),
            replaced,
        )
    return replaced


def choose_dob_format(fake_dob, real_dob):
    # Helper function to use the same format for the fake date of birth as the real date of birth

    parts = fake_dob.split('-')
    # Remove leading zeros from each part of the date (day, month)
    parts = [part[1:] if part.startswith('0') else part for part in parts]

    day = parts[2]
    month_number = parts[1]
    month_name = MONTH_MAPPING.get(month_number, month_number)
    year = parts[0]
    year_last_two = year[-2:] if int(year) < 2000 else year

    dob_formats = {
        "day_only": day,
        "month_number_only": month_number,
        "month_name_only": month_name,
        "year_only": random.choice([year, year_last_two]),
        "day_month_number": f"{day} {month_number}",
        "day_month_name": f"{day} {month_name}",
        "month_number_year": f"{month_number} {random.choice([year, year_last_two])}",
        "month_name_year": f"{month_name} {random.choice([year, year_last_two])}",
        "day_month_number_year": f"{day} {month_number} {random.choice([year, year_last_two])}",
        "day_month_name_year": f"{day} {month_name} {random.choice([year, year_last_two])}" 
    }

    if len(real_dob.split()) == 1:
        if all(char.isalpha() for char in real_dob):
            return  dob_formats["month_name_only"]
        else:
            return random.choice([dob_formats["day_only"], dob_formats["month_number_only"], dob_formats["year_only"]])
    elif len(real_dob.split()) == 2:
        if any(char.isalpha() for char in real_dob):
            return random.choice([dob_formats["day_month_name"], dob_formats["month_name_year"]])
        else: 
            return random.choice([dob_formats["day_month_number"], dob_formats["month_number_year"]])
    else:
        if any(char.isalpha() for char in real_dob):
            return dob_formats["day_month_name_year"]
        else:
            return dob_formats["day_month_number_year"]


def choose_address_format(fake_address, real_address):
    # Helper function to use the same format for the fake address as the real address

    if all(char.isdigit() or char.isspace() for char in real_address):
        return ''.join(filter(str.isdigit, fake_address))
    elif all(char.isalpha() or char.isspace() for char in real_address):
        return ''.join(filter(str.isalpha, fake_address))
    else:
        return fake_address


def choose_location_other(real_location, levenshtein_treshold):
    # Create fake region and country different from the real location
    while True:
        fake_region = random.choice(REGIONS)
        fake_country = random.choice(COUNTRIES)
        if fake_region.lower() != real_location.lower() and fake_country.lower() != real_location.lower():
            break

    # If the real location is a region, replace with a region, otherwise with a country
    if process.extractOne(real_location, REGIONS, scorer=ratio, score_cutoff=levenshtein_treshold):
        return fake_region
    else:
        return fake_country


def choose_email_format(fake_email, real_email):
    # Helper function to use the same format for the fake email as the real email
    if "@" in real_email:
        return fake_email
    else:
        return fake_email.split("@")[0]


def check_if_asr_error(category, real_pii, levenshtein_treshold):
    """
    Function to check if a real PII is an ASR error by comparing it to the list of all known PII for that category using Levenshtein distance.
    Currently only supported for NAME_GIVEN_PII, NAME_FAMILY_PII, and LOCATION_CITY_PII.

    Args:
        category (str): The category of the real PII
        real_pii (str): The real PII to check
        levenshtein_treshold (float): Threshold for Levenshtein distance to consider two strings as similar
    
    Returns:
        bool: True if real_pii is an ASR error (no match found between real_pii and reference list that surpasses treshold), False otherwise
    """
    if category not in {"NAME_GIVEN_PII", "NAME_FAMILY_PII", "LOCATION_CITY_PII"}:
        raise ValueError(f"ASR error check not supported for category: {category}")

    if category == "NAME_GIVEN_PII":
        check_list = ALL_FIRST_NAMES
    elif category == "NAME_FAMILY_PII":
        check_list = ALL_LAST_NAMES
    elif category == "LOCATION_CITY_PII":
        check_list = ALL_CITIES

    if process.extractOne(real_pii, check_list, scorer=ratio, score_cutoff=levenshtein_treshold):
        return False
    else:
        return True


def create_fake_pii_from_annotations(annotations, levenshtein_treshold=0.79, seed=None):
    """
    Function to obtain fake PII for all annotations of a transcript
    
    Args:
        annotations (list): List of dictionaries containing the annotations of a transcript
        levenshtein_treshold (float): Threshold for Levenshtein distance to consider two strings as similar. Default is 0.79 (79% similarity).

    Returns:
        all_replacements (list): List of tuples containing the category, original PII, and the corresponding fake PII for each annotation in the transcript
    """
    if seed is not None:
        random.seed(seed)
        fake.seed_instance(seed)

    real_to_fake_mapping = {}
    all_replacements = []

    # Create a fake dob, address, and email only once for every transcript. We assume that all mentions in the dialogue refer to the same dob/address/email
    fake_dob = pii_category_to_faker("DATE_OF_BIRTH_PII")
    fake_address = pii_category_to_faker("LOCATION_ADDRESS_PII")
    fake_email = pii_category_to_faker("EMAIL_ADDRESS_PII")
    alphanumeric_mapping = create_alphanumeric_mapping()

    for annotation in annotations:
        category = annotation['category']
        real_pii = annotation['text']
        # For NON_PII, keep the original text
        if "NON-PII" in category:
            all_replacements.append(real_pii)
            continue

        seen_real_piis = list(real_to_fake_mapping.keys())
        # Match against previously seen PII to reuse replacements, except for the unique and code-based categories. These categories often contain entities that partially overlap, and similarity matching could lead to incorrectly replacing these all with the exact same fake PII. Their category-specific handlers create replacements that match the original format.
        if process.extractOne(real_pii.lower(), seen_real_piis, scorer=ratio, score_cutoff=levenshtein_treshold) and category not in (UNIQUE_CATEGORIES | CODE_BASED_CATEGORIES):
            # If match is found, we ensure that the same fake_pii is used again for replacing the same real_pii
            matched_seen_pii, _ = process.extractOne(real_pii.lower(), seen_real_piis, scorer=ratio, score_cutoff=levenshtein_treshold)
            fake_pii = real_to_fake_mapping[matched_seen_pii]
            # Ensure case consistency between fake and real PII
            fake_pii = fake_pii.lower() if real_pii.islower() else fake_pii.upper() if real_pii.isupper() else fake_pii.title() if real_pii.istitle() else fake_pii
            all_replacements.append(fake_pii)
            continue
            
        # Else, we assume we have not seen this real_pii before
        if category == "DATE_OF_BIRTH_PII":
            fake_pii = choose_dob_format(fake_dob, real_pii)
        elif category == "LOCATION_ADDRESS_PII":
            fake_pii = choose_address_format(fake_address, real_pii)
        elif category == "EMAIL_ADDRESS_PII":
            fake_pii = choose_email_format(fake_email, real_pii)
        # Categories for which we have a reference list to check if the real PII is an ASR error, in which case we keep the original PII (no replacement necessary)
        elif category in ["NAME_GIVEN_PII", "NAME_FAMILY_PII", "LOCATION_CITY_PII"]:
            if check_if_asr_error(category, real_pii, levenshtein_treshold):
                fake_pii = real_pii
            else:
                fake_pii = pii_category_to_faker(category, levenshtein_treshold, real_pii)
                fake_pii = fake_pii.lower() if real_pii.islower() else fake_pii.upper() if real_pii.isupper() else fake_pii.title() if real_pii.istitle() else fake_pii
        else:
            fake_pii = pii_category_to_faker(category, levenshtein_treshold, real_pii, alphanumeric_mapping)
            # Ensure case consistency between fake and real PII
            fake_pii = fake_pii.lower() if real_pii.islower() else fake_pii.upper() if real_pii.isupper() else fake_pii.title() if real_pii.istitle() else fake_pii

        real_to_fake_mapping[real_pii.lower()] = fake_pii
        all_replacements.append(fake_pii)

    return all_replacements


def create_anonymized_transcript_and_labels(original_transcript, original_annotations, fake_piis):
    """
    Function to anonymize the original transcript by replacing the original PII with the corresponding fake PII (1) and create new labels with the fake PII and updated span indices (2)
    """
    anonymized_transcript = list(original_transcript)
    fake_pii_labels = []
    cumulative_offset = 0

    for original_annotation, new_pii in zip(original_annotations, fake_piis):
        new_start = original_annotation['beginningIndex'] + cumulative_offset
        new_end = new_start + len(new_pii)  # end = start + length of replacement

        # Replace in the string using the offset-adjusted start position
        orig_start = original_annotation['beginningIndex'] + cumulative_offset
        orig_end = original_annotation['endIndex'] + cumulative_offset
        anonymized_transcript = anonymized_transcript[:orig_start] + list(new_pii) + anonymized_transcript[orig_end:]

        # Update offset AFTER computing new_end
        cumulative_offset += len(new_pii) - len(original_annotation['text'])

        fake_pii_labels.append({
            'text': new_pii,
            'beginningIndex': new_start,
            'endIndex': new_end,
            'category': original_annotation['category']
        })

    return ''.join(anonymized_transcript), fake_pii_labels

print(create_fake_pii_from_annotations([{"text":"32. 32 Leo Eluard","beginningIndex":2030,"endIndex":2047,"category":"LOCATION_ZIP_PII"}], seed=42))