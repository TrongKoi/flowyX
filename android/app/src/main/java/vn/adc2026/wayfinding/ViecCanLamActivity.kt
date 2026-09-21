package vn.adc2026.wayfinding

import android.content.Context
import android.content.Intent
import android.graphics.Paint
import android.graphics.drawable.GradientDrawable
import android.view.Gravity
import android.view.View
import android.widget.FrameLayout
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import java.util.Calendar

/**
 * TAB KE HOACH (v4) - man hinh mo dau cua app.
 *
 * ================================================================
 * GOP "LOI NHAC" VAO DAY
 * ================================================================
 *
 * Ban v3 co ca "Ke hoach" lan "Loi nhac": hai danh sach cung tra loi "hom
 * nay can nho gi", nguoi dung phai nho mo CA HAI. Mot loi nhac chi la mot
 * ke hoach ngan co chuong - nen gio chi con ke hoach. Loi nhac cu tu doi
 * sang ke hoach mot lan (`ChuyenLoiNhac`).
 *
 * ================================================================
 * THU TU TREN MAN HINH - TOM TAT TRUOC, NUT SAU
 * ================================================================
 *
 *   1. Tom tat hom nay: bao nhieu viec, tong bao lau, con bao nhieu
 *      + ba o dem Cao / Vua / Thap
 *   2. "Tiep theo" - mot viec noi bat, nut Bat dau ngay trong the
 *   3. Cac viec hom nay, NHOM THEO UU TIEN (cao truoc)
 *   4. Nut: + Them ke hoach  ·  Xem lich tuan
 *
 * Mat doc tu tren xuong gap "hom nay nang hay nhe" TRUOC khi gap bat ky
 * nut nao - biet tai truoc roi moi quyet dinh lam gi.
 *
 * ================================================================
 * THAO TAC TREN THE
 * ================================================================
 *
 *   cham o tron ben trai   -> danh dau xong / bo danh dau (mot cham)
 *   vuot TRAI              -> danh dau xong
 *   vuot PHAI              -> xoa (co Hoan tac 5 giay)
 *   cham than the          -> sua
 *
 * Khong con nhan giu o bat ky dau.
 */
class ViecCanLamActivity : TrangCoTab() {

    private lateinit var soLich: SoLich

    override fun tab() = ThanhTab.VIEC

    override fun ve() {
        soLich = SoLich.doc(this)
        val c = Calendar.getInstance()
        val homNay = SoLich.homNay()
        val ds = Lich.trongNgay(soLich.danhSach, homNay)
        val phutBayGio = c.get(Calendar.HOUR_OF_DAY) * 60 + c.get(Calendar.MINUTE)

        tieuDe(getString(R.string.kh_hom_nay), ngayDoc(c))
        veVienThuoc()
        veTheBienBan()
        veTomTat(ds, homNay, phutBayGio)
        veTiepTheo(ds, homNay, phutBayGio)
        veNhom(ds, homNay, this)

        them(nutChinh(getString(R.string.them_ke_hoach)) {
            startActivity(Intent(this, KeHoachActivity::class.java)
                .putExtra(KeHoachActivity.THEM_NGAY, homNay))
        }, 18)
        them(nutPhu(getString(R.string.kh_xem_lich)) {
            ThanhTab.mo(this, LichActivity::class.java)
        })
        them(chuPhu(getString(R.string.kh_meo_vuot), 12f).apply {
            gravity = Gravity.CENTER; setPadding(0, dp(10), 0, 0)
        })
        batVungTha()
    }

    // ---------------------------------------------------------------
    // 1. Vien thuoc: phien Focus dang chay ngam
    // ---------------------------------------------------------------

    /**
     * Thanh vien thuoc mong, KHONG phai dong ho tron to.
     *
     * Mot dong ho tron o tab Ke hoach se chiem mot phan ba man hinh va
     * canh tranh voi chinh danh sach viec. O day chi can tra loi hai cau:
     * con bao lau, va dang lam viec gi - mot thanh tien do lam duoc ca hai
     * trong 44dp chieu cao. Cham vao la sang thang tab Tap trung.
     */
    private fun veVienThuoc() {
        val tt = TrangThaiFocus.doc(this)
        val bay = System.currentTimeMillis()
        if (!tt.dem.dangChay && !tt.dem.dangDung) {
            vienThuoc = null; tvVienThuoc = null; thanhVienThuoc = null
            tayVienThuoc.removeCallbacks(nhipVienThuoc)
            return
        }

        val con = tt.dem.conLaiMs(bay)
        val phut = DemNguoc.soPhutHien(con)
        val v = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            minimumHeight = dp(44)
            background = getDrawable(R.drawable.nen_vien_thuoc)
            setPadding(dp(12), dp(8), dp(16), dp(8))
            isClickable = true
            setOnClickListener {
                Rung.nhe(it)
                ThanhTab.mo(this@ViecCanLamActivity, FocusActivity::class.java)
            }
        }
        v.addView(ImageView(this).apply {
            setImageResource(R.drawable.ic_focus)
            setColorFilter(mau(if (tt.dem.dangDung) R.color.chu_phu else R.color.cam))
            importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
        }, LinearLayout.LayoutParams(dp(18), dp(18)).apply { marginEnd = dp(8) })
        val tvPhut = chuTo(
            if (phut == 0) getString(R.string.focus_sap_xong) else getString(R.string.gr_phut, phut), 14f)
            .apply { includeFontPadding = false }
        v.addView(tvPhut, LinearLayout.LayoutParams(-2, -2))

