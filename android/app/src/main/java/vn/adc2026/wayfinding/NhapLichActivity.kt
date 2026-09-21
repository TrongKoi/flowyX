package vn.adc2026.wayfinding

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.graphics.Typeface
import android.net.Uri
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView

/**
 * ====================================================================
 * NHAP LICH TU BEN NGOAI (v5)
 * ====================================================================
 *
 * Nhan tep `.ics` - dinh dang chung cua Google Calendar, Apple Calendar
 * va Outlook. Khong can dang nhap, khong can API, va KHONG co du lieu nao
 * roi khoi may: tep duoc doc ngay tai cho bang `DocIcs`.
 *
 * ----- Vi sao khong noi thang API Google -----
 *
 * Noi API doi hoi mot du an Google Cloud, man hinh dong y OAuth, va tu do
 * la app co token truy cap lich cua nguoi dung. Voi mot app ma diem ban
 * la "du lieu o lai trong may", do la mot doi lai rat dat cho mot tien
 * ich nhap lieu. Xuat .ics tu Google Calendar chi mat ba cham va cho ket
 * qua y het. Neu sau nay nhom muon dong bo hai chieu that su thi luc do
 * moi can API - va luc do phai co man hinh giai thich rieng.
 *
 * ----- Luong man hinh -----
 *
 *   1. Ba duong vao: Google / Apple (huong dan xuat tep) va "Mo tep .ics".
 *   2. Xem truoc: tich chon tung su kien, bo tich thi khong nhap.
 *   3. Trung gio: liet ke ro rang, ba lua chon - Giu lich cu / Giu lich
 *      moi / Giu ca hai. MAC DINH la "giu ca hai" va KHONG tu ghi de:
 *      xoa nham mot ke hoach nguoi dung tu dat la mat hut.
 *   4. Nhap.
 */
class NhapLichActivity : Activity() {

    private lateinit var khoi: LinearLayout
    private var ketQua: DocIcs.KetQua? = null
    private val boTich = hashSetOf<Int>()
    private var xuLyTrung = TRUNG_CA_HAI

    override fun attachBaseContext(moi: Context) {
        super.attachBaseContext(GiaoDien.boc(moi))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        GiaoDien.apTheme(this)
        super.onCreate(savedInstanceState)
        setContentView(R.layout.man_con)
        khoi = findViewById(R.id.noi_dung_con)
        ThanhTieuDe.noiCon(this, getString(R.string.nl_tieu_de))
        ve()
    }

    private fun ve() {
        khoi.removeAllViews()
        val kq = ketQua
        if (kq == null) veDuongVao() else veXemTruoc(kq)
        GiaoDien.apFont(findViewById(android.R.id.content), this)
    }

    // ---------------------------------------------------------------
    // 1. Ba duong vao
    // ---------------------------------------------------------------

    private fun veDuongVao() {
        khoi.addView(chu(getString(R.string.nl_mo_dau), 14f).apply {
            setTextColor(mau(R.color.chu_phu))
        }, lp(4))

        // ----- MUC 5.1: CHI HIEN DUONG CUA NEN TANG DANG CHAY -----
        //
        // Ban Android nay truoc day liet ke ca Google Calendar lan Apple
        // Calendar. Nhung huong dan Apple la "mo Lich tren iPhone, chia
        // se, xuat .ics" - mot chuoi thao tac KHONG LAM DUOC tren chinh
        // cai may dang mo man hinh nay. Nguoi dung doc xong roi moi nhan
        // ra, va do la mot vong lang phi dung luc ho dang muon xong viec.
        //
        // Ban iOS hien ca hai (`ManHinhCaiDat.swift`): tren iPhone thi ca
        // hai duong deu di duoc that.
        //
        // Duong ".ics" ben duoi van nhan tep xuat tu Apple Calendar,
        // Outlook hay bat cu dau - nen khong mat kha nang nao, chi bot
        // mot muc khong dung duoc o day.
        val t = the()
        t.addView(hang(R.drawable.ic_cau, getString(R.string.nl_google), getString(R.string.nl_cach_lay)) {
            huongDan(R.string.nl_google, R.string.nl_google_cach)
        })
        khoi.addView(t, lp(14))

        khoi.addView(nutChinh(getString(R.string.nl_mo_tep)) { moTep() }, lp(16))
        khoi.addView(chu(getString(R.string.nl_rieng_tu), 12.5f).apply {
            setTextColor(mau(R.color.chu_phu)); setLineSpacing(0f, 1.45f)
        }, lp(16))
    }

    private fun huongDan(tieuDe: Int, noi: Int) {
        android.app.AlertDialog.Builder(this)
            .setTitle(tieuDe)
            .setMessage(noi)
            .setPositiveButton(R.string.nl_mo_tep) { _, _ -> moTep() }
            .setNegativeButton(R.string.huy, null)
            .hien()
    }

