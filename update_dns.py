import requests
from dotenv import load_dotenv
import os
from cloudflare import Cloudflare

# Cloudflare API Credentials
BASE_URL = "https://api.cloudflare.com/client/v4/zones"
load_dotenv()
ZONE_NAME = os.getenv('ZONE_NAME')
RECORD_NAME = os.getenv('RECORD_NAME')

def get_public_ip():
    try:
        response = requests.get("https://api64.ipify.org?format=json")
        response.raise_for_status()
        return response.json()["ip"]
    except requests.RequestException as e:
        print(f"Error fetching IP: {e}")
        return None

def get_dns_record(cf: Cloudflare, zone_id):
    """Fetches the current DNS A record for the domain using Cloudflare library."""
    try:
        print("Grabbing zone...")
        zone = cf.zones.get(zone_id=zone_id)
        print(f'Zone ID: {zone.id}')
        print("Grabbing dns record...")
        dns_records = cf.dns.records.list(zone_id=zone_id)
        for record in dns_records:
            if record.type == "A" and record.name == ZONE_NAME:
                return record.id, record.content
        print("No A record found.")
        return None, None
    except Exception as e:
        print(f"Error fetching DNS record: {e}")
        return None, None

def update_dns_record(cf: Cloudflare, zone_id, current_ip):
    """Updates the DNS A record for the domain using Cloudflare library."""
    record_id, domain_ip = get_dns_record(cf, zone_id)
    print(record_id, domain_ip)
    if not record_id:
        print("Unable to find DNS record ID.")
        return

    print(f"Current IP {current_ip}, Domain IP {domain_ip}")
    if current_ip == domain_ip:
        print("No-op")
        return

    try:
        cf.dns.records.update(dns_record_id=record_id, zone_id=zone_id, type="A", name="@", content=current_ip, ttl=60)
        print(f"DNS record updated successfully to {current_ip}")
    except Exception as e:
        print(f"Error updating DNS record: {e}")

def get_zone(cf: Cloudflare, name: str):
    zones = cf.zones.list(name=name)
    if not zones:
        print(f"No zone found matching {name}")
        return None
    return zones.result[0]

def main():
    cf = Cloudflare(
        api_token=os.environ.get("CLOUDFLARE_API_TOKEN")
    )
    try:
        zone = get_zone(cf, ZONE_NAME)
        if not zone:
            return

        print(f"Zone ID: {zone.id}")
        ip = get_public_ip()
        if ip:
            print(f"Current IP: {ip}")
            update_dns_record(cf, zone.id, ip)
        else:
            print("Failed to retrieve IP address.")
    except Exception as e:
        print(f"Error fetching Cloudflare zones: {e}")

if __name__ == "__main__":
    main()
