#!/usr/bin/env python3
"""Nạp dữ liệu mẫu để thử backend — hai kịch bản cuộc họp thật.

Vì sao có tệp này (Bài toán 4)
------------------------------
Dữ liệu mẫu đã bị gỡ khỏi giao diện chính: sản phẩm qua giai đoạn demo, và
việc để lẫn "thật / mẫu" trên màn hình người dùng chỉ gây nghi ngờ dữ liệu nào
mới đúng. Nhưng lập trình viên vẫn cần thứ để bấm khi dựng môi trường mới, nên
nó chuyển vào đây — chạy khi cần, không bao giờ tự chạy.

Hai kịch bản, chọn có chủ đích
------------------------------
1. **Sprint Planning (kỹ thuật)** — hội thoại nhanh, nhiều thuật ngữ Anh-Việt
   lẫn lộn, có phản biện, có một quyết định bị đảo ngược giữa cuộc họp, và một
   việc **không ai nhận**. Đây là bài kiểm tra khó nhất cho phần trích xuất:
   quyết định bị thay thế và người nhận việc để trống là hai chỗ mô hình hay
   sai nhất.

2. **Business Strategy Discovery (kinh doanh)** — nhịp chậm hơn, câu dài, số
   liệu tài chính, hai người bất đồng và cuối cùng thoả hiệp. Có một đoạn
   **nghe không rõ** để kiểm đường xử lý thoại mờ, và một cam kết mức "dự kiến"
   để phân biệt với cam kết chắc.

Cách chạy::

    python tools/seed_data.py                     # nạp cho tài khoản đầu tiên
    python tools/seed_data.py --email a@b.vn      # nạp cho tài khoản cụ thể
    python tools/seed_data.py --create-user       # tạo luôn tài khoản thử
    python tools/seed_data.py --reset             # xoá dữ liệu mẫu cũ rồi nạp lại
    python tools/seed_data.py --export out/       # xuất ra .json để tải lên qua giao diện
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SEED_PREFIX = "seed_"


# ===========================================================================
#  KỊCH BẢN 1 — Sprint Planning
# ===========================================================================

SPRINT = {
    "id": "sprint25",
    "title": "Sprint 25 Planning — Thanh toán & Hiệu năng",
    "date": "2026-08-19",
    "type": "planning",
    "workspace": "w_prod",
    "people": [
        ("Phạm Quốc Hùng", "Product Lead"),
        ("Nguyễn Anh Tuấn", "Backend Engineer"),
        ("Trần Thị Lan", "QA Lead"),
        ("Lê Minh Khoa", "Hạ tầng"),
    ],
    "script": [
        (0, "Chào mọi người, mình là Hùng, Product Lead. Sprint 25 mình có hai mục tiêu chính, "
            "nhưng trước hết điểm nhanh sprint trước đã."),
        (1, "Tôi là Tuấn, Backend. Sprint 24 phần nhắc việc tự động đã xong, deploy lên staging "
            "hôm thứ 5. Còn cái query báo cáo thì vẫn 4.2 giây, chưa đạt mục tiêu dưới 2 giây."),
        (2, "Em là Lan, QA Lead. Bên em chạy hết 340 test case, pass 331, còn 9 case fail đều ở "
            "luồng thanh toán khi mạng chập chờn."),
        (0, "9 case fail ở thanh toán là nghiêm trọng. Sprint 25 mình ưu tiên số một là ổn định "
            "luồng thanh toán."),
        (3, "Em Khoa bên hạ tầng. Em muốn nói thêm là staging đang dùng chung database với "
            "môi trường dev, nên số đo hiệu năng không tin được."),
        (1, "Ừ đúng, cái đó ảnh hưởng luôn con số 4.2 giây tôi vừa nói. Có thể thực tế nhanh hơn."),
        (0, "Vậy chốt là sprint 25 làm ba việc: một là fix 9 case thanh toán, hai là tách "
            "database staging ra riêng, ba là tối ưu query báo cáo."),
        (3, "Ba việc trong hai tuần thì hơi nhiều anh ạ. Tách database mất khoảng 3 ngày, mà "
            "trong lúc tách thì cả team không test được."),
        (2, "Em đồng ý với Khoa. Nếu tách database giữa sprint thì em mất mấy ngày không chạy "
            "được hồi quy."),
        (0, "Hợp lý. Vậy mình sửa lại: sprint 25 chỉ làm hai việc là fix thanh toán và tối ưu "
            "query. Việc tách database chuyển sang sprint 26, làm ngay đầu sprint."),
        (1, "Tôi nhận phần tối ưu query báo cáo, sẽ xong trước ngày 28."),
        (2, "Chị nhận phần viết lại bộ test cho luồng thanh toán, có cả trường hợp mạng chập "
            "chờn. Xong trước thứ 6 tuần này."),
        (0, "Còn phần fix 9 case thanh toán thì ai làm? Tuấn đang bận query rồi."),
        (1, "Cái đó cần người hiểu cả frontend lẫn backend, để tôi hỏi bên mobile xem có ai "
            "rảnh không, chưa dám nhận."),
        (0, "Ok vậy để trống, tuần sau chốt lại. Còn tài liệu hướng dẫn tích hợp cổng thanh "
            "toán mới thì chưa ai viết, cũng để đó đã."),
        (3, "Em sẽ chuẩn bị sẵn kế hoạch tách database để sprint 26 vào là làm ngay, em làm "
            "trong tuần này."),
    ],
    "decisions": [
        {"s": "Sprint 25 làm ba việc: fix 9 test case thanh toán, tách database staging, "
              "và tối ưu query báo cáo",
         "by": "Phạm Quốc Hùng", "ev": 6, "dead": True,
         "q": "Vậy chốt là sprint 25 làm ba việc: một là fix 9 case thanh toán, hai là tách "
              "database staging ra riêng, ba là tối ưu query báo cáo."},
        {"s": "Sprint 25 chỉ làm hai việc: fix luồng thanh toán và tối ưu query báo cáo; "
              "việc tách database staging chuyển sang đầu sprint 26",
         "by": "Phạm Quốc Hùng", "ev": 9, "supersedes": 0,
         "q": "Vậy mình sửa lại: sprint 25 chỉ làm hai việc là fix thanh toán và tối ưu query. "
              "Việc tách database chuyển sang sprint 26, làm ngay đầu sprint."},
    ],
    "actions": [
        {"t": "Tối ưu query báo cáo xuống dưới 2 giây", "who": "Nguyễn Anh Tuấn", "ev": 10,
         "due": "2026-08-28", "strength": "firm",
         "q": "Tôi nhận phần tối ưu query báo cáo, sẽ xong trước ngày 28."},
        {"t": "Viết lại bộ test luồng thanh toán, gồm cả trường hợp mạng chập chờn",
         "who": "Trần Thị Lan", "ev": 11, "due": "2026-08-21", "strength": "firm",
         "q": "Chị nhận phần viết lại bộ test cho luồng thanh toán, có cả trường hợp mạng "
              "chập chờn. Xong trước thứ 6 tuần này."},
        {"t": "Fix 9 test case đang lỗi ở luồng thanh toán", "who": None, "ev": 13,
         "due": None, "strength": "tentative",
         "q": "Cái đó cần người hiểu cả frontend lẫn backend, để tôi hỏi bên mobile xem có ai "
              "rảnh không, chưa dám nhận."},
        {"t": "Viết tài liệu hướng dẫn tích hợp cổng thanh toán mới", "who": None, "ev": 14,
         "due": None, "strength": "tentative",
         "q": "Còn tài liệu hướng dẫn tích hợp cổng thanh toán mới thì chưa ai viết, cũng để đó đã."},
        {"t": "Chuẩn bị kế hoạch tách database staging cho sprint 26", "who": "Lê Minh Khoa",
         "ev": 15, "due": "2026-08-22", "strength": "firm",
         "q": "Em sẽ chuẩn bị sẵn kế hoạch tách database để sprint 26 vào là làm ngay, em làm "
              "trong tuần này."},
    ],
    "warns": [
        ("AMBIGUOUS_ASSIGNEE", 2, "high"),
        ("SUPERSEDED_DEPENDENCY", 1, "medium"),
        ("LOW_COMMITMENT_STRENGTH", 2, "medium"),
    ],
    "metrics": [("Test case đạt", "331/340"), ("Thời gian query báo cáo", "4.2 giây"),
                ("Test case lỗi ở thanh toán", "9")],
    "low_seg": None,
}


# ===========================================================================
#  KỊCH BẢN 2 — Business Strategy Discovery
# ===========================================================================

STRATEGY = {
    "id": "strategy_q4",
    "title": "Họp chiến lược Quý 4 — Mở rộng thị trường miền Trung",
    "date": "2026-08-20",
    "type": "board",
    "workspace": "w_fin",
    "people": [
        ("Đặng Thu Hà", "Giám đốc điều hành"),
        ("Vũ Trọng Nam", "Giám đốc kinh doanh"),
        ("Bùi Thị Mai", "Kế toán trưởng"),
        ("Phạm Quốc Hùng", "Product Lead"),
    ],
    "script": [
        (0, "Mình là Hà, điều hành. Hôm nay bàn về việc mở rộng ra miền Trung trong quý 4. "
            "Nam trình bày trước đi."),
        (1, "Tôi là Nam, kinh doanh. Theo khảo sát của bên tôi, Đà Nẵng và Huế có khoảng 340 "
            "doanh nghiệp trong nhóm khách hàng mục tiêu. Nếu chiếm được 5% trong sáu tháng "
            "thì doanh thu tăng thêm khoảng 1,8 tỷ một năm."),
        (2, "Em là Mai, kế toán trưởng. Em phải nói ngay là con số 1,8 tỷ đó là doanh thu, "
            "không phải lợi nhuận. Chi phí mở văn phòng Đà Nẵng, thuê người, đi lại — em ước "
            "tính khoảng 1,2 tỷ cho năm đầu."),
        (1, "Chị Mai tính cả văn phòng vật lý à? Bên tôi định làm mô hình bán hàng từ xa trước, "
            "chỉ cử người vào theo đợt."),
        (2, "Nếu vậy thì chi phí xuống còn khoảng 400 triệu. Nhưng tôi vẫn lo tỷ lệ chốt đơn "
            "từ xa ở thị trường đó thấp hơn nhiều so với Hà Nội."),
        (0, "Đây là điểm quan trọng. Nam có số liệu nào về tỷ lệ chốt từ xa không?"),
        (1, "Có, nhưng là số của thị trường Hải Phòng chứ không phải miền Trung. Ở Hải Phòng "
            "bán từ xa chốt được 11%, còn có người tại chỗ thì 19%."),
        (3, "Anh Hùng đây. Về phía sản phẩm, nếu vào thị trường mới thì phải bổ sung phần "
            "xuất hoá đơn theo mẫu của một số tỉnh, cái đó mất khoảng sáu tuần."),
        (0, "Sáu tuần thì kịp trước quý 4 không?"),
        (3, "Kịp nếu bắt đầu trong tháng này. Bắt đầu tháng sau thì không kịp."),
        (2, "Em đề xuất làm thử ở Đà Nẵng trước, ba tháng, ngân sách trần 400 triệu. Đạt được "
            "tỷ lệ chốt trên 8% thì mới mở tiếp ra Huế và mở văn phòng."),
        (1, "Tôi đồng ý với phương án thử trước, nhưng xin nâng trần lên 500 triệu để có ngân "
            "sách marketing tại chỗ."),
        (0, "Vậy chốt: thử nghiệm ba tháng tại Đà Nẵng theo mô hình bán hàng từ xa, ngân sách "
            "trần 450 triệu, đánh giá lại vào cuối tháng 11 dựa trên tỷ lệ chốt đơn 8%."),
        (1, "Tôi nhận phần lập kế hoạch triển khai chi tiết cho Đà Nẵng, gửi trước ngày 25."),
        (2, "Em sẽ dựng bảng theo dõi chi phí riêng cho dự án thử nghiệm này, xong trong tuần."),
        (3, "Phần xuất hoá đơn theo mẫu tỉnh thì... [không nghe rõ] ...cần xác nhận lại danh "
            "sách tỉnh trước khi bắt đầu."),
        (0, "Hùng xác nhận lại rồi báo mình nhé. Còn việc tuyển người phụ trách khu vực miền "
            "Trung thì chưa bàn hôm nay, để buổi sau."),
    ],
    "decisions": [
        {"s": "Thử nghiệm ba tháng tại Đà Nẵng theo mô hình bán hàng từ xa, ngân sách trần "
              "450 triệu, đánh giá lại cuối tháng 11 theo tỷ lệ chốt đơn 8%",
         "by": "Đặng Thu Hà", "ev": 12,
         "q": "Vậy chốt: thử nghiệm ba tháng tại Đà Nẵng theo mô hình bán hàng từ xa, ngân "
              "sách trần 450 triệu, đánh giá lại vào cuối tháng 11 dựa trên tỷ lệ chốt đơn 8%."},
    ],
    "actions": [
        {"t": "Lập kế hoạch triển khai chi tiết cho thị trường Đà Nẵng",
         "who": "Vũ Trọng Nam", "ev": 13, "due": "2026-08-25", "strength": "firm",
         "q": "Tôi nhận phần lập kế hoạch triển khai chi tiết cho Đà Nẵng, gửi trước ngày 25."},
        {"t": "Dựng bảng theo dõi chi phí riêng cho dự án thử nghiệm",
         "who": "Bùi Thị Mai", "ev": 14, "due": "2026-08-22", "strength": "firm",
         "q": "Em sẽ dựng bảng theo dõi chi phí riêng cho dự án thử nghiệm này, xong trong tuần."},
        {"t": "Xác nhận danh sách tỉnh cần bổ sung mẫu hoá đơn",
         "who": "Phạm Quốc Hùng", "ev": 15, "due": None, "strength": "tentative",
         "q": "Phần xuất hoá đơn theo mẫu tỉnh thì... [không nghe rõ] ...cần xác nhận lại danh "
              "sách tỉnh trước khi bắt đầu."},
        {"t": "Tuyển người phụ trách khu vực miền Trung", "who": None, "ev": 16,
         "due": None, "strength": "tentative",
         "q": "Còn việc tuyển người phụ trách khu vực miền Trung thì chưa bàn hôm nay, "
              "để buổi sau."},
    ],
    "warns": [
        ("AMBIGUOUS_ASSIGNEE", 1, "high"),
        ("TRANSCRIPT_GAPS", 1, "low"),
        ("LOW_COMMITMENT_STRENGTH", 2, "medium"),
    ],
    "metrics": [("Doanh nghiệp mục tiêu tại Đà Nẵng và Huế", "340"),
                ("Doanh thu dự kiến nếu chiếm 5%", "1,8 tỷ/năm"),
                ("Ngân sách trần thử nghiệm", "450 triệu"),
                ("Tỷ lệ chốt từ xa tại Hải Phòng", "11%"),
                ("Tỷ lệ chốt có người tại chỗ", "19%")],
    "low_seg": 15,
}

SCENARIOS = [SPRINT, STRATEGY]

WARN_MSG = {
    "AMBIGUOUS_ASSIGNEE": "Công việc được nêu ra nhưng chưa ai nhận trong cuộc họp.",
    "SUPERSEDED_DEPENDENCY": "Cam kết dựa trên một quyết định về sau đã bị thay đổi.",
    "TRANSCRIPT_GAPS": "Có đoạn hệ thống nghe không chắc, độ tin cậy thấp hơn.",
    "LOW_COMMITMENT_STRENGTH": "Người nói mới ở mức dự kiến, chưa phải cam kết dứt khoát.",
}


# ===========================================================================
#  Dựng dữ liệu
# ===========================================================================

def build(scn: dict) -> tuple[dict, dict]:
    """Dựng cặp (minutes, transcript) đúng hình dạng schema backend."""
    segs, t = [], 5000
    for i, (who, text) in enumerate(scn["script"]):
        dur = max(6000, min(26000, len(text) * 95))
        low = scn.get("low_seg") == i
        segs.append({
            "id": f"s_{i + 1:04d}", "index": i + 1, "speaker_label": f"SPEAKER_{who:02d}",
            "person_id": f"p_{who + 1}", "start_ms": t, "end_ms": t + dur, "text": text,
            "lang": "mixed" if any(c.isascii() and c.isalpha() for c in text) else "vi",
            "asr_confidence": 0.42 if low else 0.87 + (i % 7) / 100,
            "is_overlapped": low, "is_low_quality": low,
        })
        t += dur + 800
    total = t + 4000

    speakers = []
    for i, (name, role) in enumerate(scn["people"]):
        mine = [s for s in segs if s["speaker_label"] == f"SPEAKER_{i:02d}"]
        ms = sum(s["end_ms"] - s["start_ms"] for s in mine)
        speakers.append({
            "label": f"SPEAKER_{i:02d}", "person_id": f"p_{i + 1}", "display_name": name,
            "role": role, "identification_method": "self_intro" if mine else "pending",
            "identification_confidence": 0.95 if mine else 0.0,
            "talk_time_ms": ms, "talk_time_pct": round(ms / max(1, t - 5000) * 1000) / 10,
            "evidence_for_identification": [mine[0]["id"]] if mine else [],
        })

    decisions = []
    for i, d in enumerate(scn["decisions"]):
        decisions.append({
            "id": f"d_{i + 1:03d}", "statement": d["s"], "decided_by": d["by"],
            "quote": d["q"], "status": "rejected" if d.get("dead") else "decided",
            "supersedes": f"d_{d['supersedes'] + 1:03d}" if "supersedes" in d else None,
            "superseded_by": None, "target_date": None, "rationale": None,
            "alternatives_considered": [], "objections": [],
            "evidence_segment_ids": [f"s_{d['ev'] + 1:04d}"],
            "timestamp_ms": segs[d["ev"]]["start_ms"],
            "confidence": "high", "review_state": "ai_generated",
        })
    for d in decisions:
        if d["supersedes"]:
            old = next((x for x in decisions if x["id"] == d["supersedes"]), None)
            if old:
                old["superseded_by"] = d["id"]

    actions = []
    for i, a in enumerate(scn["actions"]):
        actions.append({
            "id": f"a_{i + 1:03d}", "task": a["t"], "assignee": a["who"],
            "assignee_raw": a["who"], "quote": a["q"], "due_date": a["due"],
            "due_raw": "theo lời nói" if a["due"] else None,
            "due_resolution_rule": "EXPLICIT" if a["due"] else "NOT_MENTIONED",
            "commitment_strength": a["strength"], "priority": "high", "status": "open",
            "depends_on": [], "related_decision_id": None, "carried_over_from": None,
            "needs_review": not a["who"] or a["strength"] != "firm",
            "evidence_segment_ids": [f"s_{a['ev'] + 1:04d}"],
            "timestamp_ms": segs[a["ev"]]["start_ms"],
            "confidence": "high" if a["who"] else "low", "review_state": "ai_generated",
        })

    minutes = {
        "minutes_id": f"min_{SEED_PREFIX}{scn['id']}", "meeting_id": f"{SEED_PREFIX}{scn['id']}",
        "version": 1,
        "meta": {
            "meeting_title": scn["title"], "date": scn["date"],
            "duration_minutes": round(total / 60000), "meeting_type": scn["type"],
            "language": "vi",
            "attendees": [{"person_id": s["person_id"], "display_name": s["display_name"],
                           "speaker_label": s["label"], "role": s["role"],
                           "talk_time_pct": s["talk_time_pct"],
                           "identification_method": s["identification_method"]}
                          for s in speakers],
        },
        "executive_summary": {
            "tldr": ([d["statement"] + "." for d in decisions if not d["superseded_by"]]
                     + [f"{a['assignee']} nhận việc: {a['task'].lower()}." if a["assignee"]
                        else f"Chưa có người nhận việc: {a['task'].lower()}."
                        for a in actions[:3]])[:5],
            "paragraphs": [" ".join(x[1] for x in scn["script"])[:520] + "…"],
        },
        "chapters": [], "discussion_points": [], "decisions": decisions,
        "action_items": actions, "risks": [],
        "metrics": [{"id": f"m_{i}", "label": k, "value_raw": v,
                     "evidence_segment_ids": [segs[0]["id"]],
                     "timestamp_ms": segs[0]["start_ms"], "confidence": "high",
                     "period": None, "trend": None}
                    for i, (k, v) in enumerate(scn["metrics"])],
        "open_questions": [], "next_meeting": None,
        "quality_report": {
            "overall_confidence": "medium" if scn["warns"] else "high",
            "needs_human_review": True,
            "warnings": [{"code": c, "message": WARN_MSG.get(c, ""), "severity": sev,
                          "affected_items": [f"x_{i}" for i in range(n)]}
                         for c, n, sev in scn["warns"]],
        },
        "validation": {"grounding_score": 1.0, "checks": {}, "schema_valid": True},
        "pipeline": {"asr_provider": "seed", "llm_provider": "seed",
                     "total_llm_requests": 0, "cost_usd": 0},
    }
    transcript = {
        "transcript_id": f"tr_{SEED_PREFIX}{scn['id']}",
        "meeting_id": f"{SEED_PREFIX}{scn['id']}", "version": 1,
        "meta": {"title": scn["title"], "meeting_date": scn["date"], "duration_ms": total,
                 "meeting_type": scn["type"], "glossary": []},
        "speakers": speakers, "segments": segs, "chunks": [],
        "language_profile": {"primary": "vi", "secondary": ["en"], "code_switching": True},
        "quality": {"overall_score": 0.74 if scn.get("low_seg") is not None else 0.88},
    }
    return minutes, transcript


# ===========================================================================
#  Nạp vào DB
# ===========================================================================

# Hai tài khoản kiểm thử theo Hạng mục 10.
TEST_ACCOUNTS = [
    ("owner@meety.ai",  "admin123", "Phạm Quốc Hùng", "Trưởng nhóm sản phẩm"),
    ("member@meety.ai", "user123",  "Trần Thị Lan",   "QA Lead"),
]


def seed_test_accounts() -> int:
    """Dựng sẵn luồng kiểm thử phân quyền: Owner có cuộc họp, Member được mời.

    Mật khẩu ngắn (admin123 / user123) CỐ Ý đặt dưới ngưỡng 8 ký tự của
    endpoint đăng ký, nên hai tài khoản này phải tạo thẳng qua tầng store.
    Đó là chủ ý: chúng chỉ dùng để thử trên máy, và việc chúng KHÔNG đăng ký
    được qua giao diện là bằng chứng ràng buộc mật khẩu đang có hiệu lực.
    """
    from core import env
    env.load_dotenv()
    from server import security, store

    users = {}
    for email, pw, name, title in TEST_ACCOUNTS:
        u = store.get_user_by_email(email)
        if u:
            # Đặt lại mật khẩu để lần chạy sau luôn dùng được, kể cả khi ai đó
            # đã đổi trong lúc thử.
            store.update_user(u["id"], password_hash=security.hash_password(pw))
            print(f"  · {email} đã có, đặt lại mật khẩu về {pw}")
        else:
            u = store.create_user(email=email, display_name=name,
                                  password_hash=security.hash_password(pw),
                                  role_title=title)
            print(f"  ✓ Tạo {email} / {pw}  ({name})")
        users[email] = u

    owner = users["owner@meety.ai"]
    member = users["member@meety.ai"]

    for scn in SCENARIOS:
        minutes, transcript = build(scn)
        mid = f"{SEED_PREFIX}{scn['id']}__{owner['id']}"
        store.create_meeting(owner["id"], meeting_id=mid, title=scn["title"],
                             meeting_date=scn["date"], workspace_id=scn["workspace"],
                             kind="real", status="pending", job_state="done",
                             minutes=minutes, transcript=transcript)
        store.add_owner(mid, owner)
        store.invite_member(mid, member["email"], owner["id"])
        auto = store.auto_assign(mid, owner["id"])
        print(f"  ✓ {scn['title']}")
        print(f"      Owner: {owner['email']} · đã mời {member['email']} · tự gán {auto} việc")

    store.add_notification(member["id"], "Bạn được mời vào 2 cuộc họp",
                           "Đăng nhập để xem biên bản")
    print(f"""
