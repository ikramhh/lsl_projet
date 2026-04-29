"""
Consul Service Discovery Demo
Shows how to discover and query registered services
"""

import requests
import os
import json

def get_consul_url():
    """Get Consul URL from environment or use default"""
    consul_host = os.environ.get('CONSUL_HOST', 'localhost')
    consul_port = os.environ.get('CONSUL_PORT', '8500')
    return f"http://{consul_host}:{consul_port}"

def list_all_services():
    """List all services registered in Consul"""
    
    consul_url = get_consul_url()
    response = requests.get(f"{consul_url}/v1/agent/services")
    
    if response.status_code == 200:
        services = response.json()
        print("\n" + "="*60)
        print("📋 ALL REGISTERED SERVICES IN CONSUL")
        print("="*60)
        
        for service_id, service_info in services.items():
            if service_id.startswith('_'):  # Skip Consul internal services
                continue
                
            print(f"\n✅ Service: {service_info['Service']}")
            print(f"   ID: {service_id}")
            print(f"   Address: {service_info['Address']}:{service_info['Port']}")
            print(f"   Tags: {', '.join(service_info.get('Tags', []))}")
            
            if 'Meta' in service_info:
                print(f"   Metadata: {service_info['Meta']}")
        
        print("\n" + "="*60)
        return services
    else:
        print(f"❌ Failed to get services: {response.text}")
        return {}

def get_service_by_name(service_name):
    """Get specific service by name"""
    
    consul_url = get_consul_url()
    response = requests.get(f"{consul_url}/v1/catalog/service/{service_name}")
    
    if response.status_code == 200:
        instances = response.json()
        
        print(f"\n🔍 Service Discovery for: '{service_name}'")
        print("="*60)
        
        if not instances:
            print(f"❌ No instances found for '{service_name}'")
            return None
        
        for i, instance in enumerate(instances, 1):
            print(f"\n✅ Instance {i}:")
            print(f"   Address: {instance['ServiceAddress']}")
            print(f"   Port: {instance['ServicePort']}")
            print(f"   Tags: {', '.join(instance.get('ServiceTags', []))}")
            
            # Show how to access this service
            address = instance['ServiceAddress'] or instance['Address']
            port = instance['ServicePort']
            print(f"\n   🌐 Access URL: http://{address}:{port}")
        
        print("\n" + "="*60)
        return instances
    else:
        print(f"❌ Failed to get service: {response.text}")
        return None

def check_service_health(service_name):
    """Check health of a specific service"""
    
    consul_url = get_consul_url()
    response = requests.get(f"{consul_url}/v1/health/service/{service_name}")
    
    if response.status_code == 200:
        checks = response.json()
        
        print(f"\n🏥 Health Check for: '{service_name}'")
        print("="*60)
        
        for check in checks:
            status = check['Status']
            status_icon = "✅" if status == "passing" else "❌" if status == "critical" else "⚠️"
            
            print(f"\n{status_icon} Check: {check['Name']}")
            print(f"   Status: {status.upper()}")
            print(f"   Notes: {check.get('Notes', 'N/A')}")
        
        print("\n" + "="*60)
        return checks
    else:
        print(f"❌ Failed to get health: {response.text}")
        return []

def demo_service_discovery():
    """Demonstrate service discovery workflow"""
    
    print("\n" + "="*60)
    print("🎯 CONSUL SERVICE DISCOVERY DEMO")
    print("="*60)
    
    # 1. List all services
    services = list_all_services()
    
    # 2. Discover specific services
    service_names = ['django-api', 'ai-service', 'auth-service']
    
    for service_name in service_names:
        get_service_by_name(service_name)
    
    # 3. Check health
    for service_name in service_names:
        check_service_health(service_name)
    
    print("\n💡 Service Discovery Benefits:")
    print("   • Services find each other dynamically")
    print("   • No hardcoded URLs or IPs")
    print("   • Automatic health checking")
    print("   • Load balancing ready")
    print("   • Service mesh foundation")
    print("\n📚 Consul UI: http://localhost:8500")
    print("="*60 + "\n")

if __name__ == "__main__":
    demo_service_discovery()
