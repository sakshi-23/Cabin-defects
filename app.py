from flask import Flask, render_template, request, jsonify
import os
from os import environ
import json
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
import sys
from random import randint
import datetime




sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

db_name = 'heroku_0t309l33'
app = Flask(__name__)


# Setup MongoDB
uri = ''
if "MONGODB_URI" in os.environ:
    uri = environ.get('MONGODB_URI')
else:
    with open('mongo-cred.json') as f:
        uri = json.load(f)['uri']
client = MongoClient(uri)
db = client[db_name]
defects = db['defects']
aircrafts = db['aircrafts']
destinations = db['destinations']
#------------------------------

port = int(os.getenv('PORT', 8000))

@app.route('/')
def home():
    return render_template('index.html')



@app.route('/create_defect', methods=['POST'])
def create_defect():
    defect_data = request.get_json(silent=True)
    defect_record_id = str(defects.insert_one(defect_data).inserted_id)
    return json.dumps({"defect_record_id" : defect_record_id})

@app.route('/defects/<city_code>')
def get_defects(city_code):
    defect_list = defects.find({'city_code': city_code})
    defect_res = []
    for defect in defect_list:
        defect['defect_record_id'] = str(defect['_id'])
        del(defect['_id'])
        defect_res.append(defect)
    return json.dumps(defect_res)


def generate_defects():
    destination_list = destinations.find({})
    aircraft_list = aircrafts.find({})
    seats = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
    durration_map = {}
    with open('defects.json') as f:
        defects = json.load(f)
    start_date = datetime.datetime.now() + datetime.timedelta(-31)
    for i in range(1,30):
        date = start_date+datetime.timedelta(i)
        for j in range(1,150):
            s_ran = randint(1, len(destination_list))
            d_ran = randint(1, len(destination_list))
            while  d_ran== s_ran:
                d_ran = randint(1, len(destination_list))
            source = destination_list[s_ran]['Code']
            dest = destination_list[d_ran]['Code']
            starttime = date + datetime.timedelta(hours=randint(1,12),minutes=randint(1,60))
            if durration_map.has_key(source+dest) :
                duration = durration_map[source+dest]
            else:
                duration = randint(3, 15)
                durration_map[source+dest] = duration
            for k in range(1,5):
                index = randint(1,12)
                defect = defects[index]
                defect['source'] = source
                defect['destination'] = dest
                defect['timestamp'] = starttime + datetime.timedelta(hours=randint(1,duration),minutes=randint(1,60))
                if defect['type'] < 9:
                    defect['seat_no'] = str(randint(1,50))+seats[randint(1,9)]





def random_date(start,l):
   current = start
   while l >= 0:
      curr = current + datetime.timedelta(minutes=randint(1,60))
      yield curr
      l-=1

if __name__ == '__main__':
    # generate_defects()
    app.run(host='0.0.0.0', port=port, debug=True)
