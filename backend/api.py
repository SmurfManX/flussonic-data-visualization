import requests
import json
from datetime import datetime
from collections import Counter

# Server details
SERVERS = [
    "192.168.200.42",
    "192.168.200.43",
    "192.168.200.44",
    "192.168.200.45",
    "192.168.200.46"
]
HTTPS_USER = "FLUSSONIC_WEB_USER"
PASSWORD = "FLUSSONIC_WEB_PASSWORD"
URL_TEMPLATE = "http://{user}:{password}@{server}:8001/streamer/api/v3/sessions?limit=5000"

# Data aggregation
all_ips = []
ip_country_map = {}
live_ips = []
dvr_ips = []
protocol_counts = {}
country_counts = {}
non_georgia_ip_country = []
channel_counts = {}

# Process each server
for server in SERVERS:
    url = URL_TEMPLATE.format(user=HTTPS_USER, password=PASSWORD, server=server)
    response = requests.get(url)
    if response.status_code == 200:
        try:
            data = response.json()
            sessions = data if isinstance(data, list) else data.get("sessions", [])
            for session in sessions:
                if isinstance(session, dict):
                    # IP Address, Country, and Channel
                    ip = session.get('ip')
                    country = session.get('country', 'NONE')
                    channel = session.get('user_name')  # Get channel name from "user_name"
                    if ip:
                        all_ips.append(ip)
                        ip_country_map[ip] = country
                        if session.get('dvr') == True:
                            dvr_ips.append(ip)
                        else:
                            live_ips.append(ip)
                        if country != 'GE':
                            non_georgia_ip_country.append(f"{ip} - {country}")

                        # Channel Count
                        if channel:
                            channel_counts[channel] = channel_counts.get(channel, 0) + 1

                    # Protocol
                    proto = session.get('proto')
                    if proto:
                        protocol_counts[proto] = protocol_counts.get(proto, 0) + 1
#                    proto = session.get('proto')
#                    if proto and (proto.lower() in ['dash', 'hls']):
#                        protocol_counts[proto] = protocol_counts.get(proto, 0) + 1 

                    # Country Count
                    country_counts[country] = country_counts.get(country, 0) + 1

        except json.JSONDecodeError:
            print(f"Failed to decode JSON from server {server}")
    else:
        print(f"Failed to retrieve data from server {server}")

# Count occurrences and sort IP addresses
ip_counts = Counter(all_ips)
sorted_ip_counts = {ip: count for ip, count in ip_counts.most_common()}  # Sort by count

# Adding country code and comments for specific IPs
commented_sorted_ip_counts = {f"{ip} - Monitoring IP, {ip_country_map[ip]}" if ip == "31.146.2.170" else f"{ip}, {ip_country_map[ip]}": count for ip, count in sorted_ip_counts.items()}

# Constructing preview URLs and sorting channels
sorted_channel_counts = {}
BASE_PREVIEW_URL = "https://cdn-tbs1.adjara.com/"

for channel, count in sorted(channel_counts.items(), key=lambda item: item[1], reverse=True):
    sorted_channel_counts[channel] = {
        "clients": count,
        "live_preview_url": f"{BASE_PREVIEW_URL}{channel}/preview.jpg"
    }

# Prepare the output
output = {
    "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "total_client_count": len(all_ips),
    "live_client_count": len(live_ips),  # Total live IPs (not unique)
    "dvr_client_count": len(dvr_ips),    # Total DVR IPs (not unique)
    "protocols": protocol_counts,  # Counts per protocol
    "client_counts_by_country": country_counts,  # Counts per country
    "client_count_by_channels": sorted_channel_counts,  # Sorted counts per channel with preview URLs
    "non_geo_client_ip_addresses": non_georgia_ip_country,
    "sorted_ip_addresses_with_counts": commented_sorted_ip_counts  # Sorted IP addresses with counts, comments, and country codes
}

# Save output to a file
with open('/var/www/html/data.json', 'w') as file:
    json.dump(output, file, indent=4)

print("Data has been successfully saved to 'data.json'.")
