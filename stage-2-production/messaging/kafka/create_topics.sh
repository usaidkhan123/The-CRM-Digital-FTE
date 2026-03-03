#!/bin/bash
# Wait for Kafka to be ready
echo "Waiting for Kafka to be ready..."
cub kafka-ready -b kafka:9092 1 60 2>/dev/null || sleep 30

KAFKA_BIN="/usr/bin"

echo "Creating Kafka topics..."

kafka-topics --create --if-not-exists --bootstrap-server kafka:9092 \
  --topic incoming-messages --partitions 3 --replication-factor 1

kafka-topics --create --if-not-exists --bootstrap-server kafka:9092 \
  --topic agent-responses --partitions 3 --replication-factor 1

kafka-topics --create --if-not-exists --bootstrap-server kafka:9092 \
  --topic notifications --partitions 3 --replication-factor 1

kafka-topics --create --if-not-exists --bootstrap-server kafka:9092 \
  --topic escalations --partitions 1 --replication-factor 1

kafka-topics --create --if-not-exists --bootstrap-server kafka:9092 \
  --topic dead-letter --partitions 1 --replication-factor 1

echo "Listing topics:"
kafka-topics --list --bootstrap-server kafka:9092

echo "Topic creation complete."
