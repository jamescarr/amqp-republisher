#!/usr/bin/env python
import argparse
import time
from kombu import Connection, Exchange, Queue, Producer
from kombu.mixins import ConsumerMixin
from kombu.log import get_logger
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

class Migrator(ConsumerMixin):
    def __init__(self, from_connection, to_connection, from_queue, throttle):
        self.connection = from_connection
        self.from_queues = [Queue(from_queue)]
        self.to_connection = to_connection
        self.producer = Producer(self.to_connection.channel())
        self.throttle = throttle

    def on_message(self, body, message):
        original_exchange = message.delivery_info['exchange']
        original_routing_key = message.delivery_info['routing_key']
        message.properties['content_type'] = message.content_type
        self.producer.publish(body=body,
                              routing_key=original_routing_key,
                              exchange=original_exchange,
                              properties=message.properties,
        )
        message.ack()
        logger.info("Sent message with routing key {} to exchange {}".format(
            original_routing_key, original_exchange
        ))
        time.sleep(self.throttle)

    def get_consumers(self, Consumer, channel):
        return [
            Consumer(self.from_queues, 
                     callbacks=[self.on_message],
                     prefetch_count=1,
                     accept=['json']),
        ]

    def on_connection_error(exc, interval):
        logger.critical("connection_error")


def migrate(from_broker_url, to_broker_url, from_queue, throttle):
    Migrator(
        Connection(from_broker_url),
        Connection(to_broker_url),
        from_queue,
        throttle,
    ).run()


def main():
    parser = argparse.ArgumentParser(description='Migrate messages.')
    parser.add_argument('--from-broker-url', help='Broker URL to connect to', dest='from_broker_url', required=True)
    parser.add_argument('--to-broker-url', help='Broker URL to connect to', dest='to_broker_url', required=True)
    parser.add_argument('--from-queue', help='Queue to subscribe to', dest='from_queue', required=True)
    parser.add_argument('--throttle', help='Time between message reads', default=1)

    args = parser.parse_args()

    migrate(**vars(args))


if __name__ == '__main__':
    main()
