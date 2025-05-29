import streamlit as st
import pdfplumber
import re
import xml.etree.ElementTree as ET
import tempfile

# Predefined keyword lists
AMENITIES = ["Pets Allowed", "TV", "Air Conditioning", "Dedicated workspace", "Washing Machine", "Dryer", "Hair Dryer", "Iron"]
FEATURES = ["Internet", "Pool", "Hot tub", "EV charger", "Cot", "King size bed", "Gym", "BBQ grill", "Smoking allowed", "Wheelchair access"]
KITCHENS = ["Full kitchen", "Shared kitchen", "Kitchenette", "Outdoor kitchen", "No kitchen"]
PARKINGS = ["Free parking on premises", "Free parking nearby", "Paid parking on premises", "Paid parking nearby", "No parking"]
SAFETY = ["Smoke alarm", "Carbon monoxide alarm", "Exterior security cameras"]
PROPERTY_TYPES = ["Apartment", "Bed & Breakfast", "Cabin", "Condo", "Guest House", "Hostel", "Hotel", "House", "House Boat", "Resort", "Other"]
LOCATIONS = ["Beachfront", "City Center", "Countryside", "Outside of City Center", "Other"]

def parse_pdf(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

def guess_title_and_description(lines):
    title = ""
    description = ""
    for line in lines:
        if len(line.strip()) > 10 and not title:
            title = line.strip()
            continue
        if len(description) < 300 and len(line.strip()) > 30:
            description += line.strip() + " "
    return title.strip(), description.strip()

def guess_number_of_guests(text):
    match = re.search(r"(sleeps|for)\s+(\d+)", text, re.IGNORECASE)
    return match.group(2) if match else ""

def guess_price(text):
    match = re.search(r"(kr|€|\\$)?\\s*(\\d{2,5})\\s*(per night|/night|per dag)?", text, re.IGNORECASE)
    return match.group(2) if match else ""

def extract_items(text, keywords):
    found = [kw for kw in keywords if kw.lower() in text.lower()]
    return found

def extract_data(text):
    lines = text.splitlines()
    title, description = guess_title_and_description(lines)

    return {
        "Category": "",  # Heuristik kan forbedres med mere domænespecifik træning
        "Title": title,
        "Description": description,
        "NumberOfGuests": guess_number_of_guests(text),
        "MinimumStay": "",  # Mangler ofte tydelig tekst
        "Amenities": extract_items(text, AMENITIES),
        "Features": extract_items(text, FEATURES),
        "Kitchen": next((k for k in KITCHENS if k.lower() in text.lower()), ""),
        "Parking": next((p for p in PARKINGS if p.lower() in text.lower()), ""),
        "HouseRules": "",  # Kan tilføjes med sektion-markering senere
        "CancellationPolicy": "",  # Samme her
        "SafetyAndProperty": extract_items(text, SAFETY),
        "PropertyType": next((pt for pt in PROPERTY_TYPES if pt.lower() in text.lower()), ""),
        "Location": next((l for l in LOCATIONS if l.lower() in text.lower()), ""),
        "ExternalLinks": re.findall(r"https?://\\S+", text),
        "PricePerNight": guess_price(text),
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

# Streamlit UI
st.set_page_config(page_title="Airbnb PDF Extractor", layout="centered")
st.title("🏡 Airbnb PDF Extractor v.3 (Heuristik-version)")

uploaded_file = st.file_uploader("Upload en PDF med boligoplysninger", type=["pdf"])

if uploaded_file:
    with st.spinner("🔍 Læser og analyserer PDF..."):
        text = parse_pdf(uploaded_file)
        data = extract_data(text)
        xml_file = generate_xml(data)

    st.success("✅ Data udtrukket!")

    st.subheader("🔎 Uddraget information:")
    for key, val in data.items():
        if isinstance(val, list):
            st.markdown(f"**{key}**: {', '.join(val)}")
        else:
            st.markdown(f"**{key}**: {val}")

    with open(xml_file, "rb") as f:
        st.download_button("📥 Download XML", f, file_name="listing_output.xml", mime="application/xml")
