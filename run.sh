python -m agents.trend_agent.main
python main.py

curl -X POST "https://open.tiktokapis.com/v2/oauth/token/" \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --header 'Cache-Control: no-cache' \
  --data-urlencode "client_key=aw6yke9o89kram7t" \
  --data-urlencode "client_secret=DbNvQcKnJnGES5AQYgGzwfFfClFDEbBD" \
  --data-urlencode "grant_type=client_credentials"

  curl --location 'https://open.tiktokapis.com/v2/research/video/query/?fields=id%2Clike_count' \
--header 'Authorization: Bearer clt.2.vOkPc2funEG07oAL6YGXe-NUFhCV5foRL6JolthL9jk7FLg1N-b9U6utUM7UcSN3RnsavsFQCSJxIRgOYGXHMw*0' \
--header 'Content-Type: application/json' \
--data '{
  "query": {
              "and": [
                   { "operation": "IN", "field_name": "region_code", "field_values": ["US", "CA"] },
                   { "operation": "EQ", "field_name": "keyword", "field_values": ["hello world"] }
               ]
          }, 
  "max_count": 100,
    "cursor": 0,
    "start_date": "20181207",
    "end_date": "20181207",
    "is_random": false}
'