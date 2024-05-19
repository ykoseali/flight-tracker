from flask import Flask, render_template_string, request
import folium
import requests
import logging

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Flight Tracker</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .container {
            background: #fff;
            padding: 20px;
            margin-top: 30px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            width: 80%;
            max-width: 800px;
        }
        h1 {
            color: #333;
        }
        form {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-bottom: 20px;
        }
        input[type="text"] {
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ccc;
            border-radius: 4px;
            width: 80%;
            max-width: 400px;
        }
        button {
            padding: 10px 20px;
            color: #fff;
            background-color: #007BFF;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background-color: #0056b3;
        }
        ul {
            list-style-type: none;
            padding: 0;
            margin: 0;
        }
        li {
            background: #f4f4f9;
            margin: 10px 0;
            padding: 10px;
            border-radius: 4px;
            box-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
        }
        #map {
            height: 400px;
            width: 100%;
            border-radius: 8px;
            margin-top: 20px;
        }
        .no-data {
            color: #888;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Flight Tracker</h1>
        <form action="/" method="post">
            <input type="text" name="callsign" placeholder="Enter Flight Callsign" required>
            <button type="submit">Track Flight</button>
        </form>
        {% if flight_info %}
            <h2>Flight Information:</h2>
            <ul>
                {% for key, value in flight_info.items() %}
                <li><strong>{{ key.replace('_', ' ').capitalize() }}:</strong> {{ value }}</li>
                {% endfor %}
            </ul>
        {% else %}
            <p class="no-data">No flight information available. Ensure the callsign is correct and the flight is currently active.</p>
        {% endif %}
        {% if map %}
            <h2>Flight Location:</h2>
            <div id="map">{{ map|safe }}</div>
        {% endif %}
    </div>
</body>
</html>
'''

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
    
@app.route('/', methods=['GET', 'POST'])
def index():
    map_html = None
    flight_info = {}
    if request.method == 'POST':
        callsign = request.form['callsign']
        logging.info(f"Form submitted with callsign: {callsign}")
        flight_data = fetch_flight_data(callsign)
        if flight_data:
            flight_info = flight_data
            if flight_data['latitude'] and flight_data['longitude']:
                map_html = create_map(flight_data['latitude'], flight_data['longitude'])
            else:
                logging.warning("Latitude or longitude not available for the flight.")
        else:
            logging.warning("No data returned for the specified callsign.")
    return render_template_string(HTML_TEMPLATE, map=map_html, flight_info=flight_info)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', port=5001, debug=True)
