"""Meety Intelligence — tầng AI độc lập với pipeline sáu pha.

    providers/          Adapter tới Gemini, Groq, mô hình cục bộ
    ai/agent.py         Chuỗi prompt chuyên biệt cho biên bản
    ai/collector.py     Thu dữ liệu chưng cất, ẩn danh trước khi ghi
    ai/consensus.py     Chạy song song và đối soát hai mô hình

Xem `ai/README.md` để biết lý do từng lớp tồn tại.
"""

from ai.agent import AgentResult, MeetingAgent, score_confidence
from ai.collector import DataCollector, anonymise_text
from ai.consensus import ComparisonReport, ConsensusEngine, compare_results

__all__ = [
    "MeetingAgent", "AgentResult", "score_confidence",
    "DataCollector", "anonymise_text",
    "ConsensusEngine", "ComparisonReport", "compare_results",
]
