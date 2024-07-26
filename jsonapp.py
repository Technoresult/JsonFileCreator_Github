import os
import streamlit as st
import json
import re
import requests
import base64
from datetime import datetime

#Function to generate filename with date
def generate_filename(metal_type):
    today = datetime.now().strftime("%Y-%m-%d")
    return f"{metal_type[0].upper()}_{today}.json"

#New funciton Test

def table_to_json(table_data, metal_type):
    if metal_type == "Gold":
        # Update the regular expression to match the new order: 22K first, then 24K, and then 18K
        parts = re.findall(r'(\w+)\s+(₹\s*[\d,.]+)\s+(₹\s*[\d,.]+)\s+(₹\s*[\d,.]+)', table_data)
        
        gold_prices = []
        
        for city, price_22k, price_24k, price_18k in parts:
            try:
                city_dict = {
                    "City": city,
                    "24K Today": price_24k.strip(),
                    "22K Today": price_22k.strip(),
                    "18K Today": price_18k.strip()
                }
                gold_prices.append(city_dict)
            except ValueError:
                st.warning(f"Skipping invalid data for city: {city}, prices: {price_24k}, {price_22k}, {price_18k}")
        
        return {"gold_prices": gold_prices}
    else:
        parts = re.findall(r'(\w+)\s+(₹\s*[\d,.]+)\s+(₹\s*[\d,.]+)\s+(₹\s*[\d,.]+)', table_data)
        
        silver_rates = []
        
        for city, price_10g, price_100g, price_1kg in parts:
            try:
                city_dict = {
                    "city": city,
                    "10_gram": price_10g.strip(),
                    "100_gram": price_100g.strip(),
                    "1_kg": price_1kg.strip()
                }
                silver_rates.append(city_dict)
            except ValueError:
                st.warning(f"Skipping invalid data for city: {city}, prices: {price_10g}, {price_100g}, {price_1kg}")
        
        return {"silver_rates": silver_rates}
#upload to GitHub Function
def upload_to_github(repo, path, token, content, message="Upload JSON file"):
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "message": message,
        "content": base64.b64encode(content.encode('utf-8')).decode('utf-8')
    }
    
    # First, try to get the file (to update it if it exists)
    get_response = requests.get(url, headers=headers)
    if get_response.status_code == 200:
        file_sha = get_response.json()['sha']
        data['sha'] = file_sha
    
    response = requests.put(url, headers=headers, json=data)
    return response

st.title("Precious Metal Price Data Converter")

# Initialize session state variables
if 'github_repo' not in st.session_state:
    st.session_state.github_repo = ""
if 'github_path' not in st.session_state:
    st.session_state.github_path = ""
if 'github_token' not in st.session_state:
    st.session_state.github_token = ""
if 'json_string' not in st.session_state:
    st.session_state.json_string = ""

metal_type = st.selectbox("Select metal type:", ["Gold", "Silver"])

st.write(f"Paste your {metal_type.lower()} price data below. The format should be:")
if metal_type == "Gold":
    st.code("City ₹ 24K_price ₹ 22K_price ₹ 18K_price")
else:
    st.code("City ₹ 10gram_price ₹ 100gram_price ₹ 1kg_price")

table_data = st.text_area("Paste your data here:", height=200)

if st.button("Convert to JSON"):
    if table_data:
        json_data = table_to_json(table_data, metal_type)
        
        st.write("Converted JSON data:")
        st.json(json_data, expanded=True)
        
        st.session_state.json_string = json.dumps(json_data, indent=2, ensure_ascii=False).encode('utf-8').decode('utf-8')
        filename = generate_filename(metal_type)
        st.download_button(
            label="Download JSON",
            file_name=f"{metal_type.lower()}_prices.json",
            mime="application/json",
            data=st.session_state.json_string,
        )
    else:
        st.warning("Please paste some data before converting.")

# GitHub upload section
st.write("Upload to GitHub")

with st.form(key='github_upload_form'):
    repo = st.text_input("GitHub Repo (e.g., username/repo)", value=st.session_state.github_repo, key="repo_input")
    filename = generate_filename(metal_type)
    path = st.text_input("File Path in Repo (e.g., data/metal_prices.json)", value=f"Folder/{filename}", key="path_input")
    token = st.text_input("GitHub Access Token", type="password", value=st.session_state.github_token, key="token_input")
    
    submit_button = st.form_submit_button(label="Upload to GitHub")

# In the form submission handling section, update the error message:
if submit_button:
    if repo and path and token and st.session_state.json_string:
        # Update session state
        st.session_state.github_repo = repo
        st.session_state.github_path = path
        st.session_state.github_token = token
        
        # Perform the upload
        response = upload_to_github(repo, path, token, st.session_state.json_string)
        if response.status_code == 201 or response.status_code == 200:
            st.success("File uploaded successfully!")
        else:
            error_message = response.json().get('message', 'Unknown error')
            st.error(f"Failed to upload file. Status code: {response.status_code}. Error: {error_message}")
            st.error(f"Full response: {response.text}")
    else:
        if not st.session_state.json_string:
            st.warning("Please convert data to JSON before uploading.")
        else:
            st.warning("Please provide all required GitHub details.")

st.write("Note: Make sure your data is in the correct format. Each city should be on a new line or separated by spaces.")

st.write("Example data:")
if metal_type == "Gold":
    example_data = """
    Chennai ₹ 7,452 ₹ 6,831 ₹ 5,596
    Mumbai ₹ 7,403 ₹ 6,786 ₹ 5,553
    Delhi ₹ 7,418 ₹ 6,800 ₹ 5,564
    Kolkata ₹ 7,403 ₹ 6,786 ₹ 5,553
    """
else:
    example_data = """
    Chennai ₹ 977.50 ₹ 9,775 ₹ 97,750 
    Mumbai ₹ 932.50 ₹ 9,325 ₹ 93,250
    Delhi ₹ 932.50 ₹ 9,325 ₹ 93,250
    Kolkata ₹ 932.50 ₹ 9,325 ₹ 93,250
    """
st.code(example_data)
