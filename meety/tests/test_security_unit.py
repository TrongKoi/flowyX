"""Kiểm thử đơn vị cho `server/security.py`.

Tầng này tự viết bằng thư viện chuẩn thay vì dùng argon2-cffi/pyotp, nên phải
tự chứng minh là nó đúng. Ba nhóm ở đây soi vào những chỗ mà một bản cài đặt
sai vẫn "chạy được" và vẫn qua các phép kiểm hời hợt:

  · băm mật khẩu   — muối phải ngẫu nhiên, chuỗi băm phải tự mang tham số,
                     chuỗi hỏng phải trả False chứ không được ném lỗi;
  · token phiên    — đủ entropy, băm một chiều, tất định;
  · TOTP           — đúng vector chuẩn RFC 4226, cửa sổ trôi đúng ±1 chu kỳ,
                     không nhận mã rác.

    pytest tests/test_security_unit.py -v
"""

from __future__ import annotations

import base64
import re
import time

import pytest

from server import security


# ===========================================================================
#  Băm mật khẩu
# ===========================================================================

def test_hash_format_is_self_describing():
    """Chuỗi băm phải mang theo tham số của chính nó.

    Không có điều này thì đổi tham số scrypt về sau sẽ làm hỏng toàn bộ mật
    khẩu cũ — người dùng đăng nhập không được và không ai hiểu vì sao.
    """
    h = security.hash_password("mat-khau-thu-nghiem")
    parts = h.split("$")
    assert len(parts) == 6
    algo, n, r, p, salt, digest = parts
    assert algo == "scrypt"
    assert int(n) == 2 ** 15 and int(r) == 8 and int(p) == 1
    assert len(base64.b64decode(salt)) == 16
    assert len(base64.b64decode(digest)) == 32


def test_same_password_different_hash():
    a = security.hash_password("giong-nhau")
    b = security.hash_password("giong-nhau")
    assert a != b, "thiếu muối ngẫu nhiên"
    assert a.split("$")[4] != b.split("$")[4]


def test_verify_roundtrip():
    for pw in ["a" * 8, "Mật khẩu tiếng Việt có dấu", "🔐 emoji cũng được",
               "x" * 200, "  khoảng trắng hai đầu  "]:
        h = security.hash_password(pw)
        assert security.verify_password(pw, h), f"trượt với: {pw!r}"
        assert not security.verify_password(pw + "x", h)


def test_verify_is_case_sensitive_and_whitespace_sensitive():
    h = security.hash_password("MatKhau")
    assert not security.verify_password("matkhau", h)
    assert not security.verify_password("MatKhau ", h)
    assert not security.verify_password(" MatKhau", h)


def test_empty_password_rejected_at_hash_time():
    with pytest.raises(ValueError):
        security.hash_password("")


@pytest.mark.parametrize("broken", [
    "", "khong-phai-dinh-dang", "scrypt$32768$8$1$chi-co-nam-phan",
    "argon2$1$2$3$c2FsdA==$aGFzaA==",          # thuật toán khác
    "scrypt$khong-phai-so$8$1$c2FsdA==$aGFzaA==",
    "scrypt$32768$8$1$@@@khong-phai-base64@@@$aGFzaA==",
    "$$$$$", "scrypt$32768$8$1$$",
])
def test_verify_never_raises_on_corrupt_hash(broken):
    """Chuỗi băm hỏng phải trả False, không được ném lỗi.

    Ném lỗi ở đây nghĩa là một bản ghi hỏng trong DB sẽ trả 500 thay vì 401 —
    và 500 khác 401 là một kênh rò rỉ thông tin cho người dò.
    """
    assert security.verify_password("bat-ky", broken) is False


def test_verify_rejects_wrong_password_with_valid_format():
    h = security.hash_password("dung")
    assert not security.verify_password("sai", h)


# ===========================================================================
#  Token phiên
# ===========================================================================

def test_token_entropy_and_charset():
    tokens = {security.new_token() for _ in range(200)}
    assert len(tokens) == 200, "token bị trùng — nguồn ngẫu nhiên có vấn đề"
    for t in tokens:
        assert len(t) >= 40
        assert re.fullmatch(r"[A-Za-z0-9_-]+", t), "phải an toàn cho URL và cookie"


def test_hash_token_is_deterministic_and_one_way():
    t = security.new_token()
    assert security.hash_token(t) == security.hash_token(t)
    assert security.hash_token(t) != t
    assert len(security.hash_token(t)) == 64          # SHA-256 dạng hex
    assert security.hash_token(t) != security.hash_token(t + "x")


