package vn.adc2026.wayfinding

import android.content.Intent
import android.graphics.Typeface
import android.net.Uri
import android.view.Gravity
import android.view.View
import android.widget.CheckBox
import android.widget.FrameLayout
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView

/**
 * TAB NHAT KY (v4).
 *
 * ================================================================
 * SUA LECH TAM - NGUYEN NHAN
 * ================================================================
 *
 * So "Chuoi ngay" va "Viec da xong": moi cot la LinearLayout doc voi
 * gravity CENTER_HORIZONTAL, nhung TextView con rong WRAP_CONTENT va co
 * font padding cua Lexend -> so lech xuong va lech ngang theo do rong chu
 * so. Sua: moi o la FrameLayout chieu cao CO DINH 88dp, so va nhan deu
 * MATCH_PARENT + gravity CENTER + includeFontPadding = false.
 *
 * Bay cham: ban cu tron lan hai loai view (ImageView co padding cho ngay
 * co lam, View tron cho ngay khong) - hai loai do do khac nhau. Sua: moi
 * cham la cung mot FrameLayout 32x32 dp dat giua mot cot weight = 1, dau
 * tick (neu co) nam GIUA FrameLayout. Nhan thu MATCH_PARENT, CENTER.
 *
 * ================================================================
 * CON LAI
 * ================================================================
 *
 * - Chuoi ngay tu tinh ca ngay chi mo app (`SoTienDo.diemDanh`).
 * - Loi nhan doi MOI NGAY, khong doi moi lan mo (`LoiNhanNgay`).
 * - Viet: trang toan man hinh (`VietNhatKyActivity`), khong phai hop thoai.
 * - Vuot phai de xoa, co Hoan tac. Cham de sua.
 * - Xuat: bam "Chon de xuat" -> o danh dau tren tung the -> "Xuat Word".
 *   Mac dinh ban DE DOC (so rieng cua chinh nguoi dung, doc de la uu tien).
 */
class NhatKyActivity : TrangCoTab() {

    private lateinit var soNhatKy: SoNhatKy
    private lateinit var soTienDo: SoTienDo

    private var dangChon = false
    private val daChon = mutableSetOf<Long>()
    private var hoSoXuat = DocxViet.HoSo.DE_DOC

    override fun tab() = ThanhTab.NHAT_KY

    override fun ve() {
        soNhatKy = SoNhatKy.doc(this)
        soTienDo = SoTienDo.doc(this)

        tieuDe(getString(R.string.tab_nhat_ky))
        veLoiNhan()
        veTomTat()
        veTuan()

        if (!dangChon) {
            them(nutChinh(getString(R.string.nk_viet_moi)) {
                startActivity(Intent(this, VietNhatKyActivity::class.java))
            }, 16)
        }
        veCacMuc()
    }

    // ---------------------------------------------------------------

    private fun veLoiNhan() {
        val t = the(nenVang = true, tren = 12)
        t.addView(nhan(getString(R.string.nk_loi_nhan_hom_nay), camMau = false))
        t.addView(chuTo(LoiNhanNgay.cua(SoLich.homNay()), 16f).apply {
            setPadding(0, dp(6), 0, 0); setLineSpacing(0f, 1.3f)
        })
    }

    private fun veTomTat() {
        val t = the(tren = 12)
        val h = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        fun o(so: String, nhanChu: String, mauSo: Int) = FrameLayout(this).apply {
            addView(LinearLayout(this@NhatKyActivity).apply {
                orientation = LinearLayout.VERTICAL
                gravity = Gravity.CENTER
                addView(TextView(this@NhatKyActivity).apply {
                    text = so; textSize = 34f; gravity = Gravity.CENTER
                    includeFontPadding = false
                    typeface = Typeface.DEFAULT_BOLD
                    setTextColor(mau(mauSo))
                }, LinearLayout.LayoutParams(-1, -2))
                addView(TextView(this@NhatKyActivity).apply {
                    text = nhanChu; textSize = 12f; gravity = Gravity.CENTER
                    includeFontPadding = false
                    setTextColor(mau(R.color.chu_phu))
                    setPadding(0, dp(6), 0, 0)
                }, LinearLayout.LayoutParams(-1, -2))
            }, FrameLayout.LayoutParams(-1, -2, Gravity.CENTER))
            contentDescription = "$nhanChu: $so"
        }
        h.addView(oChuoi(soTienDo.chuoi()))
        h.addView(View(this).apply { setBackgroundColor(mau(R.color.vien)) },
            LinearLayout.LayoutParams(dp(1), dp(56)))
        h.addView(o("${soTienDo.soViecHomNay()}", getString(R.string.nk_da_xong_hom_nay), R.color.chu),
            LinearLayout.LayoutParams(0, dp(88), 1f))
        t.addView(h)
        t.addView(chuPhu(getString(R.string.nk_chuoi_giai_thich), 12f).apply {
            gravity = Gravity.CENTER; setPadding(0, dp(4), 0, 0)
        })
    }