        // Thanh tien do: phan CON LAI thu nho dan, cung huong voi vong dong ho.
        val thanh = View(this).apply {
            background = GradientDrawable().apply {
                cornerRadius = dp(4).toFloat(); setColor(mau(R.color.dh_ranh))
            }
        }
        val phanCon = FrameLayout(this).apply {
            addView(thanh, FrameLayout.LayoutParams(-1, dp(7)))
            addView(View(this@ViecCanLamActivity).apply {
                background = GradientDrawable().apply {
                    cornerRadius = dp(4).toFloat()
                    setColor(mau(if (tt.dem.dangDung) R.color.chu_phu
                                 else if (phut > 10) R.color.dh_sap_den else R.color.dh_di_ngay))
                }
            }, FrameLayout.LayoutParams(0, dp(7)).also { lp ->
                // Ty le do bang weight: dat sau khi do duoc be ngang that.
                post {
                    val rong = (width * tt.dem.tyLe(System.currentTimeMillis())).toInt()
                    getChildAt(1).layoutParams = FrameLayout.LayoutParams(rong.coerceAtLeast(dp(6)), dp(7))
                    requestLayout()
                }
            })
        }
        v.addView(phanCon, LinearLayout.LayoutParams(0, dp(7), 1f).apply {
            marginStart = dp(10); marginEnd = dp(10)
        })
        tt.ten?.let {
            v.addView(chuPhu(it, 12f).apply {
                maxLines = 1
                ellipsize = android.text.TextUtils.TruncateAt.END
                maxWidth = dp(92)
            })
        }
        v.contentDescription = getString(R.string.kh_dang_chay_mo_ta, phut, tt.ten ?: "")
        vienThuoc = v
        tvVienThuoc = tvPhut
        thanhVienThuoc = phanCon
        them(v, 12)
        batNhipVienThuoc()
    }

    /**
     * ================================================================
     * VIEN THUOC PHAI CHAY THAT (muc 4.2)
     * ================================================================
     *
     * `veVienThuoc()` chi duoc goi tu `ve()`, tuc la mot lan moi khi mo
     * tab. Ngoi lai tab Ke hoach hai muoi phut thi vien thuoc van ghi y
     * nguyen con so luc vua vao, va thanh tien do dung im.
     *
     * Do la loi te nhat mot dong ho co the mac voi nguoi mu thoi gian:
     * no KHONG sai han - no chi lac hau - nen khong co gi bao cho biet
     * dung tin no. Nguoi dung lay so do lam moc, roi tre.
     *
     * Nhip 10 giay la du: vien thuoc chi hien SO PHUT, nen cap nhat day
     * hon khong doi gi tren man hinh, ma lai ton pin. Chay khi tab dang
     * mo va dung ngay khi tab bi che.
     */
    private var vienThuoc: View? = null
    private var tvVienThuoc: TextView? = null
    private var thanhVienThuoc: FrameLayout? = null
    private val tayVienThuoc = android.os.Handler(android.os.Looper.getMainLooper())

    private val nhipVienThuoc = object : Runnable {
        override fun run() {
            capNhatVienThuoc()
            tayVienThuoc.postDelayed(this, 10_000)
        }
    }

    private fun batNhipVienThuoc() {
        tayVienThuoc.removeCallbacks(nhipVienThuoc)
        tayVienThuoc.postDelayed(nhipVienThuoc, 10_000)
    }

    private fun capNhatVienThuoc() {
        val v = vienThuoc ?: return
        val tt = TrangThaiFocus.doc(this)
        // Phien vua ket thuc hoac bi dung -> ve lai ca trang, vi vien
        // thuoc phai bien mat va bo cuc ben duoi doi theo.
        if (!tt.dem.dangChay && !tt.dem.dangDung) { lamMoi(); return }
        val bay = System.currentTimeMillis()
        val phut = DemNguoc.soPhutHien(tt.dem.conLaiMs(bay))
        tvVienThuoc?.text =
            if (phut == 0) getString(R.string.focus_sap_xong) else getString(R.string.gr_phut, phut)
        v.contentDescription = getString(R.string.kh_dang_chay_mo_ta, phut, tt.ten ?: "")
        thanhVienThuoc?.let { khung ->
            val rong = (khung.width * tt.dem.tyLe(bay)).toInt()
            khung.getChildAt(1)?.layoutParams =
                FrameLayout.LayoutParams(rong.coerceAtLeast(dp(6)), dp(7))
            khung.requestLayout()
        }
    }

    override fun onPause() {
        super.onPause()
        tayVienThuoc.removeCallbacks(nhipVienThuoc)
        dungCuon()
    }

    // ---------------------------------------------------------------
    // 2. The tom tat bien ban vua phan tich
    // ---------------------------------------------------------------

    /**
     * Hien MOT the tom tat bien ban gan nhat, chi trong 24 gio dau va chi
     * khi chua duoc dong. Ly do gioi han:
     *
     *   · Bien ban cu nam mai o day se thanh mot khoi nhieu thi giac co
     *     dinh - dung thu tab Ke hoach can tranh.
     *   · Sau mot ngay ma viec chua vao lich thi van de khong con la "nhac
     *     cho de xu ly ngay" nua.
     *
     * The co nut dong rieng (X): nguoi dung tu quyet dinh khi nao no di.
     */
    private fun veTheBienBan() {
        val so = SoBienBan.doc(this)
        val b = so.danhSach.lastOrNull() ?: return
        val tuoi = System.currentTimeMillis() - b.luc
        if (tuoi > 24L * 60 * 60 * 1000) return
        if (SoBienBan.daDong(this, b.luc)) return

        val t = the(tren = 12)
        t.background = getDrawable(R.drawable.nen_the_tim)
        val dau = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        dau.addView(ImageView(this).apply {
            setImageResource(R.drawable.ic_meety)
            setColorFilter(mau(R.color.ghim))
            importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
        }, LinearLayout.LayoutParams(dp(16), dp(16)).apply { marginEnd = dp(6) })
        dau.addView(nhan(getString(R.string.kh_bien_ban_vua_xong, b.ten)).apply {
            setTextColor(mau(R.color.ghim))
            maxLines = 1
            ellipsize = android.text.TextUtils.TruncateAt.END
        }, LinearLayout.LayoutParams(0, -2, 1f))
        dau.addView(ImageView(this).apply {
            setImageResource(R.drawable.ic_dong)
            setColorFilter(mau(R.color.chu_phu))
            val p = dp(8); setPadding(p, p, p, p)
            contentDescription = getString(R.string.kh_dong_the)
            setOnClickListener {
                Rung.nhe(it); SoBienBan.danhDauDong(this@ViecCanLamActivity, b.luc); lamMoi()
            }
        }, LinearLayout.LayoutParams(dp(32), dp(32)))
        t.addView(dau)

        (b.tomTat.firstOrNull() ?: b.daChot.lineSequence().firstOrNull { it.isNotBlank() })?.let {
            t.addView(chuTo(it, 14f).apply {
                maxLines = 2
                ellipsize = android.text.TextUtils.TruncateAt.END
                setPadding(0, dp(6), 0, 0)
            })
        }
        val chuaVaoLich = b.viec.filter { !SoBienBan.daVaoLich(this, b.luc, it) }
        t.addView(chuPhu(
            if (chuaVaoLich.isEmpty()) getString(R.string.kh_bb_het_viec)
            else getString(R.string.kh_bb_con_viec, chuaVaoLich.size), 13f).apply {
            setPadding(0, dp(6), 0, 0)
        })
        if (chuaVaoLich.isNotEmpty()) {
            t.addView(nutChinh(getString(R.string.bb_them_vao_lich)) {
                startActivity(Intent(this, BienBanVaoLichActivity::class.java)
                    .putExtra(BienBanVaoLichActivity.THEM_LUC, b.luc))
            }, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(10) })
        }
    }

    private fun ngayDoc(c: Calendar): String {
        val thu = listOf("Chủ nhật", "Thứ hai", "Thứ ba", "Thứ tư",
            "Thứ năm", "Thứ sáu", "Thứ bảy")[c.get(Calendar.DAY_OF_WEEK) - 1]
        return "$thu, ${c.get(Calendar.DAY_OF_MONTH)} tháng ${c.get(Calendar.MONTH) + 1}"
    }

    // ---------------------------------------------------------------
    // 1. Tom tat + uu tien
    // ---------------------------------------------------------------

    private fun veTomTat(ds: List<KeHoach>, homNay: Long, phut: Int) {
        val t = the(tren = 14)
        val xong = ds.count { Lich.khoaXong(it.id, homNay) in soLich.daXong }
        val con = ds.count { Lich.khoaXong(it.id, homNay) !in soLich.daXong && it.ketThuc > phut }
        val tong = ds.sumOf { it.thoiLuong }

        val so = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        fun o(giaTri: String, nhanChu: String) = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            addView(TextView(this@ViecCanLamActivity).apply {
                text = giaTri; textSize = 22f; gravity = Gravity.CENTER
                includeFontPadding = false
                typeface = android.graphics.Typeface.DEFAULT_BOLD
                setTextColor(mau(R.color.chu))
            }, LinearLayout.LayoutParams(-1, -2))
            addView(chuPhu(nhanChu, 12f).apply { gravity = Gravity.CENTER; setPadding(0, dp(4), 0, 0) },
                LinearLayout.LayoutParams(-1, -2))
        }
        val lp = LinearLayout.LayoutParams(0, -2, 1f)
        so.addView(o("${ds.size}", getString(R.string.kh_tt_viec)), lp)
        // Muc 4.3: bo chuoi `.replace(" giờ ", "g").replace(" phút", "′")`.
        // No lay chuoi da dich roi CAT CHU trong do - nen o che do English
        // "1 hr 15 min" khong khop mau nao va hien ra nguyen xi, con o
        // tieng Viet thi ra "1g15′", mot dang viet tat khong ai doc quen.
        // `moTaPhut` gio tra thang "75 phút", khong can cat gi nua.
        so.addView(o(if (tong == 0) "0" else Lich.moTaPhut(tong, this),
            getString(R.string.kh_tt_tong)), LinearLayout.LayoutParams(lp))
        so.addView(o("$con", getString(R.string.kh_tt_con)), LinearLayout.LayoutParams(lp))
        t.addView(so)
        t.contentDescription = getString(R.string.kh_tt_mo_ta, ds.size, Lich.moTaPhut(tong, this), con, xong)

        // Ba o uu tien - LUON du ba o, ke ca khi bang 0 (vi tri co dinh).
        val hang = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(0, dp(14), 0, 0)
        }
        for ((i, u) in UuTien.entries.withIndex()) {
            val n = ds.count { it.uuTien == u }
            hang.addView(
                chipUuTien(u, n),
                LinearLayout.LayoutParams(0, dp(40), 1f).apply {
                    if (i > 0) marginStart = dp(8)
                }
            )
        }
        t.addView(hang)
    }

    private fun chipUuTien(u: UuTien, n: Int) = LinearLayout(this).apply {
        orientation = LinearLayout.HORIZONTAL
        gravity = Gravity.CENTER
        background = GradientDrawable().apply {
            cornerRadius = dp(20).toFloat()
            setColor(mau(R.color.nen))
        }
        addView(View(this@ViecCanLamActivity).apply {
            background = GradientDrawable().apply {
                shape = GradientDrawable.OVAL; setColor(mauUuTien(u))
            }
        }, LinearLayout.LayoutParams(dp(10), dp(10)).apply { marginEnd = dp(6) })
        addView(TextView(this@ViecCanLamActivity).apply {
            text = getString(R.string.kh_uu_tien_dem, context.getString(u.resID), n)
            textSize = 13f; includeFontPadding = false
            setTextColor(mau(R.color.chu))
        })
        contentDescription = getString(R.string.kh_uu_tien_mo_ta, context.getString(u.resID), n)
    }

    private fun mauUuTien(u: UuTien) = mau(when (u) {
        UuTien.CAO -> R.color.uu_cao
        UuTien.VUA -> R.color.uu_vua
        UuTien.THAP -> R.color.uu_thap
    })

    // ---------------------------------------------------------------
    // 2. Tiep theo
    // ---------------------------------------------------------------

    private fun veTiepTheo(ds: List<KeHoach>, homNay: Long, phut: Int) {
        val kh = Lich.tiepTheo(ds, homNay * 1440 + phut, soLich.daXong) ?: return
        val t = the(vienCam = true, tren = 12)
        t.addView(nhan(if (kh.batDau <= phut) getString(R.string.kh_dang_dien_ra)
                       else getString(R.string.kh_tiep_theo_luc, Lich.gioPhut(kh.batDau))))
        t.addView(chuTo("${kh.emoji}  ${kh.ten}", 17f).apply { setPadding(0, dp(4), 0, 0) })
        t.addView(chuPhu(getString(R.string.kh_trong_khoang, Lich.gioPhut(kh.batDau),
            Lich.gioPhut(kh.ketThuc), Lich.moTaPhut(kh.thoiLuong, this)), 13f))
        t.addView(nutChinh(getString(R.string.kh_bat_dau_viec)) {
            ThanhTab.mo(this, FocusActivity::class.java) { it.putExtra(FocusActivity.EXTRA_KE_HOACH, kh.id) }
        }, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(12) })
    }

    // ---------------------------------------------------------------
    // 3. Danh sach theo uu tien
    // ---------------------------------------------------------------

    // ---------------------------------------------------------------
    // 3. Ma tran uu tien: ba vung co dinh, keo tha giua cac vung
    // ---------------------------------------------------------------

    /**
     * Ba vung LUON co mat theo dung thu tu Cao - Trung binh - Thap.
     *
     * Vi sao khong an vung trong: vi tri co dinh la mot quy tac xuyen suot
     * app. Neu vung Cao bien mat khi rong thi hom sau no hien lai o cho
     * khac, va nguoi dung phai doc lai ca trang de tim. Vung trong duoc
     * THU GON thanh mot dong mong co vien dut - van thay duoc, van la cho
     * de tha viec vao, nhung khong chiem cho.
     */
    private fun veNhom(ds: List<KeHoach>, homNay: Long, ctx: Context) {
        vungUuTien.clear()
        for (u in UuTien.values()) {
            val nhom = ds.filter { it.uuTien == u }.let { Lich.theoUuTien(it) }
            them(nhan(getString(R.string.kh_nhom_uu_tien, ctx.getString(u.resID)), camMau = false).apply {
                setCompoundDrawablesRelativeWithIntrinsicBounds(GradientDrawable().apply {
                    shape = GradientDrawable.OVAL; setColor(mauUuTien(u)); setSize(dp(9), dp(9))
                }, null, null, null)
                compoundDrawablePadding = dp(6)
            }, 18)
            val vung = LinearLayout(this).apply {
                orientation = LinearLayout.VERTICAL
                tag = u
            }
            them(vung, 2)
            vungUuTien[u] = vung
            if (nhom.isEmpty()) {
                vung.addView(TextView(this).apply {
                    text = getString(R.string.kh_vung_trong)
                    textSize = 13f
                    gravity = Gravity.CENTER
                    minHeight = dp(46)
                    includeFontPadding = false
                    setTextColor(mau(R.color.chu_phu))
                    background = getDrawable(R.drawable.nen_vung_trong)
                }, LinearLayout.LayoutParams(-1, -2))
            } else {
                for (kh in nhom) theKeHoach(kh, homNay, vung)
            }
        }
        if (ds.isEmpty()) {
            them(chuPhu(getString(R.string.kh_chua_co), 13f).apply {
                gravity = Gravity.CENTER; setPadding(0, dp(12), 0, 0)
            }, 8)
        }
    }

    /** Vung tha cua tung muc uu tien, dung lai moi lan ve. */
    private val vungUuTien = LinkedHashMap<UuTien, LinearLayout>()

    /**
     * Keo-tha doi uu tien.
     *
     * Nhan giu mot the -> `startDragAndDrop`. Ba vung deu la diem tha; vung
     * nao ngon tay dang o tren thi sang vien cam. Tha xuong la doi uu tien
     * ngay, khong mo hop thoai nao.
     *
     * Nhan giu O DAY khong mau thuan voi quy tac "bo nhan giu": quy tac do
     * noi ve cac hanh dong CHINH (xong / xoa) - chung da co o tron va cu
     * vuot. Keo-tha buoc phai bat dau bang mot cu giu, va no van con duong
     * khac hoan toan tuong duong: mo the ra va doi uu tien trong trang sua.
     */
    /**
     * The dang duoc keo. Giu THAM CHIEU THANG, khong tim lai theo tag.
     *
     * Ban truoc dat `t.tag = TAG_DANG_KEO` cho MOI the roi goi
     * `findViewWithTag` luc tha - ham do tra ve the DAU TIEN mang tag ay,
     * gan nhu khong bao gio la the dang keo. Ket qua: the that giu nguyen
     * alpha 0,35 sau khi tha, thanh mot bong mo lo lung tren man hinh, con
     * the dau danh sach bi dat lai alpha 1 (vo nghia, no van dang la 1).
     */
    private var theDangKeo: View? = null

    /**
     * Bong keo NHAC LEN, khong phai mot ban sao phang.
     *
     * `View.DragShadowBuilder` mac dinh chup the o dung kich thuoc va dat
     * duoi ngon tay - khong co gi noi rang no dang duoc nhac khoi mat
     * phang. Ket qua la nguoi dung khong chac minh da bat duoc the chua.
     *
     * Ban nay phong to 6% va ve mot lop bong do mem ben duoi: the trong
     * nhu dang lo lung tren danh sach. Cung thu Material goi la
     * "elevation", chi la o day phai tu ve vi bong keo la mot Canvas
     * rieng, khong nam trong cay view nen khong co `elevation`.
     */
    private class BongNhacLen(v: View, private val doPhong: Float = 1.06f) :
        View.DragShadowBuilder(v) {

        private val butBong = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG)

        override fun onProvideShadowMetrics(kichThuoc: android.graphics.Point, cham: android.graphics.Point) {
            val v = view ?: return
            val r = (v.width * doPhong).toInt()
            val c = (v.height * doPhong).toInt()
            kichThuoc.set(r + VIEN * 2, c + VIEN * 2)
            // Ngon tay o giua the, khong o goc tren-trai.
            cham.set(kichThuoc.x / 2, kichThuoc.y / 2)
        }

        override fun onDrawShadow(canvas: android.graphics.Canvas) {
            val v = view ?: return
            canvas.save()
            // Bong do mem: ve trung tam lech xuong mot chut.
            butBong.color = 0x33000000
            butBong.maskFilter = android.graphics.BlurMaskFilter(
                VIEN.toFloat(), android.graphics.BlurMaskFilter.Blur.NORMAL)
            val w = v.width * doPhong
            val h = v.height * doPhong
            canvas.drawRoundRect(
                VIEN.toFloat(), VIEN.toFloat() + 3f,
                VIEN + w, VIEN + h + 3f, 20f, 20f, butBong)
            canvas.restore()

            canvas.save()
            canvas.translate(VIEN.toFloat(), VIEN.toFloat())
            canvas.scale(doPhong, doPhong)
            v.draw(canvas)
            canvas.restore()
        }

        private companion object { const val VIEN = 12 }
    }

    private fun batKeoTha(the: View, kh: KeHoach) {
        the.setOnLongClickListener { v ->
            // Nhip manh hon `nhe`: day la luc the ROI KHOI cho cua no,
            // va nguoi dung can biet dieu do da xay ra truoc khi di chuyen.
            Rung.rung(v, 2)
            val bong = BongNhacLen(v)
            val du = android.content.ClipData.newPlainText("ke_hoach", kh.id)
            @Suppress("DEPRECATION")
            val ok = if (android.os.Build.VERSION.SDK_INT >= 24)
                v.startDragAndDrop(du, bong, kh.id, 0) else v.startDrag(du, bong, kh.id, 0)
            if (ok) { v.alpha = 0.35f; theDangKeo = v }
            ok
        }
    }

    /**
     * Tra the dang keo ve nguyen trang.
     *
     * Goi o CA `ACTION_DRAG_ENDED` cua vung tha LAN cua goc man hinh: keo
     * roi tha ra ngoai ca ba vung thi vung tha khong nhan duoc gi, va neu
     * chi trong vao chung thi bong mo van o lai.
     */
    private fun thoiKeo() {
        theDangKeo?.alpha = 1f
        theDangKeo = null
    }

    /**
     * ================================================================
     * HAI LOI THAT, TIM RA KHI CHAY TREN MAY
     * ================================================================
     *
     * ----- 1. CRASH / DO MAN HINH KHI THA -----
     *
     * `ACTION_DROP` goi thang `doiUuTien`, ma ham do goi `lamMoi()`, ma
     * `lamMoi()` goi `noiDung.removeAllViews()`.
     *
     * Tuc la: dang O TRONG mot lan dispatch su kien keo cua chinh view
     * `vung`, ta go bo chinh view do khoi cay. Khung keo-tha sau do con
     * phai gui tiep `ACTION_DRAG_ENDED` toi cac view da dang ky - gio
     * chung da mo coi. Ket qua tuy may: hoac nem ngoai le, hoac phien keo
     * khong bao gio ket thuc va man hinh dung im.
     *
     * Chua bang `post`: hoan viec dung lai cay view sang khung hinh sau,
     * khi lan dispatch nay da xong han.
     *
     * ----- 2. KHONG KEO SANG NHOM KHAC DUOC -----
     *
     * Trang nay nam trong mot `ScrollView` (`R.id.cuon_trang`), va ba
     * nhom uu tien xep doc. Voi the tom tat, the bien ban va vien thuoc o
     * tren, nhom "Thap" gan nhu luon nam duoi mep man hinh.
     *
     * Android KHONG tu cuon trong luc keo-tha. Nguoi dung keo the toi sat
     * mep duoi, va o do khong co gi xay ra ca - vung can tha thi o ngoai
     * man hinh, con tay thi khong keo xuong duoc nua.
     *
     * Nen phai tu cuon: khi ngon tay vao vung 96dp sat mep tren hoac mep
     * duoi, trang tu truot theo, cang sat mep cang nhanh. Khong co no thi
     * tinh nang chi dung duoc khi ca ba nhom tinh co cung vua man hinh.
     */
    private fun batVungTha() {
        val cuon = findViewById<android.widget.ScrollView>(R.id.cuon_trang)

        // Luoi do o goc man hinh: tha ra NGOAI ca ba vung (len thanh tab,
        // ra le man hinh) thi khong vung nao nhan duoc su kien, nhung goc
        // thi luon nhan `ACTION_DRAG_ENDED`.
        window.decorView.setOnDragListener { _, e ->
            when (e.action) {
                // Vi tri ngon tay chi den o day khi khong vung nao nhan -
                // tuc la dung luc can cuon nhat.
                android.view.DragEvent.ACTION_DRAG_LOCATION ->
                    tuCuon(cuon, e.y - cuonTren(cuon))
                android.view.DragEvent.ACTION_DRAG_ENDED -> { dungCuon(); thoiKeo() }
            }
            true
        }

        for ((u, vung) in vungUuTien) {
            vung.setOnDragListener { v, e ->
                when (e.action) {
                    android.view.DragEvent.ACTION_DRAG_ENTERED -> {
                        v.background = getDrawable(R.drawable.nen_vung_tha)
                        // Mot nac ro rang: the se roi vao day neu tha bay gio.
                        Rung.rung(v, 1)
                        true
                    }
                    android.view.DragEvent.ACTION_DRAG_LOCATION -> {
                        // `e.y` o day tinh theo goc cua `vung`, phai doi ve
                        // toa do man hinh truoc khi so voi mep tren/duoi.
                        val xy = IntArray(2)
                        v.getLocationOnScreen(xy)
                        tuCuon(cuon, e.y + xy[1] - cuonTren(cuon))
                        true
                    }
                    // EXITED chi la "ngon tay roi khoi vung nay" - keo van
                    // dang tiep dien, nen KHONG duoc tra alpha o day.
                    android.view.DragEvent.ACTION_DRAG_EXITED -> {
                        v.background = null
                        true
                    }
                    android.view.DragEvent.ACTION_DRAG_ENDED -> {
                        v.background = null
                        dungCuon()
                        thoiKeo()
                        true
                    }
                    android.view.DragEvent.ACTION_DROP -> {
                        v.background = null
                        dungCuon()
                        thoiKeo()
                        val id = e.localState as? String ?: return@setOnDragListener false
                        // HOAN sang khung hinh sau - xem muc 1 o ghi chu tren.
                        // Dung lai cay view ngay giua lan dispatch nay la
                        // dung cai lam app crash / dung im.
                        v.post { doiUuTien(id, u) }
                        true
                    }
                    android.view.DragEvent.ACTION_DRAG_STARTED -> true
                    else -> true
                }
            }
        }
    }

    // ---------------------------------------------------------------
    // Tu cuon khi keo toi sat mep
    // ---------------------------------------------------------------

    private val tayCuon = android.os.Handler(android.os.Looper.getMainLooper())
    private var vanTocCuon = 0

    /** Toa do Y cua mep tren `ScrollView` tren man hinh. */
    private fun cuonTren(cuon: android.widget.ScrollView?): Int {
        val v = cuon ?: return 0
        val xy = IntArray(2)
        v.getLocationOnScreen(xy)
        return xy[1]
    }

    private val nhipCuon = object : Runnable {
        override fun run() {
            if (vanTocCuon == 0) return
            findViewById<android.widget.ScrollView>(R.id.cuon_trang)?.scrollBy(0, vanTocCuon)
            tayCuon.postDelayed(this, 16)
        }
    }

    /**
     * @param y toa do ngon tay tinh theo goc tren cua `ScrollView`.
     *
     * Toc do tang dan theo do sat mep: vao ria thi bo nhe, sat han thi
     * nhanh. Mot toc do co dinh se hoac qua cham de toi duoc nhom cuoi,
     * hoac qua nhanh de dung lai dung cho.
     */
    private fun tuCuon(cuon: android.widget.ScrollView?, y: Float) {
        val v = cuon ?: return
        val ria = dp(96).toFloat()
        val cao = v.height.toFloat()
        vanTocCuon = when {
            y < ria -> -(((ria - y) / ria) * dp(18)).toInt().coerceAtLeast(1)
            y > cao - ria -> (((y - (cao - ria)) / ria) * dp(18)).toInt().coerceAtLeast(1)
            else -> 0
        }
        tayCuon.removeCallbacks(nhipCuon)
        if (vanTocCuon != 0) tayCuon.post(nhipCuon)
    }

    private fun dungCuon() {
        vanTocCuon = 0
        tayCuon.removeCallbacks(nhipCuon)
    }

    /**
     * Ban truoc nhan them mot `ctx` lay bang `this.parent.baseContext`.
     * `Activity.getParent()` tra ve null tru khi Activity nam trong mot
     * ActivityGroup - thu da bo tu API 13 - nen `.baseContext` nem
     * NullPointerException ngay trong `ACTION_DROP`. Khung keo-tha nuot
     * ngoai le do, phien keo chet giua chung, va man hinh o lai trong mot
     * trang thai khong ai doan duoc. Activity nay da la Context roi.
     */
    private fun doiUuTien(id: String, u: UuTien) {
        val kh = soLich.tim(id) ?: return
        if (kh.uuTien == u) { lamMoi(); return }
        soLich.luuKeHoach(this, kh.copy(uuTien = u))
        Rung.xong(noiDung)
        lamMoi()
        ThongBao.hien(this, getString(R.string.kh_da_doi_uu_tien, kh.ten, getString(u.resID)))
    }

    private fun theKeHoach(kh: KeHoach, homNay: Long, vung: LinearLayout) {
        val xong = Lich.khoaXong(kh.id, homNay) in soLich.daXong
        val t = theRieng()
        val h = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        // O tron danh dau xong: 44dp vung cham, 24dp hinh.
        h.addView(ImageView(this).apply {
            val p = dp(10)
            setPadding(p, p, p, p)
            if (xong) {
                background = getDrawable(R.drawable.tron_cam)
                setImageResource(R.drawable.ic_tick)
                setColorFilter(mau(R.color.the))
            } else {
                setImageDrawable(getDrawable(R.drawable.tron_viec))
            }
            contentDescription = getString(if (xong) R.string.kh_bo_danh_dau else R.string.kh_danh_dau_xong)
            setOnClickListener { Rung.xong(it); doiXong(kh, homNay) }
        }, LinearLayout.LayoutParams(dp(44), dp(44)))

        val cot = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(8), 0, 0, 0)
        }
        // ----- DAU GHIM NHIN THAY DUOC (muc 5.4) -----
        //
        // Ghim da day viec len dau danh sach (`GHIM_ROI_UU_TIEN`), nhung
        // tren man hinh khong co gi noi ra dieu do. Nguoi dung vuot phai,
        // the nhay len dau, roi khong con dau vet nao - va lan mo app sau
        // ho khong biet vi sao viec do lai nam tren cung, hay lam sao go
        // no xuong.
        //
        // Mot cai ghim nho truoc ten la du. Khong to hon, khong doi mau ca
        // the: ghim la "toi muon nhin thay cai nay truoc", khong phai
        // "cai nay khan cap" - do la viec cua muc uu tien, va hai thu do
        // ma trong giong nhau thi ca hai deu mat nghia.
        val hangTen = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        if (kh.ghim) {
            hangTen.addView(ImageView(this).apply {
                setImageResource(R.drawable.ic_ghim)
                setColorFilter(mau(R.color.ghim))
                contentDescription = getString(R.string.vuot_ghim)
            }, LinearLayout.LayoutParams(dp(14), dp(14)).apply { marginEnd = dp(5) })
        }
        hangTen.addView(chuTo("${kh.emoji}  ${kh.ten}", 15f).apply {
            includeFontPadding = false
            if (xong) {
                setTextColor(mau(R.color.chu_phu))
                paintFlags = paintFlags or Paint.STRIKE_THRU_TEXT_FLAG
            }
        }, LinearLayout.LayoutParams(0, -2, 1f))
        // Viec da xong: mo CA THE di, khong chi rieng dong ten. Mot the
        // sang nguyen voi mot dong chu bi gach doc ra nhu loi hien thi;
        // ca the mo di thi no lui han ve sau, dung cho cua mot viec khong
        // con can nghi toi nua.
        if (xong) t.alpha = 0.6f
        cot.addView(hangTen, LinearLayout.LayoutParams(-1, -2))
        cot.addView(chuPhu("${Lich.gioPhut(kh.batDau)}–${Lich.gioPhut(kh.ketThuc)} · " +
            Lich.moTaPhut(kh.thoiLuong, this) +
            (if (kh.lapLai != LapLai.KHONG) " · ${Lich.moTaLapLai(kh.lapLai)}" else ""), 12f).apply {
            includeFontPadding = false; setPadding(0, dp(4), 0, 0)
        })
        h.addView(cot, LinearLayout.LayoutParams(0, -2, 1f))

        // Vach uu tien ben phai: hinh + mau, kem chu cho trinh doc man hinh.
        h.addView(View(this).apply {
            background = GradientDrawable().apply { cornerRadius = dp(3).toFloat(); setColor(mauUuTien(kh.uuTien)) }
        }, LinearLayout.LayoutParams(dp(6), dp(30)).apply { marginStart = dp(8) })
        t.addView(h)
        t.isClickable = true
        t.background = getDrawable(R.drawable.nen_the)
        t.setOnClickListener {
            startActivity(Intent(this, KeHoachActivity::class.java).putExtra(KeHoachActivity.THEM_ID, kh.id))
        }
        t.contentDescription = "${kh.ten}, ${Lich.gioPhut(kh.batDau)} đến ${Lich.gioPhut(kh.ketThuc)}, " +
            "ưu tiên ${vung.context.getString(kh.uuTien.resID)}" + if (xong) ", đã xong" else ""

        batKeoTha(t, kh)
        val k = KhungVuot(this, t,
            khiXong = { doiXong(kh, homNay) },
            khiXoa = { xoa(kh) },
            khiGhim = { doiGhim(kh) },
            // Nhan doi theo trang thai that - xem ghi chu `daXong` o KhungVuot.
            nhanXong = getString(if (xong) R.string.vuot_chua_xong else R.string.vuot_xong),
            nhanGhim = getString(if (kh.ghim) R.string.vuot_bo_ghim else R.string.vuot_ghim),
            daXong = xong)
        vung.addView(k, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(8) })
    }

    /** Ghim / bo ghim: viec ghim nhay len dau danh sach ngay. */
    private fun doiGhim(kh: KeHoach) {
        val moi = soLich.doiGhim(this, kh.id)
        lamMoi()
        ThongBao.hien(this, getString(
            if (moi) R.string.da_ghim_ten else R.string.da_bo_ghim_ten, kh.ten))
    }

    private fun doiXong(kh: KeHoach, homNay: Long) {
        soLich.doiXong(this, kh.id, homNay)
        if (Lich.khoaXong(kh.id, homNay) in soLich.daXong) {
            SoTienDo.doc(this).apply { ghi(); luu(this@ViecCanLamActivity) }
        }
        LichBao.datLai(this, soLich)
        lamMoi()
    }

    private fun xoa(kh: KeHoach) {
        val daXong = soLich.daXong.filter { it.startsWith(kh.id + "|") }
        soLich.xoa(this, kh.id)
        LichBao.datLai(this, soLich)
        lamMoi()
        HoanTac.hien(this, getString(R.string.da_xoa_ten, kh.ten)) {
            val lai = SoLich.doc(this)
            lai.luuKeHoach(this, kh)
            lai.daXong.addAll(daXong); lai.luu(this)
            LichBao.datLai(this, lai)
            lamMoi()
        }
    }
}
