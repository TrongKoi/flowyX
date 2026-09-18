"""Test cho bộ nạp ``.env``.

Module này nằm trên đường đi của **bí mật**, nên nó được kiểm kỹ hơn mức
kích thước của nó gợi ý. Ba nhóm rủi ro:

* nạp sai giá trị -> API trả 401 với thông báo không liên quan tới nguyên nhân
* ghi đè biến môi trường có sẵn -> phá CI và container
* in bí mật ra log -> lộ key qua file log hoặc screenshot
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from core.env import (
    SECRET_KEYS,
    WINDOWS_HARDEN_COMMAND,
    _parse_value,
    _windows_inheritance_present,
    check_permissions,
    load_dotenv,
    mask_secret,
)

FAKE_GEMINI = "AQ.KeyGiaDeTest_KhongPhaiKeyThat_1234567890"
FAKE_GROQ = "gsk_KeyGiaDeTest_KhongPhaiKeyThat_0987654321"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch):
    """Mỗi test chạy trên môi trường sạch, không rò rỉ sang test khác."""
    for name in ("GEMINI_API_KEY", "GROQ_API_KEY", "GHI_CHU", "BIEN_KHAC"):
        monkeypatch.delenv(name, raising=False)


def _write(tmp_path: Path, content: str) -> Path:
    path = tmp_path / ".env"
    path.write_text(content, encoding="utf-8")
    return path


class TestParseValue:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("gsk_abc123", "gsk_abc123"),
            ('"gsk_abc123"', "gsk_abc123"),
            ("'gsk_abc123'", "gsk_abc123"),
            ("  gsk_abc123  ", "gsk_abc123"),
            ("gsk_abc123 # chú thích", "gsk_abc123"),
            ('"gsk_abc123"   # chú thích', "gsk_abc123"),
            ("'gsk_abc123' # chú thích", "gsk_abc123"),
            ("", ""),
        ],
    )
    def test_cac_dang_gia_tri(self, raw: str, expected: str) -> None:
        assert _parse_value(raw) == expected

    def test_bi_mat_chua_dau_thang_van_giu_nguyen_khi_co_ngoac(self) -> None:
        """Khoá thật có thể chứa ``#``. Trong ngoặc thì phải giữ nguyên."""
        assert _parse_value('"abc #def #ghi"') == "abc #def #ghi"

    def test_ngoac_mo_ma_khong_dong(self) -> None:
        assert _parse_value('"gsk_thieu_ngoac_dong') == "gsk_thieu_ngoac_dong"

    def test_gia_tri_chua_dau_bang(self) -> None:
        """Key base64 hay có ``=`` ở cuối — không được cắt mất."""
        assert _parse_value("abc123==") == "abc123=="


