# AMQP Republisher
Simple app to read messages off of a queue and republish them intact to the original exchange using the original routing key.

Why not use shovel? Because shovel requires specifying a routing key and doesn't provide a way to just use the existing routing key.

## Usage

```
pip install -r requirements.txt

./republish.py --broker-url amqp://guest:guest@localhost/main --queue unrouted.messages

```
