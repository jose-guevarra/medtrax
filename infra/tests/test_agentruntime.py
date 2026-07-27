import boto3
import json

client = boto3.client('bedrock-agentcore', region_name='us-east-1')
payload = json.dumps({"prompt": "What can you do?"})
payload = json.dumps({"prompt": "please add 23 plus 44444"})

AGENT_RUNTIME_ARN="arn:aws:bedrock-agentcore:us-east-1:087045461309:runtime/MedTraxAgent-y9BUuLB1ZH"

SESSION_ID=""

response = client.invoke_agent_runtime(
    agentRuntimeArn=AGENT_RUNTIME_ARN,
    #runtimeSessionId=SESSION_ID, # Must be 33+ char. Every new SessionId will create a new MicroVM
    payload=payload,
    #qualifier="<Replace with your Endpoint>" # This is Optional. When the field is not provided, Runtime will use DEFAULT endpoint
)

print("RESP: ", response)

content_type = response.get('contentType', '')

if 'text/event-stream' in content_type:
    # Iterate over the stream line by line
    for line in response['response'].iter_lines(chunk_size=1024):
        if line:
            # Decode the byte line to string
            line_str = line.decode('utf-8')
            
            # Server-Sent Events usually prefix data with "data: "
            if line_str.startswith('data: '):
                data_payload = line_str[6:] # Remove "data: " prefix
                
                # Parse the JSON chunk
                try:
                    chunk_json = json.loads(data_payload)
                    #print(f"Received chunk: {chunk_json}")
                    #print(chunk_json['event'])
                    if chunk_json['event'].get('contentBlockDelta'):
                        if chunk_json['event'].get('contentBlockDelta').get('delta').get('text'):
                            print(chunk_json['event']['contentBlockDelta']['delta']['text'], end="")
                except json.JSONDecodeError:
                    print(f"Raw data: {data_payload}")
else:
    # Fallback for non-streaming JSON
    json_data = json.loads(response['response'].read().decode('utf-8'))
    print(json_data)
print("done.")