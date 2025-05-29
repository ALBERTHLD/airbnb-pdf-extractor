import streamlit as st
import pdfplumber
import re
import xml.etree.ElementTree as ET
import tempfile

# Foruddefinerede værdier
CATEGORIES = ["Entire Place", "Private Room", "Hotel Room", "Shared Room"]
AMENITIES = ["Pets Allowed", "TV", "Air Conditioning", "Dedicated workspace", "Washing Machine", "Dryer", "Hair Dryer", "Iron"]
FEATURES = ["Internet", "Pool", "Hot tub", "EV charger", "Cot", "King size bed", "Gym", "BBQ grill", "Smoking allowed", "Wheelchair access"]
KITCHENS = ["Full kitchen", "Shared", "Kitchenette", "Outdoor", "No kitchen available"]
PARKINGS = ["Free parking on premises", "Free parking nearby", "Paid parking on premises", "Paid parking nearby", "No parking available"]
SAFETY = ["Smoke alarm", "Carbon monoxide alarm", "Exterior security cameras on property"]
PROPERTY_TYPES = ["Apartment", "Bed & Breakfast", "Cabin", "Condo", "Guest House", "Hostel", "Hotel", "House", "House Boat", "Resort", "Other"]
LOCATIONS = ["Beachfront", "City Center", "Countryside", "Outside of City Center", "Other"]

# Hjælpefunktioner
def extract_first_match(text, options):
    for option in options:
        if option.lower() in text.lower():
            return option
    return ""

def extract_all_matches(text, options):
    return [opt for opt in options if opt.lower() in text.lower()]

def extract_first_number(text):
    match = re.search(r"\d+", text)
    return match.group(0) if match else ""

def extract_urls(text):
    return re.findall(r"https?://\S+", text)

def parse_pdf(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

def extract_section(text, section_title, next_titles):
    pattern = rf"{section_title}\s*:(.*?)(?=(" + "|".join(map(re.escape, next_titles)) + r")\s*:)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""

def extract_field(text, label):
    match = re.search(rf"{label}\s*:\s*(.+)", text, re.IGNORECASE)
    return match.group(1).strip() if match else ""

def extract_data(text):
    return {
        "Category": extract_first_match(text, CATEGORIES),
        "Title": extract_field(text, "Listing title"),
        "Description": extract_field(text, "Listing description"),
        "NumberOfGuests": extract_first_number(extract_field(text, "Number of guests")),
        "MinimumStay": extract_first_number(extract_field(text, "Minimum Stay")),
        "Amenities": extract_all_matches(extract_section(text, "Amenities", ["Features", "Kitchen"]), AMENITIES),
        "Features": extract_all_matches(extract_section(text, "Features", ["Kitchen", "Parking"]), FEATURES),
        "Kitchen": extract_first_match(extract_section(text, "Kitchen", ["Parking", "House Rules"]), KITCHENS),
        "Parking": extract_first_match(extract_section(text, "Parking", ["House Rules", "Cancellation Policy"]), PARKINGS),
        "HouseRules": extract_section(text, "House Rules", ["Cancellation Policy"]),
        "CancellationPolicy": extract_section(text, "Cancellation Policy", ["Safety & Property"]),
        "SafetyAndProperty": extract_all_matches(extract_section(text, "Safety & Property", ["Property Type"]), SAFETY),
        "PropertyType": extract_first_match(extract_section(text, "Property Type", ["Location"]), PROPERTY_TYPES),
        "Location": extract_first_match(extract_section(text, "Location", ["Links to this listing"]), LOCATIONS),
        "ExternalLinks": extract_urls(text),
        "PricePerNight": extract_first_number(extract_field(text, "Price per night")),
    }

def generate_xml(data):
    root = ET.Element("Listing")
    fields = [
        "Category", "Title", "Description", "NumberOfGuests", "MinimumStay",
        "Amenities", "Features", "Kitchen", "Parking",
        "HouseRules", "CancellationPolicy", "SafetyAndProperty",
        "PropertyType", "Location", "ExternalLinks", "PricePerNight"
    ]

    for key in fields:
        value = data[key]
        if isinstance(value, list):
            ET.SubElement(root, key).text = ", ".join(value)
        elif isinstance(value, str):
            ET.SubElement(root, key).text = value
        else:
            ET.SubElement(root, key).text = ""

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp:
        tree = ET.ElementTree(root)
        tree.write(tmp.name, encoding="utf-8", xml_declaration=True)
        return tmp.name

# Streamlit UI
st.set_page_config(page_title="Airbnb PDF Extractor", layout="centered")
st.title("🏡 Airbnb PDF Extractor")

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
