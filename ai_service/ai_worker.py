"""
AI Worker - Consumes prediction tasks from RabbitMQ
"""
import pika
import json
import sys
import os
import time

RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.environ.get('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.environ.get('RABBITMQ_USER', 'guest')
RABBITMQ_PASS = os.environ.get('RABBITMQ_PASS', 'guest')
QUEUE_NAME = 'asl_queue'


def callback(ch, method, properties, body):
    """Process message from queue"""
    try:
        # Parse message
        task = json.loads(body)
        task_id = task.get('task_id', 'unknown')
        image_data = task.get('image', '')
        metadata = task.get('metadata', {})
        
        print(f"\n{'='*60}")
        print(f"📊 Task received: {task_id}")
        print(f"👤 User: {metadata.get('username', 'N/A')}")
        print(f"📷 Image size: {len(image_data)} bytes")
        
        # TEST MODE - Return HELLO
        prediction = "HELLO"
        confidence = 1.0
        
        print(f"🎯 Prediction: {prediction}")
        print(f"📈 Confidence: {confidence*100:.1f}%")
        print(f"{'='*60}\n")
        
        # Acknowledge message
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def wait_for_rabbitmq(max_retries=30, retry_delay=2):
    """Wait for RabbitMQ to be ready"""
    print("⏳ Waiting for RabbitMQ to be ready...")
    
    for attempt in range(max_retries):
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            parameters = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=credentials,
                connection_attempts=3,
                retry_delay=retry_delay
            )
            connection = pika.BlockingConnection(parameters)
            connection.close()
            print("✅ RabbitMQ is ready!")
            return True
        except Exception as e:
            print(f"⏳ Attempt {attempt + 1}/{max_retries} - RabbitMQ not ready yet...")
            time.sleep(retry_delay)
    
    print("❌ RabbitMQ did not become ready in time")
    return False


def main():
    """Start worker"""
    print("\n" + "="*60)
    print("  🤖 AI WORKER - RabbitMQ Consumer")
    print("="*60)
    print(f"📡 Queue: {QUEUE_NAME}")
    print(f"📍 RabbitMQ: {RABBITMQ_HOST}:{RABBITMQ_PORT}")
    print("="*60 + "\n")
    
    # Wait for RabbitMQ to be ready
    if not wait_for_rabbitmq():
        print("⚠️  Starting worker anyway (may fail)...")
    
    while True:
        try:
            # Connect
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            parameters = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=credentials,
                connection_attempts=5,
                retry_delay=3
            )
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            
            # Declare queue
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.basic_qos(prefetch_count=1)
            
            # Start consuming
            channel.basic_consume(
                queue=QUEUE_NAME,
                on_message_callback=callback
            )
            
            print("✅ Worker started! Waiting for tasks...")
            print("   Press Ctrl+C to stop\n")
            
            channel.start_consuming()
            
        except KeyboardInterrupt:
            print("\n⏹️  Worker stopped")
            break
        except Exception as e:
            print(f"\n❌ Connection error: {e}")
            print("🔄 Reconnecting in 5 seconds...")
            time.sleep(5)


if __name__ == '__main__':
    main()
