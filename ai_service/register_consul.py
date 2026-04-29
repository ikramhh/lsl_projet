"""
Consul Service Registration Script
Registers Django services with Consul for service discovery
"""

import requests
import os
import time
import sys

def register_service(service_name, service_id, address, port, health_check_url=None):
    """
    Register a service with Consul
    
    Args:
        service_name: Name of the service (e.g., 'django-api')
        service_id: Unique ID for this instance
        address: Service address (hostname or IP)
        port: Service port
        health_check_url: Optional health check endpoint
    """
    
    consul_host = os.environ.get('CONSUL_HOST', 'consul')
    consul_port = os.environ.get('CONSUL_PORT', '8500')
    consul_url = f"http://{consul_host}:{consul_port}/v1/agent/service/register"
    
    # Service registration payload
    payload = {
        "ID": service_id,
        "Name": service_name,
        "Address": address,
        "Port": port,
        "Tags": [f"service-{service_name}", "production"],
        "Meta": {
            "version": "1.0.0",
            "environment": "docker"
        }
    }
    
    # Add health check if provided
    if health_check_url:
        payload["Check"] = {
            "HTTP": f"http://{address}:{port}{health_check_url}",
            "Interval": "10s",
            "Timeout": "5s"
        }
    
    try:
        response = requests.put(consul_url, json=payload)
        
        if response.status_code == 200:
            print(f"✅ Successfully registered {service_name} with Consul")
            print(f"   Service ID: {service_id}")
            print(f"   Address: {address}:{port}")
            print(f"   Consul UI: http://{consul_host}:{consul_port}")
            return True
        else:
            print(f"❌ Failed to register {service_name}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to Consul at {consul_host}:{consul_port}")
        print("   Make sure Consul is running and accessible")
        return False
    except Exception as e:
        print(f"❌ Error registering service: {e}")
        return False


def wait_for_consul(timeout=30):
    """Wait for Consul to be available"""
    
    consul_host = os.environ.get('CONSUL_HOST', 'consul')
    consul_port = os.environ.get('CONSUL_PORT', '8500')
    consul_url = f"http://{consul_host}:{consul_port}/v1/status/leader"
    
    print(f"⏳ Waiting for Consul to be ready at {consul_host}:{consul_port}...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(consul_url, timeout=2)
            if response.status_code == 200:
                print("✅ Consul is ready!")
                return True
        except:
            pass
        
        time.sleep(2)
        print(".", end="", flush=True)
    
    print(f"\n❌ Consul did not become ready within {timeout} seconds")
    return False


def main():
    """Main registration logic"""
    
    # Get service configuration from environment variables
    service_name = os.environ.get('CONSUL_SERVICE_NAME', 'django-service')
    service_port = int(os.environ.get('SERVICE_PORT', '8000'))
    service_address = os.environ.get('SERVICE_ADDRESS', 'localhost')
    health_check = os.environ.get('HEALTH_CHECK_URL', '/auth/')
    
    # Wait for Consul to be ready
    if not wait_for_consul(timeout=30):
        print("⚠️  Continuing without Consul registration...")
        sys.exit(0)
    
    # Register the service
    service_id = f"{service_name}-{service_port}"
    
    print(f"\n📝 Registering service:")
    print(f"   Name: {service_name}")
    print(f"   Port: {service_port}")
    print(f"   Address: {service_address}")
    
    success = register_service(
        service_name=service_name,
        service_id=service_id,
        address=service_address,
        port=service_port,
        health_check_url=health_check
    )
    
    if success:
        print(f"\n🎯 Service discovery URL:")
        print(f"   http://{service_name}.service.consul")
        print(f"   Consul UI: http://localhost:8500")
    else:
        print("\n⚠️  Service registration failed, but continuing...")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
