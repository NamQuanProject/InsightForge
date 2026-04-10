import requests
import time
from typing import List, Dict, Any
import unicodedata
import re


class ThreadsTrendAnalyzer:
    def __init__(self, token: str):
        self.base_url = "https://ensembledata.com/apis"
        self.token = token

    def search_posts(self, keyword: str, sorting: str = "0") -> Dict[str, Any]:
        endpoint = "/threads/keyword/search"

        params = {
            "name": keyword,
            "sorting": sorting,  
            "token": self.token
        }

        try:
            res = requests.get(self.base_url + endpoint, params=params, timeout=30)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"[ERROR] search_posts: {e}")
            return {}

    # =====================================
    # 2. EXTRACT POSTS FROM SEARCH
    # =====================================
    def extract_posts(self, search_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        posts = []

        for item in search_json.get("data", []):
            node = item.get("node", {})
            thread = node.get("thread", {})

            thread_items = thread.get("thread_items", [])

            if not thread_items:
                continue

            post = thread_items[0].get("post", {})
            user = post.get("user", {})

            caption = post.get("caption", {}).get("text", "")

            posts.append({
                "post_id": post.get("pk"),
                "shortcode": post.get("code"),
                "username": user.get("username"),
                "is_verified": user.get("is_verified"),

                "text": caption,
                "likes": post.get("like_count", 0),
                "timestamp": post.get("taken_at", 0),

                "post_url": self.build_post_url(
                    user.get("username"),
                    post.get("code")
                )
            })

        return posts

    # =====================================
    # 3. FETCH REPLIES
    # =====================================
    def fetch_replies(self, post_id: str, shortcode: str) -> Dict[str, Any]:
        endpoint = "/threads/post/replies"

        params = {
            "id": post_id,
            "shortcode": shortcode,
            "token": self.token
        }

        try:
            res = requests.get(self.base_url + endpoint, params=params, timeout=30)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"[ERROR] fetch_replies: {e}")
            return {}

    # =====================================
    # 4. EXTRACT COMMENTS
    # =====================================
    def extract_comments(self, reply_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        comments = []

        for item in reply_json.get("data", []):
            node = item.get("node", {})
            thread_items = node.get("thread_items", [])

            for t in thread_items:
                post = t.get("post", {})
                user = post.get("user", {})
                text_info = post.get("text_post_app_info", {})

                fragments = text_info.get("text_fragments", {}).get("fragments", [])
                text = fragments[0].get("plaintext", "") if fragments else ""

                comments.append({
                    "comment_id": post.get("pk"),
                    "username": user.get("username"),
                    "is_verified": user.get("is_verified"),

                    "text": text,
                    "likes": post.get("like_count", 0),
                    "reply_count": text_info.get("direct_reply_count", 0),

                    "timestamp": post.get("taken_at", 0)
                })

        return comments

    # =====================================
    # 5. SCORING
    # =====================================
    def compute_engagement(self, c: Dict[str, Any]) -> float:
        return c["likes"] + 2 * c["reply_count"]

    def compute_trend_score(self, c: Dict[str, Any]) -> float:
        now = int(time.time())
        age = max(now - c["timestamp"], 1)
        return self.compute_engagement(c) / age

    def rank_comments(self, comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(
            comments,
            key=self.compute_trend_score,
            reverse=True
        )

    # =====================================
    # 6. URL BUILDER
    # =====================================
    def build_post_url(self, username: str, shortcode: str) -> str:
        if not username or not shortcode:
            return None
        return f"https://www.threads.net/@{username}/post/{shortcode}"

    # =====================================
    # 7. FULL PIPELINE (KEYWORD → POSTS → COMMENTS)
    # =====================================
    def analyze_keyword(
        self,
        keyword: str,
        top_posts: int = 5,
        top_comments: int = 5
    ) -> List[Dict[str, Any]]:

        # STEP 1: SEARCH POSTS
        search_json = self.search_posts(keyword)
        posts = self.extract_posts(search_json)

        results = []

        # STEP 2: FOR EACH POST → GET COMMENTS
        for post in posts[:top_posts]:
            post_id = post["post_id"]
            shortcode = post["shortcode"]

            replies_json = self.fetch_replies(post_id, shortcode)
            comments = self.extract_comments(replies_json)

            ranked_comments = self.rank_comments(comments)

            results.append({
                "post": post,
                "top_comments": ranked_comments[:top_comments],
                "total_comments": len(comments)
            })

        return results


# =====================================
# USAGE
# =====================================
if __name__ == "__main__":
    analyzer = ThreadsTrendAnalyzer(token="Zpwn5wkjp7AZcwu2")

    results = analyzer.analyze_keyword(
        keyword="chuyện lạ",
        top_posts=10,
        top_comments=1
    )

    for item in results:
        print("\n========================")
        print("POST:", item["post"]["post_url"])
        print("TEXT:", item["post"]["text"])
        print("LIKES:", item["post"]["likes"])

        print("\nTop Comments:")
        for c in item["top_comments"]:
            print({
                "user": c["username"],
                "text": c["text"],
                "score": round(analyzer.compute_trend_score(c), 6)
            })