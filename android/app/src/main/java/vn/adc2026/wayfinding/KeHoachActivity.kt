package vn.adc2026.wayfinding

import android.app.Activity
import android.app.AlertDialog
import android.app.DatePickerDialog
import android.content.Context
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.text.InputType
import android.view.Gravity
import android.view.View
import android.widget.EditText
import android.widget.HorizontalScrollView
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.NumberPicker
import android.widget.TextView

/**
 * TAO / SUA KE HOACH (v4).
 *
 * ================================================================
 * LOI CAN GIONG - NGUYEN NHAN GOC VA CACH SUA
 * ================================================================
 *
 * Icon va nhan gio o "Keo dai / Lap lai / Nhac toi" lech tam doc vai dp.
 * Nguyen nhan: Lexend co phan dem tren (ascender) cao hon phan duoi, va
 * TextView mac dinh `includeFontPadding = true` - chu bi day xuong so voi
 * tam icon. Them vao do, ban cu moi hang tu can bang padding rieng.
 *
 * Sua bang MOT khuon hang dung chung cho moi dong (`hang()`):
 *
 *   [icon 20dp] 12dp [nhan, weight 1] [gia tri, can phai]
 *   minHeight 56dp · gravity CENTER_VERTICAL · includeFontPadding = false
 *
 * Moi dong dung khuon nay thi khong dong nao lech duoc nua.
 *
 * ================================================================
 * "KHI NAO" + "KEO DAI" -> BAT DAU / KET THUC
 * ================================================================
 *
 * Ban cu: chon gio bat dau, roi chon chip 15/30/45/60/90 phut. Nguoi dung
 * nghi "hop tu 14:00 den 15:20" - phai tu tru ra 80 phut roi thay khong co
 * chip nao. Gio: hai dong Bat dau / Ket thuc, moi dong mo dong ho cua he
 * thong. Thoi luong TU TINH va hien ben duoi. Chip nhanh (+15 +30...) van
 * con, nhung la loi tat dat Ket thuc, khong phai gioi han.
 *
 * Ket thuc truoc bat dau = qua nua dem (23:00 -> 01:00), co ghi "(hom sau)".
 *
 * ================================================================
 * LAP LAI THEO THU, NHAC TUY Y
 * ================================================================
 *
 * Lap lai: Khong / Hang ngay / Theo thu (bay nut tron T2..CN, chon nhieu).
 * Nhac: chip mau san + "Tuy chinh..." (so + phut/gio/ngay, toi da 7 ngay).
 * Moc da chon hien thanh chip co dau x de bo.
 */
class KeHoachActivity : Activity() {

    private lateinit var so: SoLich
    private var cu: KeHoach? = null

    private var emoji = Lich.EMOJI[0]
    private var mau = 0
    private var ngay = 0L
    private var batDau = 9 * 60
    private var ketThuc = 9 * 60 + 30
    private var lapLai = LapLai.KHONG
    private val thuLap = sortedSetOf<Int>()
    private val nhac = java.util.TreeSet<Int>(compareByDescending { it }).apply { add(15); add(0) }
    private var uuTien = UuTien.VUA

    private lateinit var khoi: LinearLayout
    private lateinit var oTen: EditText
    private lateinit var oDau: EditText
    private lateinit var tvLoiTen: TextView
    private lateinit var tvEmoji: TextView

    private lateinit var theThoiGian: LinearLayout
    private lateinit var theLapLai: LinearLayout
    private lateinit var theNhac: LinearLayout
    private lateinit var theUuTien: LinearLayout
    private lateinit var theBieuTuong: LinearLayout

