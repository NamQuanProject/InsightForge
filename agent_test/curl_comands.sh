curl -X POST http://localhost:5000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "msg-123",
        "role": "user",
        "parts": [
          {
            "kind": "text",
            "text": "Can you upload for me a photo at sample_data/image.png with username blhoang23 to instagram with description test post?"
          }
        ]
      }
    },
    "id": 1
  }'
