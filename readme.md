# AMQP Republisher
Simple app to read messages off of a queue and republish them intact to the original exchange using the original routing key.

## Usage

```
pip install -r requirements.txt

./republish.py --broker-url amqp://guest:guest@localhost/main --queue unrouted.messages

```