    /** Ngon ngu: xem NgonNgu.boc. Theo may thi khong tao context moi. */
    override fun attachBaseContext(moi: android.content.Context) {
        super.attachBaseContext(GiaoDien.boc(moi))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        GiaoDien.apTheme(this)
        super.onCreate(savedInstanceState)
        if (resources.configuration.smallestScreenWidthDp < 600) {
            requestedOrientation = android.content.pm.ActivityInfo.SCREEN_ORIENTATION_PORTRAIT
        }
        setContentView(R.layout.man_con)
        so = SoLich.doc(this)
        khoi = findViewById(R.id.noi_dung_con)

        cu = so.tim(intent.getStringExtra(THEM_ID))
        val homNay = SoLich.homNay()
        val k = cu
        if (k != null) {
            emoji = k.emoji; mau = k.mau; ngay = k.ngay; batDau = k.batDau
            ketThuc = (k.batDau + k.thoiLuong) % 1440; uuTien = k.uuTien
            lapLai = if (k.lapLai == LapLai.HANG_TUAN) LapLai.THEO_THU else k.lapLai
            thuLap.addAll(if (k.lapLai == LapLai.HANG_TUAN) setOf(Lich.thu(k.ngay)) else k.thuLap)
            nhac.clear(); nhac.addAll(k.nhacTruoc)
        } else {
            ngay = intent.getLongExtra(THEM_NGAY, homNay).coerceAtLeast(homNay)
            val bay = (SoLich.bayGio() - homNay * 1440).toInt()
            batDau = if (ngay == homNay) (((bay + 15) / 15 + 1) * 15).coerceAtMost(23 * 60 + 15) else 9 * 60
            ketThuc = (batDau + 30) % 1440
        }

        ThanhTieuDe.noiCon(this, getString(if (cu == null) R.string.ke_hoach_moi else R.string.sua_ke_hoach))
        if (cu != null) ThanhTieuDe.nutPhai(this, getString(R.string.xoa)) { xoaVaThoat() }
        findViewById<TextView>(R.id.nut_duoi_con).apply {
            visibility = View.VISIBLE
            text = getString(R.string.luu_ke_hoach)
            setOnClickListener { luu() }
        }

        dungForm()
        cu?.let { oTen.setText(it.ten); oDau.setText(it.oDau ?: "") }
        GiaoDien.apFont(findViewById(android.R.id.content), this)
        if (cu == null) oTen.requestFocus()
    }

    // ---------------------------------------------------------------
    // Dung form. Ten va O dau giu nguyen khi ve lai cac phan khac.
    // ---------------------------------------------------------------

    private fun dungForm() {
        val hangTen = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL
        }
        tvEmoji = TextView(this).apply {
            text = emoji; textSize = 26f; gravity = Gravity.CENTER; includeFontPadding = false
            background = getDrawable(R.drawable.nen_the)
            importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
        }
        hangTen.addView(tvEmoji, LinearLayout.LayoutParams(dp(56), dp(56)))
        oTen = EditText(this).apply {
            hint = getString(R.string.hint_ten_ke_hoach)
            textSize = 18f
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_CAP_SENTENCES
            setTextColor(mau(R.color.chu)); setHintTextColor(mau(R.color.chu_phu))
            background = getDrawable(R.drawable.o_nhap)
            setPadding(dp(14), 0, dp(14), 0)
            minHeight = dp(56)
            setOnFocusChangeListener { _, _ -> tvLoiTen.visibility = View.GONE }
        }
        hangTen.addView(oTen, LinearLayout.LayoutParams(0, dp(56), 1f).apply { marginStart = dp(10) })
        khoi.addView(hangTen, lp(4))
        tvLoiTen = TextView(this).apply {
            text = getString(R.string.thieu_ten_ke_hoach); textSize = 13f
            setTextColor(mau(R.color.chu)); visibility = View.GONE
            accessibilityLiveRegion = View.ACCESSIBILITY_LIVE_REGION_ASSERTIVE
            setPadding(dp(66), dp(6), 0, 0)
        }
        khoi.addView(tvLoiTen)

        theUuTien = the(); theThoiGian = the(); theLapLai = the(); theNhac = the(); theBieuTuong = the()
        for (t in listOf(theUuTien, theThoiGian, theLapLai, theNhac, theBieuTuong)) khoi.addView(t, lp(12))

        val theDau = the()
        theDau.addView(hang(R.drawable.ic_ghim, getString(R.string.kh_o_dau), null) {})
        oDau = EditText(this).apply {
            hint = getString(R.string.hint_o_dau); textSize = 16f
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_CAP_SENTENCES
            setTextColor(mau(R.color.chu)); setHintTextColor(mau(R.color.chu_phu))
            background = getDrawable(R.drawable.o_nhap)
            minHeight = dp(50); setPadding(dp(14), 0, dp(14), 0)
        }
        theDau.addView(oDau, lp(4))
        khoi.addView(theDau, lp(12))

