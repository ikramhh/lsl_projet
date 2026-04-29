"""
RabbitMQ Configuration - Send prediction requests to queue
"""
import pika
import json
import uuid
import os

# RabbitMQ Settings
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_PORT = int(os.environ.get('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.environ.get('RABBITMQ_USER', 'guest')
RABBITMQ_PASS = os.environ.get('RABBITMQ_PASS', 'guest')
QUEUE_NAME = 'asl_queue'


def send_to_queue(image_base64, metadata=None):
    """
    Send image to RabbitMQ queue for AI processing
    
    Args:
        image_base64: Base64 encoded image
        metadata: Optional dict with extra info
    
    Returns:
        dict with task_id and status
    """
    try:
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Create message
        message = {
            'task_id': task_id,
            'image': image_base64,
            'metadata': metadata or {},
            'timestamp': __import__('time').time()
        }
        
        # Connect to RabbitMQ
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        # Declare queue
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        
        # Send message
        channel.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Persistent message
            )
        )
        
        connection.close()
        
        print(f"✅ Sent to queue: {task_id}")
        
        return {
            'task_id': task_id,
            'status': 'queued',
            'message': 'Task sent to AI worker'
        }
        
    except Exception as e:
        print(f"❌ RabbitMQ error: {e}")
        return {
            'task_id': None,
            'status': 'error',
            'message': str(e)
        }