    /**
     * O chuoi ngay. Tu BA ngay tro len co mot ngon lua tho nhe ben canh.
     *
     * Vi sao moc ba: hai ngay chua thanh thoi quen va rat de dut; ba ngay
     * la luc nguoi dung bat dau thay "minh dang co mot chuoi" - dung luc
     * dang cong nhan. Duoi ba ngay khong co lua, va cung khong co dong chu
     * nao nhac rang chuoi con ngan.
     */
    private fun oChuoi(chuoi: Int): View {
        val ngoai = FrameLayout(this)
        val cot = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
        }
        val hang = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        hang.addView(TextView(this).apply {
            text = "$chuoi"
            textSize = 34f
            typeface = Typeface.DEFAULT_BOLD
            includeFontPadding = false
            setTextColor(mau(R.color.cam))
        })
        if (chuoi >= MOC_LUA) {
            hang.addView(TextView(this).apply {
                text = "🔥"
                textSize = 21f
                includeFontPadding = false
                importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
                // Nhip tho 1.3 giay, khong chop sang - cung nguyen tac voi phao hoa.
                startAnimation(android.view.animation.ScaleAnimation(
                    1f, 1.16f, 1f, 1.16f,
                    android.view.animation.Animation.RELATIVE_TO_SELF, 0.5f,
                    android.view.animation.Animation.RELATIVE_TO_SELF, 0.5f).apply {
                    duration = 1300
                    repeatMode = android.view.animation.Animation.REVERSE
                    repeatCount = android.view.animation.Animation.INFINITE
                })
            }, LinearLayout.LayoutParams(-2, -2).apply { marginStart = dp(5) })
        }
        // streak + task completion metrics
        cot.addView(hang.apply {
            gravity = Gravity.CENTER
        })
        cot.addView(chuPhu(getString(R.string.nk_chuoi_ngay), 12f).apply {
            gravity = Gravity.CENTER
            setPadding(0, dp(6), 0, 0)
        })
        // last 7 days widget
        ngoai.addView(cot, FrameLayout.LayoutParams(-1, -2, Gravity.CENTER))
        ngoai.contentDescription = getString(R.string.nk_chuoi_mo_ta, chuoi)
        ngoai.layoutParams = LinearLayout.LayoutParams(0, dp(88), 1f)
        return ngoai
    }

    private fun veTuan() {
        val t = the(tren = 12)
        t.addView(nhan(getString(R.string.nk_bay_ngay), camMau = false))
        val h = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(0, dp(12), 0, 0)
        }
        val cd = dp(32)
        for ((ten, coLam) in soTienDo.tuan()) {
            val cot = LinearLayout(this).apply {
                orientation = LinearLayout.VERTICAL
                gravity = Gravity.CENTER_HORIZONTAL
                contentDescription = getString(
                    if (coLam) R.string.tien_do_ngay_co_lam else R.string.tien_do_ngay_khong_lam, ten)
            }
            val cham = FrameLayout(this).apply {
                background = getDrawable(if (coLam) R.drawable.tron_cam else R.drawable.tron_ray)
                if (coLam) addView(ImageView(this@NhatKyActivity).apply {
                    setImageResource(R.drawable.ic_tick)
                    setColorFilter(mau(R.color.the))
                }, FrameLayout.LayoutParams(dp(16), dp(16), Gravity.CENTER))
            }
            cot.addView(cham, LinearLayout.LayoutParams(cd, cd).apply { gravity = Gravity.CENTER_HORIZONTAL })
            cot.addView(TextView(this).apply {
                text = ten; textSize = 11f; gravity = Gravity.CENTER
                includeFontPadding = false
                setTextColor(mau(R.color.chu_phu))
                setPadding(0, dp(6), 0, 0)
            }, LinearLayout.LayoutParams(-1, -2))
            h.addView(cot, LinearLayout.LayoutParams(0, -2, 1f))
        }
        t.addView(h)
    }

    // ---------------------------------------------------------------
    // Danh sach + chon + xuat
    // ---------------------------------------------------------------

    private fun veCacMuc() {
        val tatCa = soNhatKy.muc.reversed()

        val dau = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        dau.addView(nhan(getString(R.string.nk_cac_muc), camMau = false),
            LinearLayout.LayoutParams(0, -2, 1f))
        if (tatCa.isNotEmpty()) {
            dau.addView(TextView(this).apply {
                text = getString(if (dangChon) R.string.huy else R.string.nk_chon_de_xuat)
                textSize = 14f; includeFontPadding = false
                typeface = Typeface.DEFAULT_BOLD
                setTextColor(mau(R.color.chu_lien_ket))
                gravity = Gravity.CENTER
                minHeight = dp(44); setPadding(dp(12), 0, dp(4), 0)
                setOnClickListener {
                    Rung.nhe(it)
                    dangChon = !dangChon; daChon.clear(); lamMoi()
                }
            })
        }
        them(dau, 20)

        if (tatCa.isEmpty()) {
            khoiTrong(getString(R.string.chua_co_ghi_chu))
            return
        }

        if (dangChon) veThanhXuat(tatCa)

        for (m in tatCa.take(SO_MUC_HIEN)) {
            val t = theRieng()
            val hang = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
            }
            if (dangChon) {
                hang.addView(CheckBox(this).apply {
                    isChecked = m.luc in daChon
                    isClickable = false; isFocusable = false
                    importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
                }, LinearLayout.LayoutParams(dp(44), dp(44)))
            }
            val cot = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
            cot.addView(chuPhu(ngayGio(m.luc), 12f).apply { includeFontPadding = false })
            m.theNao?.let { tn ->
                cot.addView(TextView(this).apply {
                    text = tn; textSize = 12f; includeFontPadding = false
                    setTextColor(mau(R.color.chu))
                    background = getDrawable(R.drawable.chip_tinh)
                    setPadding(dp(10), dp(4), dp(10), dp(4))
                }, LinearLayout.LayoutParams(-2, -2).apply { topMargin = dp(6) })
            }
            if (m.tieuDe.isNotBlank()) cot.addView(TextView(this).apply {
                text = m.tieuDe
                textSize = 15.5f
                typeface = Typeface.DEFAULT_BOLD
                includeFontPadding = false
                setTextColor(mau(R.color.chu))
                maxLines = 1
                ellipsize = android.text.TextUtils.TruncateAt.END
                setPadding(0, dp(5), 0, 0)
            })
            cot.addView(TextView(this).apply {
                text = m.noiDung
                textSize = if (m.tieuDe.isBlank()) 15f else 13.5f
                setTextColor(mau(R.color.chu))
                setLineSpacing(0f, 1.4f)
                maxLines = 6; ellipsize = android.text.TextUtils.TruncateAt.END
                setPadding(0, dp(6), 0, 0)
            })
            hang.addView(cot, LinearLayout.LayoutParams(0, -2, 1f))
            t.addView(hang)
            t.isClickable = true
            t.setOnClickListener {
                if (dangChon) {
                    Rung.nhe(it)
                    if (!daChon.remove(m.luc)) daChon.add(m.luc)
                    lamMoi()
                } else {
                    startActivity(Intent(this, VietNhatKyActivity::class.java)
                        .putExtra(VietNhatKyActivity.THEM_LUC, m.luc))
                }
            }
            t.contentDescription = ngayGio(m.luc) + ". " + m.noiDung +
                if (dangChon) (if (m.luc in daChon) ". Đã chọn" else ". Chưa chọn") else ""
            if (dangChon) them(t, 8) else vuot(t, khiXoa = { xoa(m) })
        }
    }

    private fun veThanhXuat(tatCa: List<SoNhatKy.Muc>) {
        val t = the(tren = 8)
        t.addView(chuPhu(getString(R.string.nk_da_chon, daChon.size), 13f))
        val h = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; setPadding(0, dp(8), 0, 0) }
        val lp = LinearLayout.LayoutParams(0, dp(44), 1f)
        for ((i, hs) in listOf(DocxViet.HoSo.DE_DOC, DocxViet.HoSo.TIEU_CHUAN).withIndex()) {
            h.addView(TextView(this).apply {
                text = getString(if (hs == DocxViet.HoSo.DE_DOC) R.string.docx_de_doc else R.string.docx_tieu_chuan)
                textSize = 13f; gravity = Gravity.CENTER; includeFontPadding = false
                setTextColor(mau(R.color.chu))
                background = getDrawable(R.drawable.chip)
                isSelected = hs == hoSoXuat
                setOnClickListener { Rung.nhe(it); hoSoXuat = hs; lamMoi() }
            }, LinearLayout.LayoutParams(lp).apply { if (i > 0) marginStart = dp(8) })
        }
        t.addView(h)
        val hang2 = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; setPadding(0, dp(10), 0, 0) }
        hang2.addView(nutPhu(getString(if (daChon.size == tatCa.size) R.string.nk_bo_chon_het else R.string.nk_chon_het)) {
            if (daChon.size == tatCa.size) daChon.clear() else daChon.addAll(tatCa.map { it.luc })
            lamMoi()
        }, LinearLayout.LayoutParams(0, -2, 1f))
        hang2.addView(nutChinh(getString(R.string.nk_xuat_word)) {
            if (daChon.isEmpty()) {
                ThongBao.hien(this, getString(R.string.nk_chua_chon))
            } else xinChoLuu()
        }, LinearLayout.LayoutParams(0, -2, 1f).apply { marginStart = dp(8) })
        t.addView(hang2)
    }

    private fun xoa(m: SoNhatKy.Muc) {
        val chiSo = soNhatKy.muc.indexOf(m)
        if (!soNhatKy.xoa(chiSo)) return
        soNhatKy.luu(this)
        lamMoi()
        HoanTac.hien(this, getString(R.string.nk_da_xoa)) {
            val so = SoNhatKy.doc(this)
            so.chen(chiSo, m); so.luu(this); lamMoi()
        }
    }

    private fun ngayGio(luc: Long): String =
        java.text.SimpleDateFormat("EEEE, dd/MM · HH:mm", java.util.Locale("vi", "VN"))
            .format(java.util.Date(luc)).replaceFirstChar { it.uppercase() }

    // ---------------------------------------------------------------
    // Xuat .docx qua trinh chon tep cua he thong - nguoi dung chon noi luu.
    // ---------------------------------------------------------------

    private fun xinChoLuu() {
        val ngay = java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.US).format(java.util.Date())
        val duoi = if (hoSoXuat == DocxViet.HoSo.DE_DOC) "-de-doc" else ""
        val i = Intent(Intent.ACTION_CREATE_DOCUMENT).apply {
            addCategory(Intent.CATEGORY_OPENABLE)
            type = DocxViet.MIME
            putExtra(Intent.EXTRA_TITLE, "nhat-ky-flowyx-$ngay$duoi.docx")
        }
        try {
            @Suppress("DEPRECATION")
            startActivityForResult(i, MA_XUAT)
        } catch (_: Exception) {
            ThongBao.hien(this, getString(R.string.khong_xuat_duoc))
        }
    }

    @Deprecated("Deprecated in Java")
    override fun onActivityResult(ma: Int, ketQua: Int, data: Intent?) {
        @Suppress("DEPRECATION")
        super.onActivityResult(ma, ketQua, data)
        if (ma != MA_XUAT || ketQua != RESULT_OK) return
        val uri: Uri = data?.data ?: return
        try {
            val muc = SoNhatKy.doc(this).muc.filter { it.luc in daChon }.sortedBy { it.luc }
            contentResolver.openOutputStream(uri)?.use {
                it.write(DocxViet.tao(getString(R.string.nk_tieu_de_xuat), taoKhoi(muc), hoSoXuat))
            }
            ThongBao.hien(this, getString(R.string.nk_da_xuat_n, muc.size))
            findViewById<View>(android.R.id.content)?.let { Rung.xong(it) }
            dangChon = false; daChon.clear()
        } catch (_: Exception) {
            ThongBao.hien(this, getString(R.string.khong_xuat_duoc))
        }
    }

    /** Thuan, tach rieng de doc de: mot muc = ngay (muc lon) + cam xuc + noi dung. */
    private fun taoKhoi(muc: List<SoNhatKy.Muc>): List<DocxViet.Khoi> {
        val ra = mutableListOf<DocxViet.Khoi>(DocxViet.Khoi.TieuDe(getString(R.string.nk_tieu_de_xuat)))
        ra += DocxViet.Khoi.ChuNho(getString(R.string.nk_xuat_phu, muc.size))
        for (m in muc) {
            ra += DocxViet.Khoi.Muc(ngayGio(m.luc))
            m.theNao?.let { ra += DocxViet.Khoi.NoiBat(getString(R.string.nk_cam_thay), listOf(it)) }
            m.noiDung.split("\n").map { it.trim() }.filter { it.isNotEmpty() }
                .forEach { ra += DocxViet.Khoi.Doan(it) }
        }
        return ra
    }

    private companion object {
        /** So ngay lien tiep bat dau co ngon lua. */
        const val MOC_LUA = 3
        const val MA_XUAT = 7001
        const val SO_MUC_HIEN = 60
    }
}
