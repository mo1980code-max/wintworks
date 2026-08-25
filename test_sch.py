import json
import urllib.parse
import re

with open('/home/user/wintworks/data/scholarships.json') as f:
    data = json.load(f)
    sch = data['scholarships'][0]
    title = sch['title']
    # Same logic as schNormalize
    raw_id = title.lower().replace(' ', '-')
    raw_id = re.sub(r'[^a-z0-9]+', '-', raw_id)
    raw_id = raw_id.strip('-')
    encoded_id = urllib.parse.quote(raw_id, safe='')
    print(f'Title: {title}')
    print(f'Raw ID: {raw_id}')
    print(f'Encoded ID: {encoded_id}')
    print(f'Full URL: http://localhost:9000/#/{encoded_id}')