# ===========================================================================
#  TOTP
# ===========================================================================

def test_secret_is_valid_base32():
    for _ in range(20):
        s = security.new_totp_secret()
        assert re.fullmatch(r"[A-Z2-7]+", s), "app xác thực chỉ nhận base32"
        padded = s + "=" * (-len(s) % 8)
        assert len(base64.b32decode(padded)) == 20


def test_rfc4226_reference_vectors():
    """Vector chuẩn của RFC 4226 với khoá "12345678901234567890".

    Đây là phép kiểm quan trọng nhất của cả file: nếu HOTP sai, mã sinh ra vẫn
    trông như mã 6 số hợp lệ và mọi phép kiểm tự-sinh-tự-kiểm vẫn qua — nhưng
    Google Authenticator sẽ không bao giờ khớp.
    """
    key = b"12345678901234567890"
    expected = ["755224", "287082", "359152", "969429", "338314",
                "254676", "287922", "162583", "399871", "520489"]
    for counter, want in enumerate(expected):
        assert security._hotp(key, counter) == want, f"lệch ở counter={counter}"


def test_rfc6238_time_vectors():
    """TOTP-SHA1 tại các mốc thời gian chuẩn của RFC 6238."""
    secret = base64.b32encode(b"12345678901234567890").decode().rstrip("=")
    for at, want in [(59, "287082"), (1111111109, "081804"), (1111111111, "050471")]:
        assert security.totp_now(secret, at) == want, f"lệch tại t={at}"


def test_code_is_six_digits_with_leading_zeros_kept():
    s = security.new_totp_secret()
    for offset in range(0, 3000, 30):
        code = security.totp_now(s, time.time() + offset)
        assert len(code) == 6 and code.isdigit()


def test_verify_accepts_exactly_one_step_drift():
    s = security.new_totp_secret()
    now = 1_700_000_000
    assert security.totp_verify(s, security.totp_now(s, now), now)
    assert security.totp_verify(s, security.totp_now(s, now - 30), now)
    assert security.totp_verify(s, security.totp_now(s, now + 30), now)
    # Hai chu kỳ là quá rộng: mỗi chu kỳ nới thêm là nhân đôi số mã hợp lệ.
    assert not security.totp_verify(s, security.totp_now(s, now - 60), now)
    assert not security.totp_verify(s, security.totp_now(s, now + 60), now)


def test_verify_tolerates_user_typing_habits():
    """Người dùng hay chép mã kèm khoảng trắng — chấp nhận, nhưng chỉ thế thôi."""
    s = security.new_totp_secret()
    now = 1_700_000_000
    code = security.totp_now(s, now)
    assert security.totp_verify(s, f" {code} ", now)
    assert security.totp_verify(s, f"{code[:3]} {code[3:]}", now)


@pytest.mark.parametrize("junk", ["", "12345", "1234567", "abcdef", "12345a",
                                  None, "  ", "-12345", "1.2345", "١٢٣٤٥٦"])
def test_verify_rejects_malformed_codes(junk):
    s = security.new_totp_secret()
    assert security.totp_verify(s, junk) is False


def test_verify_rejects_code_from_another_secret():
    a, b = security.new_totp_secret(), security.new_totp_secret()
    now = 1_700_000_000
    assert not security.totp_verify(a, security.totp_now(b, now), now)


def test_secret_is_case_insensitive_on_input():
    """App xác thực có thể trả khoá viết thường; vẫn phải dùng được."""
    s = security.new_totp_secret()
    now = 1_700_000_000
    assert security.totp_verify(s.lower(), security.totp_now(s, now), now)


def test_uri_is_scannable_by_authenticator_apps():
    s = security.new_totp_secret()
    uri = security.totp_uri(s, "nguoi.dung@congty.vn")
    assert uri.startswith("otpauth://totp/")
    assert f"secret={s}" in uri
    assert "issuer=Meety" in uri
    assert "digits=6" in uri and "period=30" in uri and "algorithm=SHA1" in uri
    # Ký tự @ trong email phải được mã hoá, nếu không app sẽ đọc sai nhãn.
    assert "@" not in uri.split("?")[0].split("/totp/")[1]


def test_uri_escapes_special_characters_in_issuer():
    uri = security.totp_uri(security.new_totp_secret(), "a@b.vn", issuer="Công ty & Cộng sự")
    assert " " not in uri
    assert "&issuer=" in uri
