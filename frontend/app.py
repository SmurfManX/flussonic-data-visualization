from flask import Flask, render_template
import requests
import json

app = Flask(__name__)

@app.route('/')
def index():
    data_url = "http://FLUSSONIC_IP:8000/data.json"
    try:
        response = requests.get(data_url)
        data = response.json()
    except requests.RequestException as e:
        data = {"error": f"Failed to fetch data: {e}"}
    except json.JSONDecodeError:
        data = {"error": "Failed to parse JSON data"}
    
    return render_template('index.html', data=data)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
