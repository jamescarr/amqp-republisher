#!/usr/bin/env python
import argparse
import time
from kombu import Connection, Exchange, Queue, Producer
from kombu.mixins import ConsumerMixin
from kombu.log import get_logger
from multiprocessing.dummy import Pool
import logging
import sys

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

from collections import defaultdict

class Republisher(ConsumerMixin):
    def __init__(self, connection, queue, throttle, routing_key):
        self.connection = connection
        self.queues = [Queue(queue)]
        self.producer = Producer(connection.channel())
        self.throttle = float(throttle)
        self.routing_key = routing_key

    def on_message(self, body, message):
        original_exchange = message.delivery_info['exchange']
        current_routing_key = message.delivery_info['routing_key']
        if self.routing_key is not None:
            current_routing_key = self.routing_key
        message.properties['content_type'] = message.content_type
        self.producer.publish(body=body,
                              routing_key=current_routing_key,
                              exchange=original_exchange,
                              properties=message.properties,
        )
        message.ack()
        logger.info("Sent message with routing key {} to exchange {}".format(
            current_routing_key, original_exchange
        ))
        time.sleep(self.throttle)

    def get_consumers(self, Consumer, channel):
        return [
            Consumer(self.queues, 
                     callbacks=[self.on_message],
                     prefetch_count=1,
                     accept=['json']),
        ]

    def on_connection_error(self, exc, interval):
        logger.critical("connection_error")


def start(broker_urls, queue, throttle, routing_key, parallelism):
    def run_republisher(broker_url):
        Republisher(Connection(broker_url), queue, throttle, routing_key).run()
    pool = Pool(parallelism)
    pool.map(run_republisher, broker_urls)


def main():
    parser = argparse.ArgumentParser(description='Republish messages.')
    parser.add_argument('-b', '--broker-url', help='Broker URL to connect to', dest='broker_urls', metavar='BROKER_URL', action='append', required=True)
    parser.add_argument('--queue', help='Queue to subscribe to', required=True)
    parser.add_argument('--throttle', help='Time between message reads', default=1)
    parser.add_argument('--routing-key', help='Override original routing key', dest='routing_key')
    parser.add_argument('--parallelism', help='The max number of brokers to consume from in parallel', default=5, dest='parallelism')

    args = parser.parse_args()

    start(**vars(args))



if __name__ == '__main__':
    main()