Xong. Luồng kiểm thử:

  1. Đăng nhập  owner@meety.ai / admin123
     → thấy 2 cuộc họp, có toàn quyền: mời người, gán việc, phê duyệt, xuất Word.
  2. Đăng nhập  member@meety.ai / user123   (mở cửa sổ ẩn danh để dùng song song)
     → thấy đúng 2 cuộc họp đó ở chế độ chỉ đọc, chỉ thấy việc giao cho mình.
  3. Ở tài khoản Owner, vào khối Thành viên, bấm menu cạnh {member['display_name']}
     → "Chỉ định làm đồng chủ toạ" và kiểm lại quyền bên tài khoản Member.
""")
    store.close_all()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Nạp cuộc họp mẫu để thử backend Meety")
    ap.add_argument("--email", help="Email tài khoản nhận dữ liệu mẫu")
    ap.add_argument("--create-user", action="store_true",
                    help="Tạo tài khoản thử nếu chưa có (mật khẩu: meety-demo-2026)")
    ap.add_argument("--accounts", action="store_true",
                    help="Tạo hai tài khoản kiểm thử owner@meety.ai và member@meety.ai, "
                         "nạp cuộc họp cho Owner rồi mời Member vào")
    ap.add_argument("--reset", action="store_true", help="Xoá dữ liệu mẫu cũ trước khi nạp")
    ap.add_argument("--export", metavar="THƯ_MỤC",
                    help="Chỉ xuất .json để tải lên qua giao diện, không đụng DB")
    args = ap.parse_args()

    if args.accounts:
        return seed_test_accounts()

    if args.export:
        out = Path(args.export)
        out.mkdir(parents=True, exist_ok=True)
        for scn in SCENARIOS:
            _minutes, transcript = build(scn)
            path = out / f"{scn['id']}.json"
            path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2),
                            encoding="utf-8")
            print(f"  ✓ {path}  ({len(transcript['segments'])} lượt nói)")
        print("\nTải các tệp này lên qua nút “＋ Tạo cuộc họp mới” để chạy pipeline thật.")
        return 0

    from core import env
    env.load_dotenv()
    from server import security, store

    email = args.email
    if email:
        user = store.get_user_by_email(email)
    else:
        row = store.db().execute("SELECT id FROM users ORDER BY created_at LIMIT 1").fetchone()
        user = store.get_user(row["id"]) if row else None

    if not user and args.create_user:
        email = email or "demo@meety.vn"
        user = store.create_user(
            email=email, display_name="Người Dùng Thử",
            password_hash=security.hash_password("meety-demo-2026"),
            role_title="Quản trị thử nghiệm")
        print(f"  ✓ Đã tạo tài khoản {email} (mật khẩu: meety-demo-2026)")

    if not user:
        print("Không tìm thấy tài khoản nào.\n"
              "  Đăng ký qua giao diện trước, hoặc chạy lại với --create-user")
        return 1

    if args.reset:
        n = 0
        for m, _role in store.list_meetings_for_user(user["id"]):
            if SEED_PREFIX in m["id"]:
                store.delete_meeting(m["id"], user["id"])
                n += 1
        print(f"  ✓ Đã xoá {n} cuộc họp mẫu cũ")

    for scn in SCENARIOS:
        minutes, transcript = build(scn)
        mid = f"{SEED_PREFIX}{scn['id']}__{user['id']}"
        store.create_meeting(
            user["id"], meeting_id=mid, title=scn["title"], meeting_date=scn["date"],
            workspace_id=scn["workspace"], kind="real", status="pending",
            job_state="done", minutes=minutes, transcript=transcript)
        store.add_owner(mid, user)
        auto = store.auto_assign(mid, user["id"])
        unassigned = sum(1 for a in minutes["action_items"] if not a["assignee"])
        print(f"  ✓ {scn['title']}")
        print(f"      {len(transcript['segments'])} lượt nói · "
              f"{len(minutes['decisions'])} quyết định · "
              f"{len(minutes['action_items'])} công việc "
              f"({unassigned} chưa có người nhận) · tự gán {auto}")

    store.add_notification(user["id"], "Đã nạp cuộc họp mẫu",
                           f"{len(SCENARIOS)} kịch bản để thử toàn bộ hệ thống")
    print(f"\nXong. Đăng nhập bằng {user['email']} để xem.")
    store.close_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
