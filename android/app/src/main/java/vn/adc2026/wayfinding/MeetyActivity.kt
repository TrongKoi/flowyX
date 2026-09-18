package vn.adc2026.wayfinding

import android.content.Intent
import android.net.Uri
import android.view.Gravity
import android.view.View
import android.widget.LinearLayout
import android.widget.TextView

/**
 * TAB BIEN BAN (v4) - noi voi loi Meety, xuat Word hai ban.
 *
 * Hai nut tren cung, ngang hang:
 *   - "Nhap tu Meety"  -> chon tep `_minutes.json` Meety tao ra
 *   - "Ghi tay"        -> trang ghi toan man hinh (khong co ghi am)
 *
 * Moi bien ban co nut "Xuat Word" -> chon Tieu chuan / De doc -> chon noi
 * luu. Hai ban la hai tep rieng: nguoi dung gui ban Tieu chuan cho sep va
 * giu ban De doc cho minh, hoac nguoc lai.
 *
 * Vuot phai de xoa, co Hoan tac. Khong nhan giu.
 */
class MeetyActivity : TrangCoTab() {

    private lateinit var so: SoBienBan
    private var dangXuat: SoBienBan.BienBan? = null
    private var hoSo = DocxViet.HoSo.TIEU_CHUAN

    override fun tab() = ThanhTab.MEETY

    override fun ve() {
        so = SoBienBan.doc(this)
        tieuDe(getString(R.string.bb_tieu_de))
        the(nenVang = true).addView(chuPhu(getString(R.string.bb_giai_thich_v4)))

        hang(nutPhu(getString(R.string.bb_nhap_meety)) { moTepMeety() },
             nutPhu(getString(R.string.bb_ghi_tay)) {
                 startActivity(Intent(this, GhiBienBanActivity::class.java))
             }, 12)

        them(nhan(getString(R.string.bb_cac_bien_ban), camMau = false), 20)
        if (so.danhSach.isEmpty()) khoiTrong(getString(R.string.bb_chua_co))
        else for (b in so.danhSach.reversed()) veMot(b)
    }

