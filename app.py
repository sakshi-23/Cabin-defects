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
    defect_list = defects.find({'$and':[{'city_code': city_code}, {'$or' : [{'status' : 'created'}, {'status' : 'deferred'}]}]})
    defect_res = []
    for defect in defect_list:
        defect['defect_record_id'] = str(defect['_id'])
        del(defect['_id'])
        defect_res.append(defect)
    return json.dumps(defect_res)


@app.route('/new_defects/<city_code>')
def get_new_defects(city_code):
    defect_list = defects.find({'$and':[{'city_code': city_code}, {'status' : 'created'}]})
    defect_res = []
    for defect in defect_list:
        defect['defect_record_id'] = str(defect['_id'])
        del(defect['_id'])
        defect_res.append(defect)
    return json.dumps(defect_res)

@app.route('/deferred_defects/<city_code>')
def get_deferred_defects(city_code):
    defect_list = defects.find({'$and':[{'city_code': city_code}, {'status' : 'deferred'}]})
    defect_res = []
    for defect in defect_list:
        defect['defect_record_id'] = str(defect['_id'])
        del(defect['_id'])
        defect_res.append(defect)
    return json.dumps(defect_res)

@app.route('/all_defects/<city_code>')
def get_all_defects(city_code):
    defect_list = defects.find({'city_code': city_code})
    defect_res = []
    for defect in defect_list:
        defect['defect_record_id'] = str(defect['_id'])
        del(defect['_id'])
        defect_res.append(defect)
    return json.dumps(defect_res)


@app.route(('/mark_defect_fixed/<defect_id>'))
def mark_fixed(defect_id):
    defects.find_one_and_update({'_id' : ObjectId(defect_id)}, {'$set': {'status' : 'fixed'}})
    return 'OK'

@app.route(('/mark_defect_deferred/<defect_id>'))
def mark_deferred(defect_id):
    defects.find_one_and_update({'_id' : ObjectId(defect_id)}, {'$set': {'status' : 'deferred'}})
    return 'OK'


@app.route('/analytics', methods=['POST'])
def analytics():
    query_json = request.get_json(silent=True)
    defect_list =[]
    results = defects.find(query_json)
    for r in results:
        r['defect_record_id'] = str(r['_id'])
        del(r['_id'])
        defect_list.append(r)
    return json.dumps(defect_list)


def generate_defects():
    defect_all = []
    destination_list = get_array(destinations.find({}))
    aircraft_list = get_array(aircrafts.find({}))
    seats = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
    priority = ['low','medium','high']
    durration_map = {}
    journey_id_map  = {}
    with open('defects.json') as f:
        defects_source = json.load(f)
    start_date = datetime.datetime.now() + datetime.timedelta(-31)
    count = 0
    for i in range(0,30):
        date = start_date+datetime.timedelta(days=i)

        for j in range(0,150):
            s_ran = randint(1, len(destination_list)-1)
            d_ran = randint(1, len(destination_list)-1)
            while  d_ran== s_ran:
                d_ran = randint(1, len(destination_list)-1)
            source = destination_list[s_ran]['Code']
            dest = destination_list[d_ran]['Code']
            starttime = date + datetime.timedelta(hours=randint(1,12),minutes=randint(1,60))
            aircraft = aircraft_list[randint(1, len(aircraft_list)-1)]
            journey_id = randint(10001, 99999 )
            while journey_id_map.has_key(journey_id) :
                journey_id = randint(10001, 99999 )
            journey_id_map[journey_id] = ""
            if durration_map.has_key(source+dest) :
                duration = durration_map[source+dest]
            else:
                duration = randint(3, 15)
                durration_map[source+dest] = duration
            endtime = starttime+datetime.timedelta(hours=duration)
            for k in range(0,5):
                index = randint(0,11)
                defect = defects_source[index]
                defect['journey_id'] = journey_id
                defect['source'] = source
                defect['dest'] = dest
                defect["city_code"] = dest
                defect["status"] =  "fixed"
                defect["aircraft_id"] = aircraft["aircraft_registration_id"]
                defect["aircraft"] =  aircraft["aircraft_type"]
                defect["flight_start_time"] =  str(starttime)
                defect["flight_end_time"] = str(endtime)
                defect["priority"] = priority[randint(0,2)]
                defect['timestamp'] = str(starttime + datetime.timedelta(hours=randint(1,duration),minutes=randint(1,60)))
                if defect['defect_type'] < 9:
                    defect['seat_no'] = str(randint(1,50))+seats[randint(0,8)]
                if defect.has_key('_id'):
                    del(defect['_id'])
                defect_all.append(defect)
                count = count +1
                # print count
    with open('data.json', 'w') as outfile:
        json.dump(defect_all, outfile)

def get_array(cursor):
    list = []
    for i in cursor:
        list.append(i)
    return list


def random_date(start,l):
   current = start
   while l >= 0:
      curr = current + datetime.timedelta(minutes=randint(1,60))
      yield curr
      l-=1

if __name__ == '__main__':
    # generate_defects()
    app.run(host='0.0.0.0', port=port, debug=True)