class TestLoadDotenv:
    def test_nap_duoc_khoa_co_ban(self, tmp_path: Path) -> None:
        path = _write(tmp_path, f"GEMINI_API_KEY={FAKE_GEMINI}\nGROQ_API_KEY={FAKE_GROQ}\n")
        loaded = load_dotenv(path)
        assert loaded == {"GEMINI_API_KEY": FAKE_GEMINI, "GROQ_API_KEY": FAKE_GROQ}
        assert os.environ["GEMINI_API_KEY"] == FAKE_GEMINI

    def test_bien_moi_truong_co_san_luon_thang(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Quy ước chuẩn: CI và container tiêm bí mật mà không cần sửa file."""
        monkeypatch.setenv("GEMINI_API_KEY", "key-tu-CI")
        path = _write(tmp_path, f"GEMINI_API_KEY={FAKE_GEMINI}\n")
        loaded = load_dotenv(path)
        assert loaded == {}
        assert os.environ["GEMINI_API_KEY"] == "key-tu-CI"

    def test_override_cho_phep_ghi_de(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GEMINI_API_KEY", "key-cu")
        path = _write(tmp_path, f"GEMINI_API_KEY={FAKE_GEMINI}\n")
        load_dotenv(path, override=True)
        assert os.environ["GEMINI_API_KEY"] == FAKE_GEMINI

    def test_khong_co_file_thi_khong_bao_loi(self, tmp_path: Path) -> None:
        """Đường ``--mock`` không cần key nào — bắt buộc có .env sẽ phá nó."""
        assert load_dotenv(tmp_path / "khong-ton-tai.env") == {}

    def test_bo_qua_chu_thich_va_dong_trong(self, tmp_path: Path) -> None:
        path = _write(
            tmp_path,
            f"# đây là chú thích\n\n   \nGROQ_API_KEY={FAKE_GROQ}\n# cuối file\n",
        )
        assert load_dotenv(path) == {"GROQ_API_KEY": FAKE_GROQ}

    def test_bo_tien_to_export(self, tmp_path: Path) -> None:
        """Người dùng hay chép .env kiểu Linux có ``export`` ở đầu."""
        path = _write(tmp_path, f"export GROQ_API_KEY={FAKE_GROQ}\n")
        assert load_dotenv(path) == {"GROQ_API_KEY": FAKE_GROQ}

    def test_dong_thieu_dau_bang_bi_bo_qua_khong_lam_hong(self, tmp_path: Path) -> None:
        path = _write(tmp_path, f"DONG_HONG\nGROQ_API_KEY={FAKE_GROQ}\n")
        assert load_dotenv(path) == {"GROQ_API_KEY": FAKE_GROQ}

    def test_gia_tri_rong_bi_bo_qua(self, tmp_path: Path) -> None:
        """.env.example có ``GEMINI_API_KEY=`` rỗng — không được nạp chuỗi rỗng.

        Nạp chuỗi rỗng còn tệ hơn không nạp: ``os.environ.get`` trả về ``""``
        thay vì ``None``, nên nhánh kiểm tra "chưa có key" không kích hoạt và
        lỗi dời xuống tận lúc gọi API.
        """
        path = _write(tmp_path, f"GEMINI_API_KEY=\nGROQ_API_KEY={FAKE_GROQ}\n")
        loaded = load_dotenv(path)
        assert "GEMINI_API_KEY" not in loaded
        assert os.environ.get("GEMINI_API_KEY") is None

    def test_doc_duoc_file_co_BOM(self, tmp_path: Path) -> None:
        """Notepad trên Windows ghi BOM — không được coi nó là phần của tên biến."""
        path = tmp_path / ".env"
        path.write_text(f"GROQ_API_KEY={FAKE_GROQ}\n", encoding="utf-8-sig")
        assert load_dotenv(path) == {"GROQ_API_KEY": FAKE_GROQ}

    def test_ngoac_kep_quanh_key(self, tmp_path: Path) -> None:
        path = _write(tmp_path, f'GROQ_API_KEY="{FAKE_GROQ}"\n')
        assert os.environ.get("GROQ_API_KEY") is None
        load_dotenv(path)
        assert os.environ["GROQ_API_KEY"] == FAKE_GROQ

    def test_ngoac_kep_va_chu_thich_cung_luc(self, tmp_path: Path) -> None:
        """Ca đã từng làm hỏng bản đầu: bỏ ngoặc trước rồi cắt chú thích."""
        path = _write(tmp_path, f'GROQ_API_KEY="{FAKE_GROQ}"   # key của tôi\n')
        load_dotenv(path)
        assert os.environ["GROQ_API_KEY"] == FAKE_GROQ


class TestMaskSecret:
    def test_che_phan_giua(self) -> None:
        masked = mask_secret(FAKE_GROQ)
        assert FAKE_GROQ not in masked
        assert masked.startswith("gsk_")
        assert masked.endswith(f"({len(FAKE_GROQ)} ký tự)")

    def test_khong_lo_gi_voi_chuoi_ngan(self) -> None:
        assert "abc" not in mask_secret("abc")

    def test_chuoi_rong(self) -> None:
        assert mask_secret("") == "(rỗng)"

    def test_du_de_doi_chieu_nhung_khong_du_de_dung_lai(self) -> None:
        masked = mask_secret(FAKE_GEMINI)
        visible = masked.split(" ")[0].replace("...", "")
        assert len(visible) == 8


class TestCheckPermissions:
    def test_khong_co_file_thi_khong_canh_bao(self, tmp_path: Path) -> None:
        assert check_permissions(tmp_path / "khong-ton-tai") == []

    @pytest.mark.skipif(os.name == "nt", reason="Windows dùng ACL, không dùng bit quyền")
    def test_canh_bao_khi_file_de_long_quyen(self, tmp_path: Path) -> None:
        path = _write(tmp_path, f"GROQ_API_KEY={FAKE_GROQ}\n")
        path.chmod(0o644)
        assert check_permissions(path)

    @pytest.mark.skipif(os.name == "nt", reason="Windows dùng ACL, không dùng bit quyền")
    def test_khong_canh_bao_khi_quyen_da_chat(self, tmp_path: Path) -> None:
        path = _write(tmp_path, f"GROQ_API_KEY={FAKE_GROQ}\n")
        path.chmod(0o600)
        assert check_permissions(path) == []


class TestWindowsHardenCommand:
    """Lệnh icacls đưa cho người dùng phải chạy được, không phải trông có lý.

    Bản đầu tiên viết ``"$env:USERNAME:(R,W)"`` và **thất bại thật** trên máy
    người dùng với ``Invalid parameter "(R,W)"``. Nhóm test này khoá lại cả
    hai nguyên nhân.
    """

    def test_bien_username_duoc_boc_de_khong_nuot_dau_hai_cham(self) -> None:
        """PowerShell cho phép dấu hai chấm trong tên biến.

        ``"$env:USERNAME:(M)"`` khiến bộ phân tích đi tìm biến ``env:USERNAME:``
        — không tồn tại, nở ra chuỗi rỗng, icacls chỉ nhận được ``(M)``.
        """
        assert "$($env:USERNAME)" in WINDOWS_HARDEN_COMMAND
        assert "$env:USERNAME:" not in WINDOWS_HARDEN_COMMAND

    def test_dung_quyen_modify_chu_khong_phai_read_write(self) -> None:
        """``W`` không bao gồm xoá, nên trình soạn thảo lưu nguyên tử sẽ hỏng."""
        assert ":(M)" in WINDOWS_HARDEN_COMMAND
        assert "(R,W)" not in WINDOWS_HARDEN_COMMAND

    def test_duong_dan_duoc_chen_vao_va_boc_ngoac(self) -> None:
        rendered = WINDOWS_HARDEN_COMMAND.format(path="D:/Meeting Minutes AI/.env")
        assert '"D:/Meeting Minutes AI/.env"' in rendered

    def test_khong_canh_bao_khi_da_go_thua_ke(self, tmp_path, monkeypatch) -> None:
        """Người đã khoá file rồi thì không bị nhắc lại ở mỗi lần chạy."""
        path = _write(tmp_path, f"GROQ_API_KEY={FAKE_GROQ}\n")
        monkeypatch.setattr("core.env.sys.platform", "win32")
        monkeypatch.setattr("core.env._windows_inheritance_present", lambda p: False)
        assert check_permissions(path) == []

    def test_canh_bao_khi_con_thua_ke(self, tmp_path, monkeypatch) -> None:
        path = _write(tmp_path, f"GROQ_API_KEY={FAKE_GROQ}\n")
        monkeypatch.setattr("core.env.sys.platform", "win32")
        monkeypatch.setattr("core.env._windows_inheritance_present", lambda p: True)
        warnings = check_permissions(path)
        assert len(warnings) == 1
        assert "$($env:USERNAME)" in warnings[0]

    def test_canh_bao_khi_khong_ket_luan_duoc(self, tmp_path, monkeypatch) -> None:
        """Thiếu icacls thì vẫn nhắc, nhưng nói rõ là chưa kiểm tra được."""
        path = _write(tmp_path, f"GROQ_API_KEY={FAKE_GROQ}\n")
        monkeypatch.setattr("core.env.sys.platform", "win32")
        monkeypatch.setattr("core.env._windows_inheritance_present", lambda p: None)
        warnings = check_permissions(path)
        assert "Không kiểm tra được" in warnings[0]

    def test_do_co_I_trong_ket_qua_icacls_khong_phu_thuoc_ngon_ngu(
        self, tmp_path, monkeypatch
    ) -> None:
        """Tên nhóm bị dịch theo ngôn ngữ Windows, cờ ``(I)`` thì không."""
        import subprocess

        localised = (
            ".env NT AUTHORITY\\SYSTEM:(I)(F)\n"
            "     BUILTIN\\Qu\u1ea3n tr\u1ecb vi\u00ean:(I)(F)\n"
        )

        class _Result:
            returncode = 0
            stdout = localised

        monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Result())
        assert _windows_inheritance_present(tmp_path / "x") is True

    def test_khong_co_I_nghia_la_da_go_thua_ke(self, tmp_path, monkeypatch) -> None:
        import subprocess

        class _Result:
            returncode = 0
            stdout = ".env NC:(M)\n\nSuccessfully processed 1 files.\n"

        monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Result())
        assert _windows_inheritance_present(tmp_path / "x") is False

    def test_icacls_loi_thi_tra_ve_None(self, tmp_path, monkeypatch) -> None:
        import subprocess

        def _raise(*args, **kwargs):
            raise OSError("icacls không tồn tại")

        monkeypatch.setattr(subprocess, "run", _raise)
        assert _windows_inheritance_present(tmp_path / "x") is None


def test_danh_sach_bi_mat_bao_gom_ca_hai_key_cua_du_an() -> None:
    assert {"GEMINI_API_KEY", "GROQ_API_KEY"} <= SECRET_KEYS
