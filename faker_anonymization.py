from faker import Faker
import random
from Levenshtein import ratio
from fuzzywuzzy import process
import json
from os.path import dirname, join

from faker.providers.address.nl_NL import Provider as NLLocation
all_cities = list(NLLocation.cities)

references_path= join(dirname(__file__), "deidentify", "surrogates", "generators", "resources")
with open(join(references_path, "lastnames.csv"), "r", encoding="utf-8") as f:
    all_last_names = [line.replace(',', ' ').strip() for line in f.readlines()[1:]]  # Skip the header line

with open(join(references_path, "firstnames_male.txt"), "r", encoding="utf-8") as f:
    all_male_names = [line.strip() for line in f.readlines()]

with open(join(references_path, "firstnames_female.txt"), "r", encoding="utf-8") as f:
    all_female_names = [line.strip() for line in f.readlines()]

all_first_names = all_male_names + all_female_names


fake = Faker('nl_NL')


# Month number to name mapping
month_mapping = {
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

email_domain_list = ["gmail.com", "hotmail.com", "outlook.com", "yahoo.com", "icloud.com", "protonmail.com", "aol.com", "zoho.com", "gmx.com", "mail.com"]


def pii_category_to_faker(category):
    # Helper function to map the PII categories to the corresponding faker function

    if category == "NAME_GIVEN_PII":
        return fake.first_name()
    elif category == "NAME_FAMILY_PII":
        return fake.last_name()
    elif category == "DATE_OF_BIRTH_PII":
        return  str(fake.date_of_birth(minimum_age=18, maximum_age=80))
    elif category == "LOCATION_ADDRESS_PII":
        return fake.street_address()
    elif category == "LOCATION_ZIP_PII":
        # Create fake names to use for the zipcode  phonetic spelling
        return [fake.postcode(), fake.first_name(), fake.first_name()]
    elif category == "LOCATION_CITY_PII":
        return fake.city()
    elif category == "LOCATION_OTHER_PII":
        fake_country = fake.country()
        fake_province = fake.province()
        #return random.choice([fake_country, fake_province])
        return fake_province
    elif category == "EMAIL_ADDRESS_PII":
        fake_email = fake.email()
        return fake_email.split("@")[0] + '@' + random.choice(email_domain_list)
    elif category == "AGE_PII":
        return str(fake.random_int(min=18, max=80))
    elif category == "ORGANIZATION_PII":
        return fake.company()
    else:
        return None


def choose_dob_format(fake_dob, real_dob):
    # Helper function to use the same format for the fake date of birth as the real date of birth

    parts = fake_dob.split('-')

    day = parts[2]
    month_number = parts[1]
    month_name = month_mapping.get(month_number, month_number)
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


def choose_zip_format(fake_zip, real_zip):
    # Helper function to use the same format for the fake zip as the real zip

    fake_zip_digits = fake_zip[0]
    # Remove letters (characters 5 and 6) from zip created by fake.postcode(), we want to use the first letters from the complete names created with fake.first_name()
    fake_zip_digits = fake_zip_digits[:4]
    fake_name_one = fake_zip[1]
    fake_name_two = fake_zip[2]

    # Decide digit format to use
    digit_count = sum(char.isdigit() for char in real_zip)
    if digit_count == 0:
        digits = ""
    elif digit_count == 1:
        # Randomly pick 1 digit from fake
        digits = random.choice([digit for digit in fake_zip_digits])
    elif digit_count == 2:
        # Randomly pick first 2 or last 2 fake digits
        digits = random.choice([fake_zip_digits[:2], fake_zip_digits[2:]])
    elif digit_count == 3:
        # Randomly pick first 3 or last 3 fake digits
        digits = random.choice([fake_zip_digits[:3], fake_zip_digits[1:]])
    else:
        # Else we assume real_zip contains all (4) digits
        digits = fake_zip_digits

    # Decide letter format to use
    letter_count = sum(char.isalpha() for char in real_zip)
    word_count = len([word for word in real_zip.split() if not any(char.isdigit() for char in word)])
    # No letters means only digits
    if letter_count == 0:
        letters = ""
     # 1 letter means only 1 initial
    elif letter_count == 1:
        letters = random.choice([fake_name_one[0], fake_name_two[0]])
    # 2 letters means 2 initials
    elif letter_count == 2:
        letters = fake_name_one[0] + fake_name_two[0]
    # 0 (word attached to digits) or 1 word (and more than 2 letters) means 1 name
    elif word_count == 0 or word_count == 1:
        letters = random.choice([fake_name_one, fake_name_two])
    # 2 or more words (and more than 2 letters) means 2 names
    elif word_count >= 2:
        letters = fake_name_one + " " + fake_name_two

    # If either digits or letters is empty, do not add a space between them
    if digits == "" or letters == "":
        return digits + letters
    # Check if there is no space between digits and letters in real_zip by checking if there is any element containing both digits and letters
    elif any(any(char.isdigit() for char in word) and any(char.isalpha() for char in word) for word in real_zip.split()):
        return digits + letters
    else:
        return digits + " " + letters


def replace_digits(real_pii):
    # Function to replace digits in a string with random digits, but keep '06' and '0 6' at the beginning of a string unchanged (for Dutch phone numbers)
    digits = '0123456789'
    result = []
    for index, char in enumerate(real_pii):
        if char in {'0', '6'} and index < 3:
            result.append(char)
        elif char.isdigit():
            replacement_digits = [d for d in digits if d != char]
            result.append(random.choice(replacement_digits))
        else:
            result.append(char)
    return ''.join(result)


def check_if_asr_error(real_pii, category, levenshtein_treshold):
    """
    Function to check if a real PII is an ASR error by comparing it to the list of all known PII for that category using Levenshtein distance

    Args:
        real_pii (str): The real PII to check
        category (str): The category of the real PII
        levenshtein_treshold (float): Threshold for Levenshtein distance to consider two strings as similar
    
    Returns:
        bool: True if real_pii is an ASR error (no match found between real_pii and reference list that surpasses treshold), False otherwise
    """

    if category == "NAME_GIVEN_PII":
        check_list = all_first_names
    elif category == "NAME_FAMILY_PII":
        check_list = all_last_names
    elif category == "LOCATION_CITY_PII":
        check_list = all_cities

    if process.extractOne(real_pii, check_list, scorer=ratio, score_cutoff=levenshtein_treshold):
        return False
    else:
        return True


def create_fake_pii_from_annotations(annotations, levenshtein_treshold=0.79):
    """
    Function to obtain fake PII for all annotations of a transcript
    
    Args:
        annotations (list): List of dictionaries containing the annotations of a transcript
        levenshtein_treshold (float): Threshold for Levenshtein distance to consider two strings as similar. Default is 0.79 (79% similarity).

    Returns:
        all_replacements (list): List of tuples containing the category, original PII, and the corresponding fake PII for each annotation in the transcript
    """
    real_to_fake_mapping = {}
    all_replacements = []

    # Create a fake dob, address, and zipcode only once for every transcript. We assume that all mentions in the dialogue refer to the same dob/address/zipcode
    fake_dob = pii_category_to_faker("DATE_OF_BIRTH_PII")
    fake_zip = pii_category_to_faker("LOCATION_ZIP_PII")
    fake_address = pii_category_to_faker("LOCATION_ADDRESS_PII")

    for annotation in annotations:
        category = annotation['category']
        real_pii = annotation['text']
        # For NON_PII, keep the orignal text
        if "NON-PII" in category:
            all_replacements.append((category, real_pii, real_pii))
        else:
            seen_real_piis = list(real_to_fake_mapping.keys())
            # Compute Levenshtein distance between real_pii and previously seen real piis, except for DOB, ZIP, and ADDRESS, which are often uttured in multiple overlapping parts in a transcript. This would otherwise often result in these partial utterances matching with each other, causing them to all be replaced by the same PII. However, we replace these real PII by fake PII following the same format as the real PII, as can be seen in the choose_dob_format, choose_zip_format, and choose_address_format functions.
            if process.extractOne(real_pii.lower(), seen_real_piis, scorer=ratio, score_cutoff=levenshtein_treshold) and category not in ["DATE_OF_BIRTH_PII", "LOCATION_ZIP_PII", "LOCATION_ADDRESS_PII"]:
                # If match is found, we ensure that the same fake_pii is used again for replacing the same real_pii
                matched_seen_pii, _ = process.extractOne(real_pii.lower(), seen_real_piis, scorer=ratio, score_cutoff=levenshtein_treshold)
                fake_pii = real_to_fake_mapping[matched_seen_pii]
                # Ensure case consistency between fake and real PII
                fake_pii = fake_pii.lower() if real_pii.islower() else fake_pii.upper() if real_pii.isupper() else fake_pii.title() if real_pii.istitle() else fake_pii
                all_replacements.append((category, real_pii, fake_pii))
                
            # Else, we assume we have not seen this real_pii before
            else:
                if category == "DATE_OF_BIRTH_PII":
                    fake_pii = choose_dob_format(fake_dob, real_pii)
                elif category == "LOCATION_ZIP_PII":
                    fake_pii = choose_zip_format(fake_zip, real_pii)
                elif category == "LOCATION_ADDRESS_PII":
                    fake_pii = choose_address_format(fake_address, real_pii)
                elif category == "PHONE_NUMBER_PII":
                    fake_pii = replace_digits(real_pii)
                # Categories for which we have a reference list to check if the real PII is an ASR error, in which case we keep the original PII
                elif category in ["NAME_GIVEN_PII", "NAME_FAMILY_PII", "LOCATION_CITY_PII"]:
                    if check_if_asr_error(real_pii, category, levenshtein_treshold):
                        fake_pii = real_pii
                    else:
                        fake_pii = pii_category_to_faker(category)
                        fake_pii = fake_pii.lower() if real_pii.islower() else fake_pii.upper() if real_pii.isupper() else fake_pii.title() if real_pii.istitle() else fake_pii
                else:
                    fake_pii = pii_category_to_faker(category)
                    # Ensure case consistency between fake and real PII
                    fake_pii = fake_pii.lower() if real_pii.islower() else fake_pii.upper() if real_pii.isupper() else fake_pii.title() if real_pii.istitle() else fake_pii

                real_to_fake_mapping[real_pii.lower()] = fake_pii
                all_replacements.append((category, real_pii, fake_pii))

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

