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
            "text": "I am based in Austin, TX. How do I get mental health therapy near me and what does my insurance cover?"
          }
        ]
      }
    },
    "id": 1
  }'

