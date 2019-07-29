from flask import Flask, render_template, jsonify, request

from module.Direction import Direction

app = Flask(__name__)

# index page
@app.route('/')
def index():
    return render_template('index.html')

# My direction api
@app.route('/my_direction_api', methods=['POST'])
def my_direction():
    # get data from request
    data = request.get_json()
    origin = data['origin']
    destination = data['destination']
    travelMode = data['travelMode']

    # open route service direction api
    direction = Direction(origin, destination, travelMode)
    # Regular Route
    routes_list = direction.start()

    return jsonify(routes_list)

if __name__ == '__main__':
    app.debug = True
    app.run()