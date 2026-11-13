import json

filepath = r'C:\Users\admin\AppData\Local\Temp\trae\toolcall-output\c1fced5e-cd59-452f-b513-3f1f1f875a89.txt'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

prefix = "The MCP server responded with: "
idx = content.find(prefix)
if idx >= 0:
    content = content[idx + len(prefix):]

raw = json.loads(content)
text_content = raw[0]['text']
data = json.loads(text_content)

for m in data['matches']:
    num = m['matchNumStr']
    ht = m['home']['abbName']
    at = m['away']['abbName']
    hh = m['markets'].get('hhad', {})
    if hh:
        hcap = hh.get('handicap', 'N/A')
        print(f"\n{num} {ht} vs {at} | handicap={hcap}")
        for o in hh.get('outcomes', []):
            label = o.get('labelZh', '?')
            odds = o.get('odds', '?')
            prob = o.get('probability', 'N/A')
            print(f"  {label}={odds} prob={prob}")
    else:
        print(f"\n{num} {ht} vs {at} | NO HHAD")
