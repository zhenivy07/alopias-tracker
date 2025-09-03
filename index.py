import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import json
import os
import time
from datetime import datetime

species_list = [
    "Alopias vulpinus",
    "Alopias pelagicus",
    "Alopias superciliosus"
]

species_colors = {
    "Alopias vulpinus": "red",
    "Alopias pelagicus": "blue",
    "Alopias superciliosus": "green"
}


def load_cache(year):
    cache_file = f"sharks_{year}.json"
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return json.load(f)
    return None


def save_cache(year, data):
    cache_file = f"sharks_{year}.json"
    with open(cache_file, "w") as f:
        json.dump(data, f)


def get_shark_data_since(year):
    cached = load_cache(year)
    if cached:
        return cached

    all_results = []

    for species in species_list:
        offset = 0
        limit = 300
        while True:
            params = {
                "scientificName": species,
                "hasCoordinate": "true",
                # fetch only desired years
                "eventDate": f"{year}-01-01,2025-12-31",
                "limit": limit,
                "offset": offset
            }
            try:
                response = requests.get(
                    "https://api.gbif.org/v1/occurrence/search", params=params)
                data = response.json()
                results = data.get("results", [])
                if not results:
                    break
                all_results.extend(results)
                if data.get("endOfRecords", True):
                    break
                offset += limit
                time.sleep(0.1)
            except Exception as e:
                st.error(f"API error for {species}: {e}")
                break

    save_cache(year, all_results)
    return all_results

# -- Website app config --


st.set_page_config(page_title="Thresher Shark Tracker",
                   page_icon=":shark:", layout="wide")

with st.container():
    st.subheader("Hi! I'm Ivy,")
    st.title("and I really like sharks.")
    st.write(
        "This website shows you the number of thresher sightings since your birth year according to GBIF data.")

if "shark_data" not in st.session_state:
    st.session_state["shark_data"] = []

year = st.number_input("Show sightings since year:",
                       min_value=1900, max_value=2025, step=1)

if st.button("Show Sightings"):
    st.session_state["shark_data"] = get_shark_data_since(year)

shark_data = st.session_state["shark_data"]

if shark_data:
    st.write(f" {len(shark_data)} sightings since {year}")
    try:
        lat = shark_data[0]['decimalLatitude']
        lon = shark_data[0]['decimalLongitude']
    except KeyError:
        lat, lon = 0, 0

    m = folium.Map(location=[lat, lon], zoom_start=2)

    for r in shark_data:
        try:
            lat = r['decimalLatitude']
            lon = r['decimalLongitude']
            species = r.get("species", "Alopias sp.")
            event_date = r.get("eventDate", "Unknown")
            popup = f"{species} ({event_date})"
            color = species_colors.get(species, "gray")

            folium.CircleMarker(
                [lat, lon],
                radius=4,
                popup=popup,
                color=color,
                fill=True,
                fill_color=color
            ).add_to(m)
        except KeyError:
            continue

    st_folium(m, width=700, height=500)


# cd ~/Desktop/"hello world"
# streamlit run alopias_working.py
