"""Test cho hạ tầng log.

Module này nằm giữa **bí mật** và **đĩa cứng**. Một lỗi ở đây không làm sập
chương trình — nó chỉ âm thầm ghi API key vào file log rồi người dùng dán
file đó lên diễn đàn để hỏi. Vì vậy nhóm test này kiểm cả các định dạng key
mà dự án chưa dùng tới, phòng khi thêm nhà cung cấp về sau.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from core.logging import (
    SecretRedactingFilter,
    _KNOWN_SECRETS,
    configure_logging,
    redact,
    register_secret,
)

FAKE_GROQ = "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"
FAKE_GEMINI = "AQ.Ab8RN6IkPJQ2Rgoh02zLPPb8bGeAFivVmf64WY3_Rce1KxssFg"
FAKE_GOOGLE_OLD = "AIzaSyD-9tSrke72PouQMnMX-a7eZSW0jkFMBWY"
FAKE_OPENAI = "sk-proj-1234567890abcdefghijklmnopqrstuvwxyz"


@pytest.fixture(autouse=True)
def _clean_registry():
    snapshot = set(_KNOWN_SECRETS)
    yield
    _KNOWN_SECRETS.clear()
    _KNOWN_SECRETS.update(snapshot)


def _record(message: str, level: int = logging.INFO) -> logging.LogRecord:
    return logging.LogRecord("test", level, __file__, 1, message, None, None)


class TestRedact:
    @pytest.mark.parametrize(
        "secret", [FAKE_GROQ, FAKE_GEMINI, FAKE_GOOGLE_OLD, FAKE_OPENAI]
    )
    def test_bat_duoc_dinh_dang_key_pho_bien(self, secret: str) -> None:
        cleaned = redact(f"Gọi API thất bại với key {secret} — HTTP 401")
        assert secret not in cleaned
        assert "..." in cleaned

    def test_giu_lai_dau_va_duoi_de_con_doi_chieu_duoc(self) -> None:
        cleaned = redact(FAKE_GROQ)
        assert cleaned.startswith("gsk_")
        assert cleaned.endswith(FAKE_GROQ[-4:])

    def test_khong_dong_cham_van_ban_binh_thuong(self) -> None:
        message = "EXTRACT xong: 23 mục, loại 0 mục thiếu bằng chứng hợp lệ"
        assert redact(message) == message

    def test_bat_duoc_nhieu_key_trong_mot_dong(self) -> None:
        cleaned = redact(f"gemini={FAKE_GEMINI} groq={FAKE_GROQ}")
        assert FAKE_GEMINI not in cleaned
        assert FAKE_GROQ not in cleaned

    def test_key_dang_ky_thu_cong_cung_bi_che(self) -> None:
        """Nhà cung cấp mới có thể dùng định dạng chưa nằm trong regex."""
        odd = "khoa-la-hoac-khong-giong-ai-1234567890"
        assert odd in redact(f"key={odd}")
        register_secret(odd)
        assert odd not in redact(f"key={odd}")

    def test_khong_dang_ky_chuoi_qua_ngan(self) -> None:
        """Che một chuỗi ngắn sẽ khớp nhầm vào văn bản bình thường."""
        register_secret("abc")
        assert "abc" in redact("abc def")

    def test_key_nam_trong_url(self) -> None:
        cleaned = redact(f"https://api.example.com/v1?key={FAKE_GOOGLE_OLD}&x=1")
        assert FAKE_GOOGLE_OLD not in cleaned


class TestFilter:
    def test_thay_the_msg_va_xoa_args(self) -> None:
        """Giữ args thì handler nội suy lại và bí mật quay về nguyên vẹn."""
        record = logging.LogRecord(
            "test", logging.INFO, __file__, 1, "key=%s", (FAKE_GROQ,), None
        )
        SecretRedactingFilter().filter(record)
        assert record.args == ()
        assert FAKE_GROQ not in record.getMessage()

    def test_cat_ngan_ban_ghi_debug_dai(self) -> None:
        record = _record("x" * 5_000, logging.DEBUG)
        SecretRedactingFilter().filter(record)
        text = record.getMessage()
        assert len(text) < 500
        assert "--log-full-content" in text

    def test_khong_cat_khi_bat_co_cho_phep(self) -> None:
        record = _record("x" * 5_000, logging.DEBUG)
        SecretRedactingFilter(allow_full_content=True).filter(record)
        assert len(record.getMessage()) == 5_000

    def test_khong_cat_ban_ghi_info_du_dai(self) -> None:
        """Chỉ DEBUG mới có khả năng chứa nội dung họp nguyên văn."""
        record = _record("y" * 5_000, logging.INFO)
        SecretRedactingFilter().filter(record)
        assert len(record.getMessage()) == 5_000

    def test_cho_phep_cat_van_che_bi_mat(self) -> None:
        record = _record(f"key={FAKE_GROQ}", logging.DEBUG)
        SecretRedactingFilter(allow_full_content=True).filter(record)
        assert FAKE_GROQ not in record.getMessage()

    def test_tham_so_dinh_dang_sai_khong_lam_sap(self) -> None:
        record = logging.LogRecord("t", logging.INFO, __file__, 1, "%d", ("x",), None)
        assert SecretRedactingFilter().filter(record) is True

    def test_luon_tra_ve_True_de_khong_nuot_ban_ghi(self) -> None:
        assert SecretRedactingFilter().filter(_record("bình thường")) is True


class TestConfigureLogging:
    def test_gan_bo_loc_vao_moi_handler(self, tmp_path: Path) -> None:
        configure_logging(log_file=tmp_path / "run.log")
        root = logging.getLogger()
        assert len(root.handlers) == 2
        for handler in root.handlers:
            assert any(isinstance(f, SecretRedactingFilter) for f in handler.filters)

    def test_ghi_ra_file_va_che_key(self, tmp_path: Path) -> None:
        log_file = tmp_path / "run.log"
        configure_logging(log_file=log_file)
        logging.getLogger("thu").info("dùng key %s", FAKE_GROQ)
        for handler in logging.getLogger().handlers:
            handler.flush()

        content = log_file.read_text(encoding="utf-8")
        assert FAKE_GROQ not in content
        assert "gsk_" in content

    def test_dang_ky_key_tu_bien_moi_truong(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        odd = "khoa-dinh-dang-la-abcdefghijklmnop"
        monkeypatch.setenv("GEMINI_API_KEY", odd)
        configure_logging(log_file=tmp_path / "run.log")
        assert odd not in redact(f"lỗi với {odd}")

    def test_ghim_thu_vien_on_ao_xuong_warning(self, tmp_path: Path) -> None:
        """httpx và bạn bè hay đưa cả URL kèm tham số truy vấn vào log."""
        configure_logging(verbose=True, log_file=tmp_path / "run.log")
        for noisy in ("httpx", "httpcore", "urllib3", "groq"):
            assert logging.getLogger(noisy).level >= logging.WARNING

    def test_go_handler_cu_khong_ghi_trung(self, tmp_path: Path) -> None:
        configure_logging(log_file=tmp_path / "a.log")
        configure_logging(log_file=tmp_path / "b.log")
        assert len(logging.getLogger().handlers) == 2

    def test_tao_thu_muc_cha_cua_file_log(self, tmp_path: Path) -> None:
        configure_logging(log_file=tmp_path / "sau" / "nua" / "run.log")
        assert (tmp_path / "sau" / "nua").is_dir()


@pytest.fixture(autouse=True)
def _restore_logging():
    yield
    root = logging.getLogger()
    for handler in list(root.handlers):
        handler.close()
        root.removeHandler(handler)
