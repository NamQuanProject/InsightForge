from upload_post import UploadPostClient

client = UploadPostClient(api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImJ1aWxlaG9hbmcucW5AZ21haWwuY29tIiwiZXhwIjo0OTI5NDk2MDg3LCJqdGkiOiI3NmQ2ZWIzNC0zMjE5LTQwNTgtYTBjNC0yOWFjMDBhNzliODkifQ.KbEelnG7qxuYGBdGiJDK0dRmetyeTFfRD_SyN1jbuTs")

response = client.upload_video(
    video_path="/path/to/video.mp4",
    title="My Awesome Video",
    user="blhoang23",
    platforms=["tiktok", "instagram"]
)
# curl.exe -X GET "https://api.upload-post.com/api/uploadposts/me" -H "Authorization: Apikey eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImJ1aWxlaG9hbmcucW5AZ21haWwuY29tIiwiZXhwIjo0OTI5NDk2MDg3LCJqdGkiOiI3NmQ2ZWIzNC0zMjE5LTQwNTgtYTBjNC0yOWFjMDBhNzliODkifQ.KbEelnG7qxuYGBdGiJDK0dRmetyeTFfRD_SyN1jbuTs"
# curl.exe -X GET "https://api.upload-post.com/api/uploadposts/users" -H "Authorization: Apikey eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImJ1aWxlaG9hbmcucW5AZ21haWwuY29tIiwiZXhwIjo0OTI5NDk2MDg3LCJqdGkiOiI3NmQ2ZWIzNC0zMjE5LTQwNTgtYTBjNC0yOWFjMDBhNzliODkifQ.KbEelnG7qxuYGBdGiJDK0dRmetyeTFfRD_SyN1jbuTs"
{
  "success": true,
  "access_url": "https://app.upload-post.com/connect?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImJ1aWxlaG9hbmcucW5AZ21haWwuY29tIiwicHJvZmlsZV91c2VybmFtZSI6ImJsaG9hbmcyMyIsImV4cCI6MTc3NjA3NDk5MSwiaWF0IjoxNzc1OTAyMTkxfQ.46wbvRFRlrnPDTs-YPikLvOFjTn91F4UWsRaeZpcNEU",
  "duration": "48h"
}