    private fun veMot(b: SoBienBan.BienBan) {
        val t = theRieng()
        t.addView(chuPhu(b.ngayDoc() + if (b.nguon == SoBienBan.NGUON_MEETY) "  ·  Meety" else "", 12f))
        t.addView(chuTo(b.ten, 16f).apply { setPadding(0, dp(3), 0, 0) })
        (b.tomTat.firstOrNull() ?: b.daChot.lineSequence().firstOrNull { it.isNotBlank() })?.let {
            t.addView(TextView(this).apply {
                text = it; textSize = 13f; maxLines = 3
                setTextColor(mau(R.color.chu)); setLineSpacing(0f, 1.4f)
                setPadding(0, dp(6), 0, 0)
            })
        }
        if (b.viec.isNotEmpty()) {
            t.addView(nhan(getString(R.string.bb_viec_n, b.viec.size)).apply { setPadding(0, dp(12), 0, 0) })
            for (v in b.viec.take(4)) {
                val h = LinearLayout(this).apply {
                    orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL
                    setPadding(0, dp(6), 0, 0)
                }
                h.addView(TextView(this).apply {
                    text = v; textSize = 13.5f; setTextColor(mau(R.color.chu))
                }, LinearLayout.LayoutParams(0, -2, 1f))
                h.addView(TextView(this).apply {
                    text = getString(R.string.bb_them_vao_lich)
                    textSize = 12f; includeFontPadding = false; gravity = Gravity.CENTER
                    minHeight = dp(36)
                    setTextColor(mau(R.color.chu))
                    background = getDrawable(R.drawable.chip_tinh)
                    setPadding(dp(11), 0, dp(11), 0)
                    setOnClickListener { Rung.xong(it); vaoLich(v) }
                }, LinearLayout.LayoutParams(-2, -2).apply { marginStart = dp(8) })
                t.addView(h)
            }
        }
        t.addView(nutPhu(getString(R.string.bb_xuat_word)) { hoiXuat(b) },
            LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(12) })
        vuot(t, khiXoa = { xoa(b) })
    }

    // ---------------------------------------------------------------

    private fun vaoLich(ten: String) {
        val c = java.util.Calendar.getInstance()
        val batDau = ((c.get(java.util.Calendar.HOUR_OF_DAY) + 1) * 60).coerceAtMost(23 * 60)
        val soLich = SoLich.doc(this)
        soLich.luuKeHoach(this, KeHoach(id = SoLich.moiId(), ten = ten.take(80),
            ngay = SoLich.homNay(), batDau = batDau, thoiLuong = 30, uuTien = UuTien.CAO))
        LichBao.datLai(this, soLich)
        ThongBao.hien(this, getString(R.string.bb_da_them))
    }

    private fun xoa(b: SoBienBan.BienBan) {
        val i = so.danhSach.indexOf(b)
        if (!so.xoa(i)) return
        so.luu(this); lamMoi()
        HoanTac.hien(this, getString(R.string.da_xoa_ten, b.ten)) {
            val lai = SoBienBan.doc(this); lai.chen(i, b); lai.luu(this); lamMoi()
        }
    }

    private fun hoiXuat(b: SoBienBan.BienBan) {
        val tieuDe = arrayOf(getString(R.string.docx_tieu_chuan_mo_ta), getString(R.string.docx_de_doc_mo_ta))
        android.app.AlertDialog.Builder(this)
            .setTitle(R.string.bb_chon_ban)
            .setItems(tieuDe) { _, i ->
                hoSo = if (i == 0) DocxViet.HoSo.TIEU_CHUAN else DocxViet.HoSo.DE_DOC
                dangXuat = b
                val duoi = if (hoSo == DocxViet.HoSo.DE_DOC) "-de-doc" else ""
                val ten = b.ten.lowercase().replace(Regex("[^\\p{L}\\p{N}]+"), "-").trim('-').take(40)
                try {
                    @Suppress("DEPRECATION")
                    startActivityForResult(Intent(Intent.ACTION_CREATE_DOCUMENT).apply {
                        addCategory(Intent.CATEGORY_OPENABLE); type = DocxViet.MIME
                        putExtra(Intent.EXTRA_TITLE, "bien-ban-$ten$duoi.docx")
                    }, MA_XUAT)
                } catch (_: Exception) {
                    ThongBao.hien(this, getString(R.string.khong_xuat_duoc))
                }
            }
            .setNegativeButton(R.string.huy, null)
            .hien()
    }

    private fun moTepMeety() {
        try {
            @Suppress("DEPRECATION")
            startActivityForResult(Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
                addCategory(Intent.CATEGORY_OPENABLE)
                type = "*/*"
                putExtra(Intent.EXTRA_MIME_TYPES, arrayOf("application/json", "text/plain", "application/octet-stream"))
            }, MA_NHAP)
        } catch (_: Exception) {
            ThongBao.hien(this, getString(R.string.bb_khong_mo_duoc))
        }
    }

    @Deprecated("Deprecated in Java")
    override fun onActivityResult(ma: Int, kq: Int, data: Intent?) {
        @Suppress("DEPRECATION")
        super.onActivityResult(ma, kq, data)
        if (kq != RESULT_OK) return
        val uri: Uri = data?.data ?: return
        when (ma) {
            MA_XUAT -> {
                val b = dangXuat ?: return
                try {
                    contentResolver.openOutputStream(uri)?.use {
                        it.write(DocxViet.tao(b.ten, SoBienBan.khoiDocx(b), hoSo))
                    }
                    ThongBao.hien(this, getString(R.string.da_xuat))
                    findViewById<View>(android.R.id.content)?.let { Rung.xong(it) }
                } catch (_: Exception) {
                    ThongBao.hien(this, getString(R.string.khong_xuat_duoc))
                }
            }
            MA_NHAP -> {
                val chu = try {
                    contentResolver.openInputStream(uri)?.use { s ->
                        // Tran 5 MB: bien ban that chi vai chuc KB.
                        String(s.readBytes().take(5_000_000).toByteArray(), Charsets.UTF_8)
                    }
                } catch (_: Exception) { null }
                val b = chu?.let { SoBienBan.tuMeety(it) }
                if (b == null) {
                    ThongBao.hien(this, getString(R.string.bb_khong_phai_meety))
                } else {
                    val lai = SoBienBan.doc(this)
                    lai.themBan(b); lai.luu(this)
                    ThongBao.hien(this, getString(R.string.bb_da_nhap, b.ten))
                    lamMoi()
                }
            }
        }
    }

    private companion object {
        const val MA_XUAT = 7101
        const val MA_NHAP = 7102
    }
}
