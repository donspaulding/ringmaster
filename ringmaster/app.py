#!/usr/bin/env python
import csv
import json
import glob
import redis
from flask import Flask, render_template, jsonify, request
from flask.ext.sse import sse, send_event

DEBUG = True
SECRET_KEY = open('secret_key.txt').read()

app = Flask(__name__)
app.config.from_object(__name__)
app.register_blueprint(sse, url_prefix='/sse/')

@app.route('/')
def index():
    return render_template('index_static.html')

@app.route('/get/all/')
def get_all_data():
    r = redis.Redis()
    data = json.loads(r.get("relief:2013:data"))
    data.update({
        'announcement': open("announcement.txt").read(),
        'upcoming_events': json.loads(open('upcoming_events.json').read())
    })
    return jsonify(data)

@app.route('/get/all/items/')
def get_items():
    r = redis.Redis()
    L = []
    for num in r.smembers('relief:2013:items'):
        L.append({
            "number": num,
            "description": r.get("relief:2013:item:%s:description" % num),
            "details": []
        })
    print L[:10]
    return json.dumps(sorted(L, key=lambda item: item['number']))

@app.route('/admin/', methods=["GET", "POST"])
def admin():
    r = redis.Redis()
    if request.method == "GET":
        return render_template('admin.html')
    r.set('relief:2013:data', request.form['data'])
    send_event('force_update', 'null')
    return "OK"


@app.route('/admin/force_refresh/')
def force_refresh():
    send_event('force_refresh', 'null')
    return "OK"

@app.route('/admin/scroll_to/')
def scroll_to():
    send_event('scroll_to', request.args['number'])
    return "OK"

@app.route('/old')
def old_index():
    r = redis.Redis()
    item_number = request.args.get('item_number', '')
    if item_number:
        r.lpush('relief:next_items', item_number)
    next_item = request.args.get('next_item', '')
    if next_item:
        next = r.rpop('relief:next_items')
        if next is not None:
            r.set('relief:current_item', next)
    return render_template(
        'index.html',
        upcoming_items=[get_item(number) for number in r.lrange('relief:next_items', 0, -1)]
    )


@app.route('/display/')
def display():
    return render_template('display.html')


@app.route('/load/')
def load():
    reader = csv.reader(open("2013-item-list.csv"))
    r = redis.Redis()
    for date, group, number, description, donor, cost in reader:
        files = glob.glob('static/images/item_pics/%s.jpg' % number)
        files += glob.glob('static/images/item_pics/%s-?.jpg' % number)
        pic_urls = ['/' + path for path in files]
        r.set("relief:2013:item:%s:date" % number, date)
        r.set("relief:2013:item:%s:group" % number, group)
        r.set("relief:2013:item:%s:description" % number, description)
        r.set("relief:2013:item:%s:donor" % number, donor)
        r.set("relief:2013:item:%s:pics" % number, ';'.join(pic_urls))
        r.sadd("relief:2013:items", number)
    return "Loaded %d items!" % r.scard('relief:2013:items')


def get_item(item_number):
    r = redis.Redis()
    pics = r.get('relief:item:%s:pics' % item_number)
    if not pics:
        pics = ['/static/images/blank.png']
    else:
        pics = pics.split(';')
    return {
        'item_number': item_number,
        'item_description': r.get('relief:item:%s:description' % item_number) or "Unlisted Item",
        'item_donor': r.get('relief:item:%s:donor' % item_number),
        'item_date': r.get('relief:item:%s:date' % item_number),
        'item_urls': pics,
    }


@app.route('/nextup/')
def next_up():
    r = redis.Redis()
    item_number = r.get("relief:current_item")
    if not item_number:
        return jsonify({'item_number': 0})
    return jsonify(**get_item(item_number))


if __name__ == '__main__':
    app.run(extra_files=['templates/'])
