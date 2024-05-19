from flask import Flask, render_template_string, request
import folium
import requests
import logging

app = Flask(__name__)

def fetch_flight_data(callsign):
    """ Fetch flight data from OpenSky """
    url = f"https://opensky-network.org/api/states/all?callsign={callsign.upper()}"
    response = requests.get(url)
    logging.info(f"API URL: {url}")
    if response.status_code == 200:
        data = response.json().get('states', [])
        logging.info(f"Data fetched: {data}")
        for state in data:
            if state[1] and state[1].strip().upper() == callsign.strip().upper():
                logging.info(f"Exact match found: {state}")
                return {
                    'callsign': state[1],
                    'origin_country': state[2],
                    'longitude': state[5],
                    'latitude': state[6],
                    'altitude': state[7],
                    'velocity': state[9],
                    'heading': state[10],
                    'vertical_rate': state[11]
                }
        logging.warning("No exact match found for callsign.")
    else:
        logging.error("Failed to fetch data from OpenSky API.")
    return None

def create_map(latitude, longitude):
    """ Create a map using Folium centered at the flight's current position """
    if latitude and longitude:
        logging.info(f"Creating map at latitude: {latitude}, longitude: {longitude}")
        map_obj = folium.Map(location=[latitude, longitude], zoom_start=6)
        folium.Marker([latitude, longitude], tooltip='Flight Location').add_to(map_obj)
        map_html = map_obj._repr_html_()
        logging.info("Map created successfully.")
        return map_html
    logging.warning("Invalid latitude or longitude provided, cannot create map.")
    return None