    private fun moTep() {
        try {
            @Suppress("DEPRECATION")
            startActivityForResult(Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
                addCategory(Intent.CATEGORY_OPENABLE)
                type = "*/*"
                putExtra(Intent.EXTRA_MIME_TYPES, arrayOf("text/calendar", "text/plain", "application/octet-stream"))
            }, MA_TEP)
        } catch (_: Exception) {
            ThongBao.hien(this, getString(R.string.bb_khong_mo_duoc))
        }
    }

    @Deprecated("Deprecated in Java")
    override fun onActivityResult(ma: Int, kq: Int, data: Intent?) {
        @Suppress("DEPRECATION")
        super.onActivityResult(ma, kq, data)
        if (ma != MA_TEP || kq != RESULT_OK) return
        val uri: Uri = data?.data ?: return
        val chu = try {
            contentResolver.openInputStream(uri)?.use {
                // Tran 5 MB: tep .ics that hiem khi qua vai tram KB.
                String(it.readBytes().take(5_000_000).toByteArray(), Charsets.UTF_8)
            }
        } catch (_: Exception) { null }
        if (chu.isNullOrBlank()) { ThongBao.hien(this, getString(R.string.nl_khong_doc_duoc)); return }
        val r = DocIcs.doc(chu)
        if (r.suKien.isEmpty()) {
            ThongBao.hien(this, getString(R.string.nl_khong_co_su_kien))
            return
        }
        ketQua = r
        boTich.clear()
        ve()
    }

    // ---------------------------------------------------------------
    // 2. Xem truoc + trung gio
    // ---------------------------------------------------------------

    private fun veXemTruoc(kq: DocIcs.KetQua) {
        val chon = kq.suKien.filterIndexed { i, _ -> i !in boTich }
        val daCo = SoLich.doc(this).danhSach
        val trung = DocIcs.timTrung(chon, daCo)

        khoi.addView(nhanXam(getString(R.string.nl_xem_truoc, kq.suKien.size)), lp(2))
        if (kq.boQua > 0) {
            khoi.addView(chu(getString(R.string.nl_bo_qua, kq.boQua), 12.5f).apply {
                setTextColor(mau(R.color.chu_phu))
            }, lp(4))
        }

        for ((i, s) in kq.suKien.withIndex()) {
            val tich = i !in boTich
            val h = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
                background = getDrawable(R.drawable.nen_the)
                setPadding(dp(6), dp(6), dp(14), dp(6))
                isClickable = true
                setOnClickListener {
                    Rung.nhe(it)
                    if (!boTich.remove(i)) boTich.add(i)
                    ve()
                }
            }
            h.addView(ImageView(this).apply {
                setImageResource(if (tich) R.drawable.ic_tick else R.drawable.tron_viec)
                setColorFilter(mau(if (tich) R.color.cam else R.color.chu_phu))
                val p = dp(11); setPadding(p, p, p, p)
                importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
            }, LinearLayout.LayoutParams(dp(44), dp(44)))
            val cot = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
            cot.addView(chu(s.ten, 14.5f, dam = true))
            cot.addView(chu(moTa(s), 12f).apply {
                setTextColor(mau(R.color.chu_phu)); setPadding(0, dp(3), 0, 0)
            })
            h.addView(cot, LinearLayout.LayoutParams(0, -2, 1f))
            h.contentDescription = "${s.ten}, ${moTa(s)}, " +
                getString(if (tich) R.string.nl_se_nhap else R.string.nl_bo_qua_muc)
            khoi.addView(h, lp(8))
        }

        if (trung.isNotEmpty()) veTrung(trung)

        khoi.addView(nutChinh(getString(R.string.nl_nhap_n, chon.size)) { nhap(chon, trung) }
            .apply { isEnabled = chon.isNotEmpty(); alpha = if (chon.isEmpty()) 0.5f else 1f }, lp(18))
        khoi.addView(nutPhu(getString(R.string.nl_chon_tep_khac)) { ketQua = null; ve() }, lp(8))
    }

    private fun veTrung(trung: List<DocIcs.Trung>) {
        val t = the()
        t.background = getDrawable(R.drawable.nen_the_cam)
        t.addView(nhan(getString(R.string.nl_trung_gio, trung.size)))
        for (x in trung.take(4)) {
            t.addView(chu(getString(R.string.nl_trung_dong,
                x.moi.ten, Lich.gioPhut(x.moi.batDau), x.cu.ten), 13f).apply {
                setPadding(0, dp(6), 0, 0); setLineSpacing(0f, 1.35f)
            })
        }
        if (trung.size > 4) {
            t.addView(chu(getString(R.string.nl_trung_them, trung.size - 4), 12.5f).apply {
                setTextColor(mau(R.color.chu_phu)); setPadding(0, dp(4), 0, 0)
            })
        }
        val hang = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(0, dp(10), 0, 0)
        }
        for ((ma, nhanChu) in listOf(
            TRUNG_CA_HAI to R.string.nl_giu_ca_hai,
            TRUNG_GIU_CU to R.string.nl_giu_cu,
            TRUNG_GIU_MOI to R.string.nl_giu_moi)) {
            hang.addView(TextView(this).apply {
                text = getString(nhanChu)
                textSize = 12.5f
                gravity = Gravity.CENTER
                minHeight = dp(44)
                includeFontPadding = false
                setTextColor(mau(R.color.chu))
                background = getDrawable(R.drawable.chip)
                isSelected = xuLyTrung == ma
                setOnClickListener { Rung.nhe(it); xuLyTrung = ma; ve() }
            }, LinearLayout.LayoutParams(0, -2, 1f).apply { if (ma != TRUNG_CA_HAI) marginStart = dp(6) })
        }
        t.addView(hang)
        khoi.addView(t, lp(16))
    }

    private fun moTa(s: DocIcs.SuKien): String {
        val ngay = Lich.tenNgay(s.ngay, SoLich.homNay(), this)
        if (s.caNgay) return "$ngay · " + getString(R.string.nl_ca_ngay)
        val lap = if (s.lapLai == LapLai.KHONG) "" else " · " +
            Lich.moTaLapLai(DocIcs.sangKeHoach(s).lapLai)
        return "$ngay · ${Lich.gioPhut(s.batDau)}–${Lich.gioPhut((s.batDau + s.thoiLuong) % 1440)}$lap"
    }

    // ---------------------------------------------------------------
    // 3. Nhap
    // ---------------------------------------------------------------

    private fun nhap(chon: List<DocIcs.SuKien>, trung: List<DocIcs.Trung>) {
        val so = SoLich.doc(this)
        val boMoi = if (xuLyTrung == TRUNG_GIU_CU) trung.map { it.moi }.toSet() else emptySet()
        if (xuLyTrung == TRUNG_GIU_MOI) {
            for (x in trung.distinctBy { it.cu.id }) so.xoa(this, x.cu.id)
        }
        var n = 0
        for (s in chon) {
            if (s in boMoi) continue
            so.luuKeHoach(this, DocIcs.sangKeHoach(s))
            n++
        }
        LichBao.datLai(this, so)
        Rung.xong(khoi)
        ThongBao.hien(this, getString(R.string.nl_da_nhap_n, n))
        khoi.postDelayed({ finish() }, 800)
    }

    // --- khuon nho ---

    private fun the() = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        background = getDrawable(R.drawable.nen_the)
        setPadding(dp(14), dp(10), dp(14), dp(12))
    }

    private fun vach() = View(this).apply {
        setBackgroundColor(mau(R.color.vien))
        layoutParams = LinearLayout.LayoutParams(-1, dp(1)).apply { marginStart = dp(32) }
    }

    private fun hang(icon: Int, nhanChu: String, giaTri: String, khiCham: () -> Unit) =
        LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            minimumHeight = dp(56)
            isClickable = true
            background = getDrawable(android.R.drawable.list_selector_background)
            setOnClickListener { Rung.nhe(it); khiCham() }
            addView(ImageView(this@NhapLichActivity).apply {
                setImageResource(icon)
                setColorFilter(mau(R.color.chu_phu))
                importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
            }, LinearLayout.LayoutParams(dp(20), dp(20)).apply { marginEnd = dp(12) })
            addView(chu(nhanChu, 15f), LinearLayout.LayoutParams(0, -2, 1f))
            addView(chu(giaTri, 14f).apply { setTextColor(mau(R.color.chu_lien_ket)) })
            contentDescription = "$nhanChu: $giaTri"
        }

    private fun nutChinh(s: String, khi: () -> Unit) = TextView(this).apply {
        text = s; textSize = 16f; gravity = Gravity.CENTER
        typeface = Typeface.DEFAULT_BOLD
        minHeight = dp(50); includeFontPadding = false
        setTextColor(mau(R.color.chu_tren_nhan))
        background = getDrawable(R.drawable.nut_chinh)
        setOnClickListener { Rung.nhe(it); khi() }
    }

    private fun nutPhu(s: String, khi: () -> Unit) = TextView(this).apply {
        text = s; textSize = 14.5f; gravity = Gravity.CENTER
        minHeight = dp(46); includeFontPadding = false
        setTextColor(mau(R.color.chu))
        background = getDrawable(R.drawable.nut_phu)
        setOnClickListener { Rung.nhe(it); khi() }
    }

    private fun chu(s: String, co: Float, dam: Boolean = false) = TextView(this).apply {
        text = s; textSize = co; includeFontPadding = false
        setTextColor(mau(R.color.chu))
        if (dam) typeface = Typeface.DEFAULT_BOLD
    }

    private fun nhan(s: String) = TextView(this).apply {
        text = s; textSize = 11.5f; typeface = Typeface.DEFAULT_BOLD
        letterSpacing = 0.04f
        setTextColor(mau(R.color.cam))
    }

    private fun nhanXam(s: String) = nhan(s).apply { setTextColor(mau(R.color.chu_phu)) }

    private fun lp(tren: Int) = LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(tren) }
    private fun dp(n: Int) = (n * resources.displayMetrics.density).toInt()
    private fun mau(id: Int) = resources.getColor(id, theme)

    private companion object {
        const val MA_TEP = 9101
        const val TRUNG_CA_HAI = 0
        const val TRUNG_GIU_CU = 1
        const val TRUNG_GIU_MOI = 2
    }
}
