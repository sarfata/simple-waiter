#!/usr/bin/env python

from pymongo import MongoClient
from bson.son import SON
import argparse
import time
import subprocess
import csv
import sys
import socket, os
import logging

class DeliveryException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "DeliveryException: {}".format(repr(self.value))

class Waiter:
    def __init__(self, kitchen, database, name):
        self.db = MongoClient(kitchen)[database]
        self.name = name

    def fetch_and_deliver_order(self, deliver_cmd):
        order = self.db.orders.find_and_modify({'status': 'READY'}, { '$set': { 'status': 'RUNNING', 'start': time.time() } }, new = True)

        if order is None:
            return False

        try:
            self.deliver(deliver_cmd, order)
            order['status'] = 'DONE'
        except DeliveryException as e:
            order['error'] = str(e)
            order['status'] = 'ERROR'
        order['end'] = time.time()
        order['waiter'] =self.name
        self.db.orders.save(order)

        return True

    # You can also override deliver if you'd rather do python stuff
    def deliver(self, deliver_cmd, order):
        print "Delivering {}".format(order)
        try:
            args = deliver_cmd + order['arguments']
            cmd = " ".join(args)

            logging.debug("Running {}".format(cmd))
            subprocess.check_call(cmd, shell = True)
        except subprocess.CalledProcessError as e:
            raise DeliveryException(e)

    def take_order(self, dishes):
        order = { 'status': 'READY', 'arguments': dishes }
        self.db.orders.insert(order)

    def order_status(self):
        return self.db.orders.aggregate([
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$sort": SON([("count", -1), ("_id", -1)])}
        ])['result']

    def list_orders(self):
        return  self.db.orders.find()

    def clean_orders(self):
        self.db.orders.remove()

    def reset_orders(self):
        self.db.orders.update({ 'status': { '$in': [ 'ERROR', 'RUNNING' ] }}, { '$set': { 'status': 'READY' }}, multi = True)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    argparser = argparse.ArgumentParser("A waiter goes to the kitchen to get an order, delivers it, and then loops again!")
    argparser.add_argument('-k', '--kitchen', help = 'MongoDB URL of the kitchen where the waiter will get orders to deliver (defaults to localhost)')
    argparser.add_argument('--db', help = 'Name of the MongoDB database to use (default is simplewaiter)', default = 'simplewaiter')
    argparser.add_argument('-n', '--name', help = 'Name of the waiter processing the order. Defaults to hostname/pid',
        default = socket.gethostname() + "/" + str(os.getpid()))

    subparsers = argparser.add_subparsers(dest = 'action')
    sub_status = subparsers.add_parser('status', help = "Displays information on the status of all orders")

    sub_extract = subparsers.add_parser('extract', help = "Extract all the jobs and their status")
    sub_extract.add_argument('-o', '--output', help = "Output file", type=argparse.FileType('wb'), default = sys.stdout)

    sub_deliver = subparsers.add_parser('deliver', help = "Get orders and deliver them")
    sub_deliver.add_argument('deliver', help = 'A command and params that will be called to deliver the order', nargs = argparse.REMAINDER)

    sub_load = subparsers.add_parser('load', help = "Load order from file")
    sub_load.add_argument('orders', help = 'File to read from', type=argparse.FileType('rb'))

    sub_clean = subparsers.add_parser('clean', help = "Clean orders")
    sub_reset = subparsers.add_parser('reset', help = "Reset RUNNING and ERROR orders to READY")

    args = argparser.parse_args()
    nestor = Waiter(args.kitchen, args.db, args.name)

    if args.action == 'status':
        print nestor.order_status()

    elif args.action == 'load':
        order_reader = csv.reader(args.orders)
        c = 0
        for dishes in order_reader:
            nestor.take_order(dishes)
            c = c + 1
        print "Loaded {} orders".format(c)

    elif args.action == 'deliver':
        c = 0
        while nestor.fetch_and_deliver_order(args.deliver):
            print "."
            c = c + 1

        print "Done. Delivered {} orders.".format(c)

    elif args.action == 'reset':
        nestor.reset_orders()
        print "Reset orders"

    elif args.action == 'clean':
        nestor.clean_orders()
        print "Cleaned database."

    elif args.action == 'extract':
        writer = csv.writer(args.output)

        keys = ['_id', 'status', 'waiter', 'start', 'stop', 'arguments', 'error']
        default_values = { key: '' for key in keys }

        writer.writerow(keys)
        for o in nestor.list_orders():
            # provide default values
            csvline = dict(default_values.items() + o.items())
            writer.writerow([csvline[key] for key in keys ])

    else:
        print "Unrecognized argument."
