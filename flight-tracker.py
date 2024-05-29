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
            
            height: 1200px;
        }
        h1 {
            text-align: center;
            color: #333;
        }
        form {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-bottom: 20px;
        }
        #search-box{
            position: relative;
            cursor: text;
            font-size: 14px;
            line-height: 20px;
            padding: 0 16px;
            height: 48px;
            background-color: #fff;
            border: 1px solid #168CAA;
            border-radius: 3px;
            color: rgb(35, 38, 59);
            box-shadow: inset 0 1px 4px 0 rgb(119 122 175 / 30%);
            overflow: hidden;
            transition: all 100ms ease-in-out;
            width: 80%;
            max-width: 400px; 
        }
        search-box:focus{
            border: 1px solid #116D84;
            box-shadow: 0 1px 0 0 rgb(33, 158, 188 / 5%);
        }
        button {
            margin: 20px 0;
            display: inline-block;
            outline: none;
            cursor: pointer;
            font-size: 14px;
            line-height: 1;
            border-radius: 500px;
            transition-property: background-color,border-color,color,box-shadow,filter;
            transition-duration: .3s;
            border: 1px solid transparent;
            letter-spacing: 2px;
            min-width: 160px;
            text-transform: uppercase;
            white-space: normal;
            font-weight: 700;
            text-align: center;
            padding: 17px 48px;
            color: #fff;
            background-color: #219EBC;
            height: 48px;  
        }
        button:hover {
            transform: scale(1.04);
            background-color: #0F83A0;
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
            margin: 20px, 0;
        }
        .no-data {
            text-align: center;
            color: #888;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Flight Tracker</h1>
        <form action="/" method="post">
            <input id="search-box" type="search"  name="callsign" aria-label="Search" placeholder="Enter Flight Call Sign" required>
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
            <p class="no-data">No flight information is available. Ensure the call sign is correct and the flight is currently active.</p>
        {% endif %}
        {% if map %}
            <h3>Flight Location:</h3>
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
        data = response.json().get('states', None)
        logging.info(f"Data fetched: {data}")
        if data is None:
            logging.error("No data found in the API response.")
            return None
        for state in data:
            if state[1] and state[1].strip().upper() == callsign.strip().upper():
                logging.info(f"Exact match found: {state}")
                return {
                    'call_sign': state[1],
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
        logging.error(f"Failed to fetch data from OpenSky API. Status code: {response.status_code}")
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
