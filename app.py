from flask import Flask, render_template, request, redirect, url_for
import json
import folium
from folium.plugins import HeatMap
import os
from datetime import datetime

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.json'):
            file_path = os.path.join('static', 'data.json')
            file.save(file_path)
            generate_heatmap(file_path)
            return redirect(url_for('heatmap'))
    return render_template('index.html')

@app.route('/heatmap')
def heatmap():
    return render_template('heatmap.html')

@app.route('/filter-heatmap', methods=['POST'])
def filter_heatmap():
    daterange = request.form.get('daterange')
    
    # If the daterange is empty, don't filter and generate the heatmap without date restriction
    if not daterange:
        file_path = os.path.join('static', 'data.json')
        generate_heatmap(file_path) 
        return redirect(url_for('heatmap'))

    try:
        start_str, end_str = daterange.split(' to ')
        start_date = datetime.strptime(start_str.strip(), '%Y-%m-%d')
        end_date = datetime.strptime(end_str.strip(), '%Y-%m-%d')
    except ValueError:
        return "Invalid date format. Use 'YYYY-MM-DD to YYYY-MM-DD'.", 400

    # Generate the heatmap with the date filter applied
    file_path = os.path.join('static', 'data.json')
    generate_heatmap(file_path, start_date=start_date, end_date=end_date)
    return redirect(url_for('heatmap'))


def generate_heatmap(file_path, start_date=None, end_date=None):
    with open(file_path, 'r') as f:
        data = json.load(f)

    map = folium.Map(zoom_start=12)
    heat_data = []

    for entry in data:
        timestamp = entry.get("startTime") or entry.get("activity", {}).get("start")
        if not timestamp:
            continue

        # Parse timestamp
        try:
            dt = datetime.strptime(timestamp[:19], '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            continue

        # Filter by date range if specified
        if start_date and end_date and not (start_date <= dt <= end_date):
            continue

        # Extract coordinates
        if "visit" in entry:
            coords = entry["visit"]["topCandidate"]["placeLocation"].replace("geo:", "").split(",")
        elif "activity" in entry:
            coords = entry["activity"]["start"].replace("geo:", "").split(",")
        else:
            continue

        try:
            lat, lon = float(coords[0]), float(coords[1])
            heat_data.append([lat, lon])
        except ValueError:
            continue

    HeatMap(heat_data, radius=15, min_opacity=0.3).add_to(map)
    map.save(os.path.join('static', 'heatmap.html'))

if __name__ == '__main__':
    app.run(debug=True)
