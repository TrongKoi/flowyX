package vn.adc2026.wayfinding

import android.app.Activity
import android.content.Context
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView

/**
 * ====================================================================
 * BIEN BAN -> LICH (v5)
 * ====================================================================
 *
 * Bam "Thêm vào lịch" tren mot bien ban -> vao thang day. Ten viec DA
 * DIEN SAN, chi con chot ngay va gio.
 *
 * Vi sao mot man hinh rieng chu khong mo thang trang tao ke hoach:
 *
 *   · Mot cuoc hop thuong de lai NHIEU viec. Man hinh nay cho tich chon
 *     nhieu viec roi dat gio cho tung cai, khong phai lam lai tu dau
 *     nam lan.
 *   · Viec da vao lich duoc danh dau, nen quay lai khong bi them lan hai.
 *   · Nguoi dung thay ro viec nao con sot - dung cai ma tab Ke hoach
 *     dang giuc.
 *
 * Moi viec duoc chon se thanh mot ke hoach 30 phut, uu tien Cao, cach
 * nhau 30 phut ke tu gio bat dau - nguoi dung sua sau neu muon.
 */
class BienBanVaoLichActivity : Activity() {

    private var b: SoBienBan.BienBan? = null
    private val daChon = linkedSetOf<String>()
    private var ngay = 0L
    private var gioBatDau = 9 * 60

    private lateinit var khoi: LinearLayout

    override fun attachBaseContext(moi: Context) {
        super.attachBaseContext(GiaoDien.boc(moi))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        GiaoDien.apTheme(this)
        super.onCreate(savedInstanceState)
        setContentView(R.layout.man_con)
        khoi = findViewById(R.id.noi_dung_con)

        val luc = intent.getLongExtra(THEM_LUC, 0L)
        b = SoBienBan.doc(this).danhSach.firstOrNull { it.luc == luc }
        if (b == null) { finish(); return }

        ngay = SoLich.homNay()
        val bay = (SoLich.bayGio() - ngay * 1440).toInt()
        gioBatDau = (((bay / 60) + 1) * 60).coerceIn(7 * 60, 21 * 60)

        ThanhTieuDe.noiCon(this, getString(R.string.bb_them_vao_lich))
        findViewById<TextView>(R.id.nut_duoi_con).apply {
            visibility = View.VISIBLE
            setOnClickListener { luu() }
        }
        ve()
    }

    private fun ve() {
        val bb = b ?: return
        khoi.removeAllViews()

        // Nguon: nhac lai cuoc hop nao, de khong mat mach.
        khoi.addView(the().apply {
            background = getDrawable(R.drawable.nen_the_tim)
            addView(nhan(getString(R.string.bb_tu_cuoc_hop)).apply { setTextColor(mau(R.color.ghim)) })
            addView(chu(bb.ten, 16f, true).apply { setPadding(0, dp(4), 0, 0) })
        }, lp(4))

        // Chon viec
        khoi.addView(nhanXam(getString(R.string.bb_chon_viec)), lp(18))
        val chuaCo = bb.viec.filter { !SoBienBan.daVaoLich(this, bb.luc, it) }
        if (chuaCo.isEmpty()) {
            khoi.addView(chu(getString(R.string.bb_het_viec_moi), 14f).apply {
                setTextColor(mau(R.color.chu_phu))
            }, lp(6))
        }
        for (v in bb.viec) {
            val daCo = SoBienBan.daVaoLich(this, bb.luc, v)
            val hang = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
                background = getDrawable(R.drawable.nen_the)
                setPadding(dp(6), dp(6), dp(14), dp(6))
                isClickable = !daCo
                alpha = if (daCo) 0.55f else 1f
                setOnClickListener {
                    Rung.nhe(it)
                    if (!daChon.remove(v)) daChon.add(v)
                    ve()
                }
            }
            hang.addView(ImageView(this).apply {
                setImageResource(when {
                    daCo -> R.drawable.ic_tick
                    v in daChon -> R.drawable.ic_tick
                    else -> R.drawable.tron_viec
                })
                setColorFilter(mau(if (daCo) R.color.chu_phu else if (v in daChon) R.color.cam else R.color.chu_phu))
                val p = dp(11); setPadding(p, p, p, p)
                importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
            }, LinearLayout.LayoutParams(dp(44), dp(44)))
            hang.addView(chu(v, 14.5f).apply {
                if (daCo) paintFlags = paintFlags or android.graphics.Paint.STRIKE_THRU_TEXT_FLAG
            }, LinearLayout.LayoutParams(0, -2, 1f))
            hang.contentDescription = v + when {
                daCo -> ", " + getString(R.string.bb_da_vao_lich)
                v in daChon -> ", " + getString(R.string.kh_dang_chon)
                else -> ""
            }
            khoi.addView(hang, lp(8))
        }

