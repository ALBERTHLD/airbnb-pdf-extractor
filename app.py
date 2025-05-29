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

# Funktionshjælpere
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

def extract_data(text):
    return {
        "Category": extract_first_match(text, CATEGORIES),
        "Title": re.search(r"(?i)(title|listing title):\s*(.*)", text),
        "Description": re.search(r"(?i)(description):\s*(.*)", text),
        "NumberOfGuests": extract_first_number(re.search(r"guests?:.*", text, re.IGNORECASE).group(0)) if re.search(r"guests?:.*", text, re.IGNORECASE) else "",
        "MinimumStay": extract_first_number(re.search(r"minimum stay.*", text, re.IGNORECASE).group(0)) if re.search(r"minimum stay.*", text, re.IGNORECASE) else "",
        "Amenities": extract_all_matches(text, AMENITIES),
        "Features": extract_all_matches(text, FEATURES),
        "Kitchen": extract_first_match(text, KITCHENS),
        "Parking": extract_first_match(text, PARKINGS),
        "HouseRules": re.search(r"(?i)house rules:\s*(.*?)(?=\n[A-Z])", text, re.DOTALL),
        "CancellationPolicy": re.search(r"(?i)cancellation policy:\s*(.*?)(?=\n[A-Z])", text, re.DOTALL),
        "SafetyAndProperty": extract_all_matches(text, SAFETY),
        "PropertyType": extract_first_match(text, PROPERTY_TYPES),
        "Location": extract_first_match(text, LOCATIONS),
        "ExternalLinks": extract_urls(text),
        "PricePerNight": extract_first_number(re.search(r"price.*?(\d+)", text, re.IGNORECASE).group(0)) if re.search(r"price.*?(\d+)", text, re.IGNORECASE) else "",
    }

def generate_xml(data):
    root = ET.Element("Listing")
    ET.SubElement(root, "Category").text = data["Category"]
    ET.SubElement(root, "Title").text = data["Title"].group(2).strip() if data["Title"] else ""
    ET.SubElement(root, "Description").text = data["Description"].group(2).strip() if data["Description"] else ""
    ET.SubElement(root, "NumberOfGuests").text = data["NumberOfGuests"]
    ET.SubElement(root, "MinimumStay").text = data["MinimumStay"]
    ET.SubElement(root, "Amenities").text = ", ".join(data["Amenities"])
    ET.SubElement(root, "Features").text = ", ".join(data["Features"])
    ET.SubElement(root, "Kitchen").text = data["Kitchen"]
    ET.SubElement(root, "Parking").text = data["Parking"]
    ET.SubElement(root, "HouseRules").text = data["HouseRules"].group(1).strip() if data["HouseRules"] else ""
    ET.SubElement(root, "CancellationPolicy").text = data["CancellationPolicy"].group(1).strip() if data["CancellationPolicy"] else ""
    ET.SubElement(root, "SafetyAndProperty").text = ", ".join(data["SafetyAndProperty"])
    ET.SubElement(root, "PropertyType").text = data["PropertyType"]
    ET.SubElement(root, "Location").text = data["Location"]
    ET.SubElement(root, "ExternalLinks").text = "\n".join(data["ExternalLinks"])
    ET.SubElement(root, "PricePerNight").text = data["PricePerNight"]
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp:
        tree = ET.ElementTree(root)
        tree.write(tmp.name, encoding="utf-8", xml_declaration=True)
        return tmp.name

# Streamlit UI
st.set_page_config(page_title="Airbnb PDF Extractor", layout="centered")

st.markdown("""
<style>
h1 {
    color: #ff5a5f;
    font-family: 'Helvetica Neue', sans-serif;
    text-align: center;
}
.stButton button {
    background-color: #ff5a5f;
    color: white;
    font-weight: bold;
    border-radius: 8px;
}
.stMarkdown {
    font-family: 'Arial', sans-serif;
}
</style>
""", unsafe_allow_html=True)

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
        elif isinstance(val, str):
            st.markdown(f"**{key}**: {val}")
        elif val and hasattr(val, "group"):
            st.markdown(f"**{key}**: {val.group(2).strip() if key in ['Title', 'Description'] else val.group(1).strip()}")

    with open(xml_file, "rb") as f:
        st.download_button("📥 Download XML", f, file_name="listing_output.xml", mime="application/xml")
