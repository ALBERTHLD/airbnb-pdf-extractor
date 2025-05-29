import streamlit as st
import pdfplumber
import re
import xml.etree.ElementTree as ET
import tempfile

AMENITIES = ["Pets Allowed", "TV", "Air Conditioning", "Dedicated workspace", "Washing Machine", "Dryer", "Hair Dryer", "Iron"]
FEATURES = ["Internet", "Pool", "Hot tub", "EV charger", "Cot", "King size bed", "Gym", "BBQ grill", "Smoking allowed", "Wheelchair access"]
KITCHENS = ["Full kitchen", "Shared kitchen", "Kitchenette", "Outdoor kitchen", "No kitchen"]
PARKINGS = ["Free parking on premises", "Free parking nearby", "Paid parking on premises", "Paid parking nearby", "No parking"]
SAFETY = ["Smoke alarm", "Carbon monoxide alarm", "Exterior security cameras"]
PROPERTY_TYPES = ["Apartment", "Bed & Breakfast", "Cabin", "Condo", "Guest House", "Hostel", "Hotel", "House", "House Boat", "Resort", "Other"]
LOCATIONS = ["Beachfront", "City Center", "Countryside", "Outside of City Center", "Other"]

def extract_text_and_words(uploaded_file):
    all_text = ""
    all_words = []
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            words = page.extract_words()
            if text:
                all_text += text + "\n"
            all_words.extend(words)
    return all_text, all_words

def extract_title_and_price(words):
    title_words = [w["text"] for w in words if w["top"] < 200 and len(w["text"]) > 3]
    full_line = " ".join(title_words)
    price_match = re.search(r"(\\d{2,5})\\s*(kr|DKK|€|\\$)", full_line)
    title = re.sub(r"(\\d{2,5})\\s*(kr|DKK|€|\\$).*", "", full_line).strip()
    price = price_match.group(1) if price_match else ""
    return title, price

def extract_description(words):
    lines = {}
    for w in words:
        top = round(w["top"] / 10) * 10
        lines.setdefault(top, []).append(w["text"])
    sorted_lines = [" ".join(lines[t]) for t in sorted(lines.keys())]
    description = ""
    for line in sorted_lines:
        if any(word in line.lower() for word in ["faciliteter", "omtaler", "beliggenhed", "reservation"]):
            break
        if len(line.strip()) > 30:
            description += line.strip() + " "
    return description.strip()

def extract_list_matches(words, items):
    found = set()
    word_texts = [w["text"].lower() for w in words]
    for item in items:
        if item.lower() in word_texts:
            found.add(item)
    return list(found)

def extract_first_number_from_text(text):
    match = re.search(r"\\d+", text)
    return match.group(0) if match else ""

def extract_data(text, words):
    title, price = extract_title_and_price(words)
    description = extract_description(words)

    return {
        "Category": "",
        "Title": title,
        "Description": description,
        "NumberOfGuests": extract_first_number_from_text(text),
        "MinimumStay": "",
        "Amenities": extract_list_matches(words, AMENITIES),
        "Features": extract_list_matches(words, FEATURES),
        "Kitchen": next((k for k in KITCHENS if k.lower() in text.lower()), ""),
        "Parking": next((p for p in PARKINGS if p.lower() in text.lower()), ""),
        "HouseRules": "",
        "CancellationPolicy": "",
        "SafetyAndProperty": extract_list_matches(words, SAFETY),
        "PropertyType": next((pt for pt in PROPERTY_TYPES if pt.lower() in text.lower()), ""),
        "Location": next((loc for loc in LOCATIONS if loc.lower() in text.lower()), ""),
        "ExternalLinks": re.findall(r"https?://\\S+", text),
        "PricePerNight": price
    }

def generate_xml(data):
    root = ET.Element("Listing")
    for key in [
        "Category", "Title", "Description", "NumberOfGuests", "MinimumStay",
        "Amenities", "Features", "Kitchen", "Parking",
        "HouseRules", "CancellationPolicy", "SafetyAndProperty",
        "PropertyType", "Location", "ExternalLinks", "PricePerNight"
    ]:
        val = data[key]
        if isinstance(val, list):
            ET.SubElement(root, key).text = ", ".join(val)
        else:
            ET.SubElement(root, key).text = val or ""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp:
        tree = ET.ElementTree(root)
        tree.write(tmp.name, encoding="utf-8", xml_declaration=True)
        return tmp.name

# UI
st.set_page_config(page_title="Airbnb PDF Extractor", layout="centered")
st.title("📄 Airbnb PDF Extractor v.4 (Layout-intelligent)")

uploaded_file = st.file_uploader("Upload en PDF med boligoplysninger", type=["pdf"])

if uploaded_file:
    wit
