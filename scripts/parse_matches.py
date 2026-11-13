import json

with open(r'C:\Users\admin\AppData\Local\Temp\trae\toolcall-output\2825afc0-9b72-4aec-b75d-9247d2908652.txt', 'r', encoding='utf-8') as f:
    raw = f.read()

# Find the first { that starts the JSON object
# The format is: The MCP server responded with: [{"type":"text","text":"{ ... }"}]
# We need to find the inner JSON string in the "text" field

# Find "text":" pattern
text_start = raw.find('"text":"')
if text_start != -1:
    text_start += len('"text":"')
    # Now we need to find the matching closing quote, but we need to handle escaped quotes
    # The text field contains a JSON string with escaped quotes
    # Let's find the end by looking for the pattern "}]} at the end
    
    # Actually, let's just find the JSON object that starts with {"updatedAt"
    json_start = raw.find('{\\n  \\"updatedAt\\"', text_start)
    if json_start == -1:
        json_start = raw.find('{\\n    \\"updatedAt\\"', text_start)
    
    # Try a different approach - find all content between text":" and "}]} 
    remaining = raw[text_start:]
    # Find the closing pattern "}]}
    end_idx = remaining.rfind('"}]')
    if end_idx != -1:
        json_str = remaining[:end_idx]
        # Unescape the JSON string
        json_str = json_str.replace('\\"', '"').replace('\\n', '\n')
        data = json.loads(json_str)
        
        for m in data['matches']:
            print(f'{m["matchNumStr"]} | {m["matchNumDate"]} | {m["league"]["abbName"]} | {m["home"]["abbName"]} vs {m["away"]["abbName"]} | {m["matchTime"]} | single={m.get("bettingSingle", False)}')
        
        print(f'\nTotal: {data["matchCount"]} matches, updated at {data["updatedAt"]}')
    else:
        print("Could not find end of JSON")
else:
    print("Could not find text field")