        // Ngay va gio
        khoi.addView(nhanXam(getString(R.string.bb_dat_gio)), lp(18))
        val t = the()
        t.addView(hangCaiDat(R.drawable.ic_lich_nho, getString(R.string.kh_ngay),
            Lich.tenNgay(ngay, SoLich.homNay(), this)) { chonNgay() })
        t.addView(View(this).apply {
            setBackgroundColor(mau(R.color.vien))
            layoutParams = LinearLayout.LayoutParams(-1, dp(1)).apply { marginStart = dp(32) }
        })
        t.addView(hangCaiDat(R.drawable.ic_dong_ho, getString(R.string.kh_bat_dau_luc),
            Lich.gioPhut(gioBatDau)) {
            BoChonGio.hien(this, getString(R.string.gio_chon_bat_dau), gioBatDau) {
                gioBatDau = it; ve()
            }
        })
        khoi.addView(t, lp(4))
        khoi.addView(chu(getString(R.string.bb_cach_nhau), 12.5f).apply {
            setTextColor(mau(R.color.chu_phu)); setPadding(dp(4), dp(8), 0, 0)
        }, lp(0))

        findViewById<TextView>(R.id.nut_duoi_con).apply {
            text = getString(R.string.bb_luu_n, daChon.size)
            isEnabled = daChon.isNotEmpty()
            alpha = if (daChon.isEmpty()) 0.5f else 1f
        }
        GiaoDien.apFont(findViewById(android.R.id.content), this)
    }

    private fun chonNgay() {
        val (y, m, d) = Lich.ngayThang(ngay)
        android.app.DatePickerDialog(this, { _, nam, thang, ngayThang ->
            ngay = Lich.tuNgayThang(nam, thang + 1, ngayThang); ve()
        }, y, m - 1, d).apply {
            datePicker.minDate = SoLich.sangMili(SoLich.homNay() * 1440)
            datePicker.firstDayOfWeek = java.util.Calendar.MONDAY
        }.hien()
    }

    private fun luu() {
        val bb = b ?: return
        val so = SoLich.doc(this)
        var gio = gioBatDau
        for (v in daChon) {
            so.luuKeHoach(this, KeHoach(
                id = SoLich.moiId(),
                ten = v.take(90),
                emoji = "📌",
                ngay = ngay,
                batDau = gio.coerceAtMost(23 * 60 + 30),
                thoiLuong = 30,
                uuTien = UuTien.CAO,
                nhacTruoc = listOf(15, 0),
            ))
            SoBienBan.danhDauVaoLich(this, bb.luc, v)
            gio += 30
        }
        LichBao.datLai(this, so)
        Rung.xong(khoi)
        ThongBao.hien(this, getString(R.string.bb_da_them_n, daChon.size))
        khoi.postDelayed({ finish() }, 700)
    }

    // --- khuon nho dung chung ---

    private fun the() = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        background = getDrawable(R.drawable.nen_the)
        setPadding(dp(14), dp(10), dp(14), dp(12))
    }

    private fun hangCaiDat(icon: Int, nhan: String, giaTri: String, khiCham: () -> Unit) =
        LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            minimumHeight = dp(56)
            isClickable = true
            background = getDrawable(android.R.drawable.list_selector_background)
            setOnClickListener { Rung.nhe(it); khiCham() }
            addView(ImageView(this@BienBanVaoLichActivity).apply {
                setImageResource(icon)
                setColorFilter(mau(R.color.chu_phu))
                importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
            }, LinearLayout.LayoutParams(dp(20), dp(20)).apply { marginEnd = dp(12) })
            addView(chu(nhan, 15f), LinearLayout.LayoutParams(0, -2, 1f))
            addView(chu(giaTri, 15f, true).apply { setTextColor(mau(R.color.chu_lien_ket)) })
            contentDescription = "$nhan: $giaTri"
        }

    private fun chu(s: String, co: Float, dam: Boolean = false) = TextView(this).apply {
        text = s; textSize = co; includeFontPadding = false
        setTextColor(mau(R.color.chu))
        if (dam) typeface = Typeface.DEFAULT_BOLD
        setLineSpacing(0f, 1.3f)
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

    companion object {
        const val THEM_LUC = "luc"
    }
}