        veUuTien(this); veThoiGian(); veLapLai(); veNhac(); veBieuTuong()
    }

    private fun veUuTien(ctx: Context) {
        theUuTien.removeAllViews()
        theUuTien.addView(hang(R.drawable.ic_co, getString(R.string.kh_uu_tien), null) {})
        val h = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        for ((i, u) in UuTien.values().withIndex()) {
            h.addView(chip(ctx.getString(u.resID), u == uuTien, cham = mauUuTien(u)) { uuTien = u; veUuTien(this) },
                LinearLayout.LayoutParams(0, dp(44), 1f).apply { if (i > 0) marginStart = dp(8) })
        }
        theUuTien.addView(h, lp(4))
        GiaoDien.apFont(theUuTien, this)
    }

    private fun veThoiGian() {
        theThoiGian.removeAllViews()
        val homNay = SoLich.homNay()
        theThoiGian.addView(hang(R.drawable.ic_lich_nho, getString(R.string.kh_ngay), Lich.tenNgay(ngay, homNay, this)) { chonNgay() })
        theThoiGian.addView(vach())
        theThoiGian.addView(hang(R.drawable.ic_dong_ho, getString(R.string.kh_bat_dau_luc), Lich.gioPhut(batDau)) {
            chonGio(batDau, R.string.gio_chon_bat_dau) { g ->
                // Doi bat dau thi GIU thoi luong: ket thuc di theo.
                val tl = Lich.thoiLuongGiua(batDau, ketThuc)
                batDau = g; ketThuc = (g + tl) % 1440; veThoiGian()
            }
        })
        theThoiGian.addView(vach())
        val quaDem = ketThuc <= batDau
        theThoiGian.addView(hang(R.drawable.ic_dong_ho, getString(R.string.kh_ket_thuc_luc_nhan),
            Lich.gioPhut(ketThuc) + if (quaDem) getString(R.string.kh_hom_sau) else "") {
            chonGio(ketThuc, R.string.gio_chon_ket_thuc) { g -> ketThuc = g; veThoiGian() }
        })

        val tl = Lich.thoiLuongGiua(batDau, ketThuc)
        theThoiGian.addView(TextView(this).apply {
            text = getString(R.string.kh_keo_dai_la, Lich.moTaPhut(tl, this@KeHoachActivity))
            textSize = 13f; setTextColor(mau(R.color.chu_phu)); includeFontPadding = false
            setPadding(dp(32), dp(8), 0, dp(8))
        })
        val cuon = HorizontalScrollView(this).apply { isHorizontalScrollBarEnabled = false }
        val h = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        for (p in Lich.MUC_THOI_LUONG) {
            h.addView(chip("+${Lich.moTaPhut(p, this@KeHoachActivity)}", tl == p) {
                ketThuc = (batDau + p) % 1440; veThoiGian()
            }, LinearLayout.LayoutParams(-2, dp(40)).apply { marginEnd = dp(8) })
        }
        cuon.addView(h)
        theThoiGian.addView(cuon, lp(0))
        GiaoDien.apFont(theThoiGian, this)
    }

    private fun veLapLai() {
        theLapLai.removeAllViews()
        theLapLai.addView(hang(R.drawable.ic_lap_lai, getString(R.string.kh_lap_lai), null) {})
        val h = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        for ((i, l) in listOf(LapLai.KHONG, LapLai.HANG_NGAY, LapLai.THEO_THU).withIndex()) {
            h.addView(chip(baseContext.getString(Lich.moTaLapLai(l)), l == lapLai) {
                lapLai = l
                if (l == LapLai.THEO_THU && thuLap.isEmpty()) thuLap.add(Lich.thu(ngay))
                veLapLai()
            }, LinearLayout.LayoutParams(0, dp(44), 1f).apply { if (i > 0) marginStart = dp(8) })
        }
        theLapLai.addView(h, lp(4))

        if (lapLai == LapLai.THEO_THU) {
            val hangThu = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER }
            for (t in 0..6) {
                val chon = t in thuLap
                hangThu.addView(TextView(this).apply {
                    text = context.getString(Lich.TEN_THU_NGAN[t])
                    textSize = 13f; gravity = Gravity.CENTER; includeFontPadding = false
                    typeface = if (chon) Typeface.DEFAULT_BOLD else Typeface.DEFAULT
                    setTextColor(mau(if (chon) R.color.chu_tren_nhan else R.color.chu))
                    background = GradientDrawable().apply {
                        shape = GradientDrawable.OVAL
                        setColor(mau(if (chon) R.color.nhan else R.color.nen))
                        setStroke(dp(1), mau(if (chon) R.color.nhan_vien else R.color.vien))
                    }
                    contentDescription = context.getString(Lich.TEN_THU[t]) + if (chon) ", đang chọn" else ""
                    setOnClickListener {
                        Rung.nhe(it)
                        // Luon con it nhat MOT thu - bo het thi "theo thu" vo nghia.
                        if (chon) { if (thuLap.size > 1) thuLap.remove(t) } else thuLap.add(t)
                        veLapLai()
                    }
                }, LinearLayout.LayoutParams(0, dp(42), 1f).apply { marginStart = dp(3); marginEnd = dp(3) })
            }
            theLapLai.addView(hangThu, lp(12))
            theLapLai.addView(TextView(this).apply {
                text = Lich.moTaLapLai(taoKeHoach("x"), this.context)
                textSize = 13f; setTextColor(mau(R.color.chu_phu)); gravity = Gravity.CENTER
                setPadding(0, dp(8), 0, 0)
            })
        }
        GiaoDien.apFont(theLapLai, this)
    }

    private fun veNhac() {
        theNhac.removeAllViews()
        theNhac.addView(hang(R.drawable.ic_chuong, getString(R.string.kh_nhac_toi),
            if (nhac.isEmpty()) getString(R.string.kh_khong_nhac) else null) {})

        if (nhac.isNotEmpty()) {
            val cuon = HorizontalScrollView(this).apply { isHorizontalScrollBarEnabled = false }
            val h = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
            for (p in nhac.toList()) {
                h.addView(chip("${Lich.moTaNhac(p, this@KeHoachActivity)}  ✕", true) { nhac.remove(p); veNhac() }.apply {
                    contentDescription = getString(R.string.kh_bo_moc_nhac, Lich.moTaNhac(p, this@KeHoachActivity))
                }, LinearLayout.LayoutParams(-2, dp(40)).apply { marginEnd = dp(8) })
            }
            cuon.addView(h)
            theNhac.addView(cuon, lp(4))
        }
        val cuon2 = HorizontalScrollView(this).apply { isHorizontalScrollBarEnabled = false }
        val h2 = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        for (p in Lich.MUC_NHAC.filter { it !in nhac }) {
            h2.addView(chip("+ ${Lich.moTaNhac(p, this@KeHoachActivity)}", false) { nhac.add(p); veNhac() },
                LinearLayout.LayoutParams(-2, dp(40)).apply { marginEnd = dp(8) })
        }
        h2.addView(chip(getString(R.string.kh_tuy_chinh), false) { nhapNhacTuyChon() },
            LinearLayout.LayoutParams(-2, dp(40)))
        cuon2.addView(h2)
        theNhac.addView(cuon2, lp(8))
        theNhac.addView(TextView(this).apply {
            text = getString(R.string.kh_nhac_giai_thich); textSize = 12f
            setTextColor(mau(R.color.chu_phu)); setPadding(0, dp(8), 0, 0)
        })
        GiaoDien.apFont(theNhac, this)
    }

    private fun veBieuTuong() {
        theBieuTuong.removeAllViews()
        theBieuTuong.addView(TextView(this).apply {
            text = getString(R.string.kh_bieu_tuong); textSize = 15f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(mau(R.color.chu)); includeFontPadding = false
            setPadding(0, dp(12), 0, dp(10))
        })
        val cuon = HorizontalScrollView(this).apply { isHorizontalScrollBarEnabled = false }
        val h = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        for (e in Lich.EMOJI) {
            h.addView(chip(e, e == emoji, co = 20f) { emoji = e; tvEmoji.text = e; veBieuTuong() }.apply {
                contentDescription = "Biểu tượng $e"
            }, LinearLayout.LayoutParams(dp(52), dp(44)).apply { marginEnd = dp(6) })
        }
        cuon.addView(h)
        theBieuTuong.addView(cuon)
        val hm = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; setPadding(0, dp(12), 0, 0) }
        val ma = intArrayOf(R.color.buoc_1, R.color.buoc_2, R.color.buoc_3, R.color.buoc_4, R.color.buoc_5)
        for (i in 0 until 5) {
            val chon = i == mau
            hm.addView(TextView(this).apply {
                text = if (chon) "✓" else ""; gravity = Gravity.CENTER; textSize = 16f
                includeFontPadding = false
                setTextColor(mau(R.color.chu))
                background = GradientDrawable().apply {
                    shape = GradientDrawable.OVAL; setColor(mau(ma[i]))
                    setStroke(dp(if (chon) 3 else 1), mau(if (chon) R.color.chu else R.color.vien))
                }
                contentDescription = getString(R.string.mau_so, i + 1) + if (chon) ", đang chọn" else ""
                setOnClickListener { Rung.nhe(it); mau = i; veBieuTuong() }
            }, LinearLayout.LayoutParams(dp(44), dp(44)).apply { marginEnd = dp(12) })
        }
        theBieuTuong.addView(hm)
        GiaoDien.apFont(theBieuTuong, this)
    }

    // ---------------------------------------------------------------
    // Khuon dung chung - day la cho sua loi can giong.
    // ---------------------------------------------------------------

    private fun hang(icon: Int, nhan: String, giaTri: String?, khiCham: () -> Unit): LinearLayout =
        LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            minimumHeight = dp(56)
            addView(ImageView(this@KeHoachActivity).apply {
                setImageResource(icon)
                setColorFilter(mau(R.color.chu_phu))
                importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
            }, LinearLayout.LayoutParams(dp(20), dp(20)).apply { marginEnd = dp(12) })
            addView(TextView(this@KeHoachActivity).apply {
                text = nhan; textSize = 15f; includeFontPadding = false
                setTextColor(mau(R.color.chu))
                if (giaTri == null) typeface = Typeface.DEFAULT_BOLD
            }, LinearLayout.LayoutParams(0, -2, 1f))
            if (giaTri != null) {
                addView(TextView(this@KeHoachActivity).apply {
                    text = giaTri; textSize = 15f; includeFontPadding = false
                    gravity = Gravity.END or Gravity.CENTER_VERTICAL
                    typeface = Typeface.DEFAULT_BOLD
                    setTextColor(mau(R.color.chu_lien_ket))
                }, LinearLayout.LayoutParams(-2, -2))
                isClickable = true
                background = getDrawable(android.R.drawable.list_selector_background)
                setOnClickListener { Rung.nhe(it); khiCham() }
                contentDescription = "$nhan: $giaTri"
            }
        }

    private fun chip(chu: String, chon: Boolean, co: Float = 14f, cham: Int? = null, khiCham: () -> Unit) =
        TextView(this).apply {
            text = chu; textSize = co; gravity = Gravity.CENTER; includeFontPadding = false
            setPadding(dp(14), 0, dp(14), 0)
            setTextColor(mau(R.color.chu))
            background = getDrawable(R.drawable.chip)
            isSelected = chon
            if (cham != null) {
                setCompoundDrawablesRelativeWithIntrinsicBounds(GradientDrawable().apply {
                    shape = GradientDrawable.OVAL; setColor(cham); setSize(dp(10), dp(10))
                }, null, null, null)
                compoundDrawablePadding = dp(8)
            }
            if (chon) contentDescription = "$chu, đang chọn"
            setOnClickListener { Rung.nhe(it); khiCham() }
        }

    private fun the() = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        background = getDrawable(R.drawable.nen_the)
        setPadding(dp(14), dp(4), dp(14), dp(12))
    }

    private fun vach() = View(this).apply {
        setBackgroundColor(mau(R.color.vien))
        layoutParams = LinearLayout.LayoutParams(-1, dp(1)).apply { marginStart = dp(32) }
    }

    private fun mauUuTien(u: UuTien) = mau(when (u) {
        UuTien.CAO -> R.color.uu_cao; UuTien.VUA -> R.color.uu_vua; UuTien.THAP -> R.color.uu_thap
    })

    // ---------------------------------------------------------------
    // Hop thoai chon
    // ---------------------------------------------------------------

    private fun chonNgay() {
        val (y, m, d) = Lich.ngayThang(ngay)
        DatePickerDialog(this, { _, nam, thang, ngayThang ->
            ngay = Lich.tuNgayThang(nam, thang + 1, ngayThang); veThoiGian()
        }, y, m - 1, d).apply {
            datePicker.minDate = SoLich.sangMili(SoLich.homNay() * 1440)
            datePicker.firstDayOfWeek = java.util.Calendar.MONDAY
        }.hien()
    }

    /** v5: trong cuon cua FlowyX, khong dung TimePickerDialog he thong. */
    private fun chonGio(phut: Int, tieuDe: Int, xong: (Int) -> Unit) {
        BoChonGio.hien(this, getString(tieuDe), phut, xong)
    }

    /** So + don vi. Toi da 7 ngay - xa hon nua thi mot loi nhac khong con giup nho. */
    private fun nhapNhacTuyChon() {
        val donVi = arrayOf(getString(R.string.dv_phut), getString(R.string.dv_gio), getString(R.string.dv_ngay))
        val heSo = intArrayOf(1, 60, 1440)
        val chonSo = NumberPicker(this).apply { minValue = 1; maxValue = 90; value = 20; wrapSelectorWheel = false }
        val chonDv = NumberPicker(this).apply {
            minValue = 0; maxValue = 2; displayedValues = donVi; wrapSelectorWheel = false
        }
        val h = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER
            setPadding(dp(24), dp(12), dp(24), 0)
            addView(chonSo)
            addView(chonDv, LinearLayout.LayoutParams(-2, -2).apply { marginStart = dp(24) })
            addView(TextView(this@KeHoachActivity).apply {
                text = getString(R.string.kh_truoc); textSize = 16f; setTextColor(mau(R.color.chu))
            }, LinearLayout.LayoutParams(-2, -2).apply { marginStart = dp(16) })
        }
        AlertDialog.Builder(this)
            .setTitle(R.string.kh_nhac_tuy_chinh_tieu_de)
            .setView(h)
            .setPositiveButton(R.string.them) { _, _ ->
                val p = (chonSo.value * heSo[chonDv.value]).coerceAtMost(Lich.NHAC_TUY_CHON_TOI_DA)
                nhac.add(p); veNhac()
            }
            .setNegativeButton(R.string.huy, null)
            .hien()
    }

    // ---------------------------------------------------------------

    private fun taoKeHoach(ten: String) = KeHoach(
        id = cu?.id ?: SoLich.moiId(),
        ten = ten, emoji = emoji, mau = mau, ngay = ngay, batDau = batDau,
        thoiLuong = Lich.thoiLuongGiua(batDau, ketThuc), lapLai = lapLai,
        nhacTruoc = nhac.toList(),
        oDau = if (::oDau.isInitialized) oDau.text.toString().trim().ifBlank { null } else null,
        thuLap = if (lapLai == LapLai.THEO_THU) thuLap.toSet() else emptySet(),
        uuTien = uuTien,
    )

    private fun luu() {
        val ten = oTen.text.toString().trim()
        if (ten.isEmpty()) {
            // Bao NGAY TAI O, man hinh khong dong.
            tvLoiTen.visibility = View.VISIBLE
            oTen.requestFocus()
            findViewById<android.widget.ScrollView>(R.id.cuon_con)?.smoothScrollTo(0, 0)
            return
        }
        so.luuKeHoach(this, taoKeHoach(ten))
        LichBao.datLai(this, so)
        findViewById<View>(android.R.id.content)?.let { Rung.xong(it) }
        finish()
    }

    private fun xoaVaThoat() {
        val k = cu ?: return
        AlertDialog.Builder(this)
            .setTitle(R.string.kh_xoa_hoi)
            .apply { if (k.lapLai != LapLai.KHONG) setMessage(R.string.kh_xoa_lap_lai) }
            .setPositiveButton(R.string.xoa) { _, _ ->
                so.xoa(this, k.id); LichBao.datLai(this, so); finish()
            }
            .setNegativeButton(R.string.huy, null)
            .hien()
    }

    private fun lp(tren: Int) = LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(tren) }
    private fun dp(n: Int) = (n * resources.displayMetrics.density).toInt()
    private fun mau(id: Int) = resources.getColor(id, theme)

    companion object {
        const val THEM_ID = "id"
        const val THEM_NGAY = "ngay"
    }
}
