"""
Seed realistic lifehack/education mock content through the real persistence path.

This script intentionally uses ImageStoreService and PostgresService instead of
writing database rows by hand. Each generated content row only gets saved after
all planned images have been generated, copied into sample_data/img_db, embedded,
uploaded, and attached back to image_set.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import json
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db import init_db
from app.services.image_store_service import ImageStoreService
from app.services.postgres_service import PostgresService
from app.services.user_context import resolve_user_id


PROFILE_CONTEXT = {
    "brand": "Góc Nhỏ Thông Minh",
    "voice": "gần gũi, thực tế, có tính giáo dục nhưng không lên lớp",
    "audience": (
        "Người Việt 22-40 tuổi, bận rộn với công việc và gia đình, muốn các mẹo "
        "đơn giản để sống ngăn nắp hơn, tiết kiệm thời gian hơn và cải thiện bản thân."
    ),
}


MOCK_RUNS: list[dict[str, Any]] = [
    {
        "query": "mẹo vặt sức khỏe dễ làm cho người bận rộn",
        "trend": {
            "main_keyword": "uống đủ nước đúng cách",
            "why": (
                "Các nội dung về thói quen nhỏ cải thiện năng lượng trong ngày đang dễ được lưu lại, "
                "vì người xem muốn giải pháp đơn giản hơn là lời khuyên phức tạp."
            ),
            "score": 42.0,
            "interest": [24.0, 28.5, 31.0, 34.5, 38.0, 42.0],
            "velocity": 4100.0,
            "hashtags": ["#uongnuocdu", "#meovatsuckhoe", "#thoiquentot"],
            "action": "Tạo carousel 4 ảnh giải thích dấu hiệu thiếu nước và một cách nhắc uống nước dễ áp dụng.",
        },
        "content": {
            "title": "Uống đủ nước không khó: mẹo 3 chiếc ly cho ngày bận rộn",
            "hook": "Bạn không lười chăm sóc sức khỏe, có thể bạn chỉ chưa có một hệ thống nhắc mình đủ đơn giản.",
            "description": "Bài post hướng dẫn mẹo uống nước thực tế cho người hay quên vì lịch làm việc dày.",
            "body": (
                "Slide 1: Thiếu nước thường bắt đầu bằng mệt mỏi nhẹ.\n"
                "Slide 2: Đặt 3 chiếc ly ở 3 mốc thời gian: sáng, chiều, tối.\n"
                "Slide 3: Ghép uống nước với việc đã làm sẵn như mở laptop hoặc ăn trưa.\n"
                "Slide 4: Theo dõi bằng cảm giác tỉnh táo thay vì ép bản thân đạt con số hoàn hảo."
            ),
            "cta": "Lưu lại mẹo 3 chiếc ly và thử trong ngày mai.",
            "hashtags": ["#uongnuocdu", "#meovatsuckhoe", "#songthongminh", "#thoiquentot"],
            "slides": [
                (
                    "Dấu hiệu thiếu nước dễ bị bỏ qua",
                    "Ảnh mở đầu giúp người xem nhận ra cảm giác mệt, khô môi, thiếu tập trung có thể đến từ việc uống nước quá ít.",
                    "A busy Vietnamese young professional at a tidy desk, looking slightly tired while a nearly empty water glass sits beside a laptop, soft morning window light, realistic lifestyle photography, clean composition.",
                ),
                (
                    "Mẹo 3 chiếc ly",
                    "Ảnh minh họa hệ thống uống nước đơn giản theo ba mốc trong ngày, dễ áp dụng cho người bận rộn.",
                    "Three clear glasses of water labeled morning afternoon evening on a minimalist kitchen counter, bright natural light, organized and practical mood, realistic product photography.",
                ),
                (
                    "Gắn với thói quen có sẵn",
                    "Ảnh cho thấy cách đặt ly nước cạnh các hoạt động quen thuộc để biến việc uống nước thành phản xạ tự nhiên.",
                    "A glass of water placed next to a laptop, lunch bowl, and bedside book as a simple habit stacking visual, cozy Vietnamese apartment, warm natural light, realistic editorial style.",
                ),
                (
                    "Cơ thể tỉnh táo hơn",
                    "Ảnh kết thúc truyền cảm giác nhẹ nhàng, khỏe khoắn khi người xem duy trì được một thay đổi nhỏ.",
                    "A refreshed Vietnamese adult smiling calmly while drinking water near a bright window with plants, clean home setting, optimistic lifestyle photography, vibrant but natural colors.",
                ),
            ],
        },
    },
    {
        "query": "lifehack dọn nhà nhanh cho gia đình bận rộn",
        "trend": {
            "main_keyword": "dọn nhà 10 phút mỗi ngày",
            "why": (
                "Nội dung dọn dẹp ngắn, có checklist rõ ràng thường tạo nhiều lượt lưu vì giải quyết nỗi đau nhà bừa nhưng thiếu thời gian."
            ),
            "score": 47.0,
            "interest": [29.0, 31.5, 35.0, 39.0, 43.5, 47.0],
            "velocity": 5200.0,
            "hashtags": ["#donnhagon", "#lifehackgiadinh", "#meovatcuocsong"],
            "action": "Tạo bài post nhiều ảnh về quy tắc 10 phút và chia vùng dọn theo ngày.",
        },
        "content": {
            "title": "Nhà gọn hơn với quy tắc 10 phút: không cần tổng vệ sinh",
            "hook": "Một căn nhà gọn không bắt đầu từ cả ngày dọn dẹp, mà từ 10 phút có điểm dừng.",
            "description": "Bài post giáo dục nhẹ nhàng về cách dọn nhà theo vùng nhỏ để giảm áp lực.",
            "body": (
                "Slide 1: Vì sao càng nghĩ đến tổng vệ sinh càng dễ trì hoãn.\n"
                "Slide 2: Chọn một vùng nhỏ: bàn ăn, sofa hoặc kệ giày.\n"
                "Slide 3: Hẹn giờ 10 phút và chỉ làm 3 việc: gom, lau, trả đồ về chỗ.\n"
                "Slide 4: Ghi lại vùng đã xong để tạo cảm giác tiến bộ."
            ),
            "cta": "Tối nay chọn một góc nhỏ và đặt hẹn giờ 10 phút.",
            "hashtags": ["#donnhagon", "#meovatcuocsong", "#nhacuasachgon", "#lifehack"],
            "slides": [
                (
                    "Tổng vệ sinh làm bạn nản",
                    "Ảnh chỉ ra cảm giác quá tải khi nhìn cả căn phòng bừa bộn, tạo sự đồng cảm ngay từ đầu.",
                    "A realistic Vietnamese living room with mild everyday clutter, a person standing thoughtfully with a timer in hand, natural evening light, relatable home lifestyle scene.",
                ),
                (
                    "Chọn một vùng thật nhỏ",
                    "Ảnh hướng người xem tập trung vào một khu vực cụ thể thay vì cố dọn cả căn nhà.",
                    "A small dining table area before cleaning, highlighted as a single focus zone, cozy apartment, clear visual boundaries, realistic lifestyle photography.",
                ),
                (
                    "10 phút: gom, lau, trả đồ",
                    "Ảnh minh họa ba thao tác đơn giản trong một khoảng thời gian ngắn, tạo cảm giác làm được ngay.",
                    "A tidy cleaning scene with a small basket, microfiber cloth, and items being returned to shelves, visible kitchen timer set to 10 minutes, bright clean composition.",
                ),
                (
                    "Một góc gọn tạo động lực",
                    "Ảnh kết thúc bằng một góc nhà đã gọn gàng, tạo cảm giác nhẹ nhõm và có thành quả rõ.",
                    "A neatly organized small living room corner after a quick cleanup, warm lamp light, calm and satisfying atmosphere, realistic interior photography.",
                ),
            ],
        },
    },
    {
        "query": "câu chuyện giáo dục về thói quen tốt",
        "trend": {
            "main_keyword": "quy tắc 2 phút chống trì hoãn",
            "why": (
                "Các câu chuyện ngắn về thói quen cá nhân dễ được chia sẻ vì người xem thấy bản thân trong đó và có hành động nhỏ để thử ngay."
            ),
            "score": 44.0,
            "interest": [27.0, 30.0, 33.5, 37.0, 40.5, 44.0],
            "velocity": 3900.0,
            "hashtags": ["#thoiquentot", "#ky_nang_song", "#cauchuyengiaoduc"],
            "action": "Tạo carousel dạng câu chuyện ngắn, mỗi ảnh là một nhịp nhận ra và hành động.",
        },
        "content": {
            "title": "Quy tắc 2 phút: câu chuyện nhỏ để bắt đầu việc bạn cứ trì hoãn",
            "hook": "Có những việc không khó, chỉ khó ở khoảnh khắc bắt đầu.",
            "description": "Bài post kể chuyện ngắn về cách biến một việc lớn thành hành động đầu tiên chỉ mất 2 phút.",
            "body": (
                "Slide 1: Nhân vật cứ để việc nhỏ chất thành áp lực lớn.\n"
                "Slide 2: Người đó thử mở việc ra chỉ trong 2 phút.\n"
                "Slide 3: Khi đã bắt đầu, não bớt sợ việc đó hơn.\n"
                "Slide 4: Bài học: đừng đặt mục tiêu hoàn thành, hãy đặt mục tiêu khởi động."
            ),
            "cta": "Chọn một việc bạn đang né và làm phiên bản 2 phút ngay hôm nay.",
            "hashtags": ["#quytac2phut", "#thoiquentot", "#ky_nang_song", "#songthongminh"],
            "slides": [
                (
                    "Việc nhỏ chất thành núi",
                    "Ảnh mở đầu kể cảm giác áp lực khi nhiều việc nhỏ bị trì hoãn và dồn lại.",
                    "A Vietnamese young adult sitting at a desk with sticky notes and small unfinished tasks around, thoughtful expression, cinematic warm desk light, realistic storytelling image.",
                ),
                (
                    "Chỉ mở việc trong 2 phút",
                    "Ảnh minh họa hành động khởi động cực nhỏ: mở tài liệu, lấy bút, viết dòng đầu tiên.",
                    "Close-up of hands opening a notebook and writing the first line beside a two-minute timer, calm desk setup, shallow depth of field, realistic editorial photography.",
                ),
                (
                    "Bắt đầu làm nỗi sợ nhỏ lại",
                    "Ảnh truyền tải khoảnh khắc người xem nhận ra việc không đáng sợ như mình tưởng sau khi đã bắt đầu.",
                    "A person relaxing their shoulders and smiling slightly while working on a simple task, clean desk, soft light, motivational realistic lifestyle scene.",
                ),
                (
                    "Mục tiêu là khởi động",
                    "Ảnh kết luận bằng một checklist có dòng đầu tiên được tick, nhấn mạnh sự tiến bộ nhỏ nhưng thật.",
                    "A minimal checklist with the first tiny task checked off, a pen and cup of tea nearby, bright peaceful morning light, realistic close-up photography.",
                ),
            ],
        },
    },
    {
        "query": "mẹo sức khỏe đọc nhãn thực phẩm",
        "trend": {
            "main_keyword": "đường ẩn trong đồ uống đóng chai",
            "why": (
                "Người xem ngày càng quan tâm đến đường ẩn nhưng vẫn cần cách đọc nhãn thật đơn giản, không quá học thuật."
            ),
            "score": 49.0,
            "interest": [31.0, 34.0, 38.0, 41.0, 45.0, 49.0],
            "velocity": 6100.0,
            "hashtags": ["#duongan", "#meovatsuckhoe", "#songkhoe"],
            "action": "Tạo bài post hướng dẫn 3 điểm cần nhìn trên nhãn đồ uống trước khi mua.",
        },
        "content": {
            "title": "Đường ẩn trong đồ uống: 3 dòng trên nhãn bạn nên nhìn trước khi mua",
            "hook": "Một chai nhìn có vẻ lành mạnh vẫn có thể chứa nhiều đường hơn bạn nghĩ.",
            "description": "Bài post hướng dẫn đọc nhãn đồ uống đóng chai theo cách đơn giản và không gây hoang mang.",
            "body": (
                "Slide 1: Vấn đề không chỉ là đồ uống có ngọt hay không.\n"
                "Slide 2: Nhìn khẩu phần: một chai có thể nhiều hơn một khẩu phần.\n"
                "Slide 3: Tìm các tên khác của đường như syrup, fructose, sucrose.\n"
                "Slide 4: Chọn phiên bản ít đường hơn và uống nước lọc xen kẽ."
            ),
            "cta": "Lần tới mua đồ uống, hãy kiểm tra 3 dòng này trước khi bỏ vào giỏ.",
            "hashtags": ["#duongan", "#docnhanthucpham", "#meovatsuckhoe", "#songthongminh"],
            "slides": [
                (
                    "Đồ uống lành mạnh chưa chắc ít đường",
                    "Ảnh tạo tình huống quen thuộc khi người xem cầm một chai đồ uống đẹp mắt nhưng chưa biết lượng đường thật.",
                    "A hand holding a colorful bottled drink in a convenience store aisle, label visible but generic, curious and cautious mood, realistic Vietnamese shopping scene.",
                ),
                (
                    "Khẩu phần mới là điểm đầu tiên",
                    "Ảnh zoom vào phần serving size trên nhãn, giúp người xem nhớ cần kiểm tra số khẩu phần trong cả chai.",
                    "Close-up of a generic nutrition label with serving size area highlighted, clean educational composition, no brand names, bright store lighting, realistic macro photography.",
                ),
                (
                    "Đường có nhiều tên khác",
                    "Ảnh minh họa các tên gọi khác nhau của đường trên nhãn thành phần một cách dễ hiểu.",
                    "A clean flat lay of a generic ingredients list with words like syrup, fructose, sucrose highlighted in subtle color, educational health content style, sharp details.",
                ),
                (
                    "Chọn thông minh hơn",
                    "Ảnh kết thúc đưa lựa chọn nhẹ nhàng: đồ uống ít đường cạnh nước lọc, không cực đoan hóa vấn đề.",
                    "Two drink options on a table: a low-sugar bottled beverage and a glass of water with lemon, balanced healthy choice mood, bright natural light, realistic food photography.",
                ),
            ],
        },
    },
    {
        "query": "câu chuyện giáo dục kỹ năng sống cho người trưởng thành",
        "trend": {
            "main_keyword": "chiếc lọ ưu tiên cuộc sống",
            "why": (
                "Câu chuyện ẩn dụ về ưu tiên cuộc sống dễ phù hợp với nội dung giáo dục vì vừa dễ nhớ vừa có tính chia sẻ cao."
            ),
            "score": 45.0,
            "interest": [26.0, 29.0, 33.0, 37.5, 41.0, 45.0],
            "velocity": 4600.0,
            "hashtags": ["#cauchuyengiaoduc", "#kynangsong", "#songthongminh"],
            "action": "Tạo carousel kể chuyện chiếc lọ, đá lớn, sỏi nhỏ và bài học về ưu tiên.",
        },
        "content": {
            "title": "Chiếc lọ ưu tiên: câu chuyện nhỏ giúp bạn bớt sống theo việc vụn vặt",
            "hook": "Nếu bạn cho việc nhỏ vào trước, những điều quan trọng có thể không còn chỗ.",
            "description": "Bài post kể chuyện giáo dục về cách phân biệt ưu tiên lớn và việc nhỏ trong đời sống hằng ngày.",
            "body": (
                "Slide 1: Một chiếc lọ rỗng tượng trưng cho một ngày của bạn.\n"
                "Slide 2: Đá lớn là sức khỏe, gia đình, công việc quan trọng.\n"
                "Slide 3: Sỏi nhỏ là tin nhắn, việc vụn, những thứ chen ngang.\n"
                "Slide 4: Bài học: đặt đá lớn vào trước, rồi việc nhỏ sẽ tự tìm chỗ."
            ),
            "cta": "Viết ra 3 viên đá lớn của tuần này trước khi mở lịch làm việc.",
            "hashtags": ["#cauchuyengiaoduc", "#kynangsong", "#songthongminh", "#thoiquentot"],
            "slides": [
                (
                    "Chiếc lọ rỗng của một ngày",
                    "Ảnh mở đầu dùng chiếc lọ rỗng như biểu tượng cho thời gian và năng lượng hữu hạn của mỗi người.",
                    "A clear empty glass jar on a wooden desk, morning light, calm minimalist scene, symbolic educational storytelling, realistic photography.",
                ),
                (
                    "Đá lớn là điều quan trọng",
                    "Ảnh minh họa các ưu tiên lớn cần được đặt vào trước như sức khỏe, gia đình và công việc quan trọng.",
                    "Large smooth stones being placed into a glass jar, with subtle labels health family important work, warm natural light, realistic symbolic composition.",
                ),
                (
                    "Sỏi nhỏ là việc chen ngang",
                    "Ảnh cho thấy nhiều việc vụn có thể lấp đầy ngày nếu được đặt lên trước.",
                    "Small pebbles scattered beside a phone with notifications and a notebook, visual metaphor for interruptions, realistic desk scene, soft shadows.",
                ),
                (
                    "Đặt điều quan trọng vào trước",
                    "Ảnh kết thúc thể hiện chiếc lọ đã xếp hợp lý, gửi thông điệp ưu tiên điều lớn trước việc nhỏ.",
                    "A glass jar filled with large stones first and small pebbles fitting around them, peaceful organized desk, golden afternoon light, realistic inspirational photography.",
                ),
            ],
        },
    },
]


def build_trend_payload(run: dict[str, Any]) -> dict[str, Any]:
    trend = run["trend"]
    keyword = trend["main_keyword"]
    return {
        "query": run["query"],
        "results": [
            {
                "main_keyword": keyword,
                "why_the_trend_happens": trend["why"],
                "trend_score": trend["score"],
                "interest_over_day": trend["interest"],
                "avg_views_per_hour": trend["velocity"],
                "recommended_action": trend["action"],
                "top_videos": [],
                "top_hashtags": trend["hashtags"],
                "google": {
                    "keyword": keyword,
                    "momentum": "rising",
                    "peak_region": "Vietnam",
                },
                "tiktok": {
                    "platform": "TikTok",
                    "top_velocity": trend["velocity"],
                    "avg_engagement_rate": round(min(0.09, trend["score"] / 1000), 4),
                },
                "threads": None,
            }
        ],
        "markdown_summary": (
            f"Chủ đề '{keyword}' phù hợp với kênh {PROFILE_CONTEXT['brand']} vì vừa có tính ứng dụng "
            "vừa dễ kể thành bài post nhiều ảnh. Nên triển khai bằng giọng gần gũi, có ví dụ đời thường "
            "và CTA khuyến khích lưu bài."
        ),
        "error": None,
    }


def build_content_payload(run: dict[str, Any], run_index: int) -> dict[str, Any]:
    content = run["content"]
    keyword = run["trend"]["main_keyword"]
    hashtags = content["hashtags"]
    image_set = []
    for image_index, (title, description, prompt) in enumerate(content["slides"], start=1):
        image_set.append(
            {
                "index": image_index,
                "title": title,
                "description": description,
                "prompt": prompt,
                "style": "vivid",
                "size": "1792x1024",
                "output_path": f"mock_lifehack_{run_index:02d}_{image_index:02d}.png",
            }
        )

    platform_posts = {
        "tiktok": {
            "caption": f"{content['hook']} Xem carousel này để thử ngay một thay đổi nhỏ hôm nay.",
            "hashtags": hashtags[:4] + ["#learnontiktok"],
            "cta": content["cta"],
            "best_post_time": "19:30",
            "image_notes": "Dùng nhịp ảnh nhanh, chữ overlay ngắn và màu sáng để người xem dễ lưu lại.",
        },
        "facebook": {
            "caption": (
                f"{content['hook']}\n\n{content['description']}\n\n"
                f"{content['body']}\n\n{content['cta']}"
            ),
            "hashtags": hashtags,
            "cta": content["cta"],
            "best_post_time": "20:00",
            "image_notes": "Đăng dạng album 4 ảnh, phần caption giải thích rõ từng bước và giữ giọng không lên lớp.",
        },
        "instagram": {
            "caption": f"{content['title']}\n\n{content['description']}\n\n{content['cta']}",
            "hashtags": hashtags[:6],
            "cta": "Lưu bài để thử lại khi cần.",
            "best_post_time": "21:00",
            "image_notes": "Carousel cần thống nhất ánh sáng, bố cục sạch và tiêu đề ảnh ngắn gọn.",
        },
    }

    return {
        "selected_keyword": keyword,
        "main_title": content["title"],
        "post_content": {
            "post_type": "multi_image_post",
            "title": content["title"],
            "hook": content["hook"],
            "caption": (
                f"{content['hook']}\n\n{content['description']}\n\n{content['body']}\n\n"
                f"{content['cta']}"
            ),
            "description": content["description"],
            "body": content["body"],
            "call_to_action": content["cta"],
            "hashtags": hashtags,
            "tone": PROFILE_CONTEXT["voice"],
            "personalization_notes": [
                f"Cá nhân hóa theo thương hiệu {PROFILE_CONTEXT['brand']}: mẹo nhỏ, thực tế, có tính giáo dục.",
                f"Phù hợp audience: {PROFILE_CONTEXT['audience']}",
                "Các keyword/hashtag được chọn để không lặp quá sát giữa các bài seed.",
            ],
        },
        "image_set": image_set,
        "platform_posts": platform_posts,
        "publishing": {
            "default_visibility": "public",
            "recommended_platforms": ["facebook", "instagram", "tiktok"],
            "timezone": "Asia/Saigon",
            "weekly_content_frequency": 5,
        },
        "error": None,
    }


def collect_image_failures(image_set: list[dict[str, Any]]) -> list[str]:
    failures = []
    for image in image_set:
        if image.get("image_store_error"):
            failures.append(f"{image.get('output_path')}: {image['image_store_error']}")
        if not image.get("id") or not image.get("local_path") or not image.get("image_url"):
            failures.append(f"{image.get('output_path')}: missing stored image metadata")
    return failures


async def seed(count: int) -> list[dict[str, Any]]:
    load_dotenv(override=True)
    await init_db()

    user_id = resolve_user_id(None)
    if user_id is None:
        raise RuntimeError("No valid INSIGHTFORGE_DEFAULT_USER_ID configured.")

    postgres = PostgresService()
    image_store = ImageStoreService()
    user = await postgres.get_user(user_id)
    if user is None:
        raise RuntimeError(f"Configured user_id does not exist in users table: {user_id}")

    seeded = []
    for index, run in enumerate(MOCK_RUNS[:count], start=1):
        trend_payload = build_trend_payload(run)
        content_payload = build_content_payload(run, index)

        attached_images = await image_store.attach_post_images(content_payload["image_set"])
        failures = collect_image_failures(attached_images)
        if failures:
            raise RuntimeError(
                "Image generation/storage failed; database insert aborted.\n"
                + "\n".join(failures)
            )

        content_to_save = copy.deepcopy(content_payload)
        content_to_save["image_set"] = attached_images

        trend_record = await postgres.save_trend_analysis(
            query=trend_payload["query"],
            results=trend_payload["results"],
            summary=trend_payload["markdown_summary"],
            user_id=user_id,
            status="completed",
            error=None,
        )
        generated_record = await postgres.save_generated_content(
            raw_output=content_to_save,
            post_content=content_to_save["post_content"],
            image_set=attached_images,
            platform_posts=content_to_save["platform_posts"],
            publishing=content_to_save["publishing"],
            video_script={},
            user_id=user_id,
            trend_analysis_id=trend_record.id,
            selected_keyword=content_to_save["selected_keyword"],
            main_title=content_to_save["main_title"],
            status="generated",
        )

        seeded.append(
            {
                "trend_analysis_id": str(trend_record.id),
                "generated_content_id": str(generated_record.id),
                "selected_keyword": content_to_save["selected_keyword"],
                "image_count": len(attached_images),
                "local_paths": [image["local_path"] for image in attached_images],
            }
        )

    return seeded


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed mock lifehack content data.")
    parser.add_argument("--count", type=int, default=5, choices=range(1, 6))
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    seeded = await seed(count=args.count)
    print(json.dumps({"status": "success", "seeded": seeded}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
