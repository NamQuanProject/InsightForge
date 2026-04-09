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
            "text": "Can I get trend about latest google trend and analysis content for it"
          }
        ]
      }
    },
    "id": 1
  }'

