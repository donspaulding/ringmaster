#!/usr/bin/env python
import csv
import glob
import redis
from flask import Flask, render_template, jsonify, request

DEBUG = True
SECRET_KEY = open('secret_key.txt').read()

app = Flask(__name__)
app.config.from_object(__name__)


@app.route('/')
def index():
    r = redis.Redis()
    item_number = request.args.get('item_number', '')
    if item_number:
        r.lpush('relief:next_items', item_number)
    next_item = request.args.get('next_item', '')
    if next_item:
        next = r.rpop('relief:next_items')
        if next is not None:
            r.set('relief:current_item', next)
    return render_template('index.html',
                    upcoming_items=[get_item(number) for number in r.lrange('relief:next_items', 0, -1)]
    )


@app.route('/display/')
def display():
    return render_template('display.html')


@app.route('/load/')
def load():
    reader = csv.reader(open("2012-item-list.csv"))
    r = redis.Redis()
    for date, number, description, donor in reader:
        files = glob.glob('static/images/item_pics/%s.jpg' % number)
        files += glob.glob('static/images/item_pics/%s-?.jpg' % number)
        pic_urls = ['/' + path for path in files]
        r.set("relief:item:%s:date" % number, date)
        r.set("relief:item:%s:description" % number, description)
        r.set("relief:item:%s:donor" % number, donor)
        r.set("relief:item:%s:pics" % number, ';'.join(pic_urls))
        r.sadd("relief:items", number)
    return "Loaded %d items!" % r.scard('relief:items')


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
