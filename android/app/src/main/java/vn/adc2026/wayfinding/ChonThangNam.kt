package vn.adc2026.wayfinding

import android.app.Activity
import android.app.Dialog
import android.content.Context
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.view.Gravity
import android.view.View
import android.view.Window
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView

/**
 * ====================================================================
 * BO CHON THANG / NAM (muc 5.2)
 * ====================================================================
 *
 * Cham vao thanh "< Tháng 9, 2026 >" o tab Lich -> mo mot lich thang day
 * du. Chon mot ngay -> dong lai, va tab Lich cuon toi dung tuan va dung
 * ngay do.
 *
 * ----- Vi sao khong dung DatePickerDialog cua he thong -----
 *
 * Cung ly do da viet o `BoChonGio`, va o day con nang hon: hop thoai he
 * thong mang bang mau rieng, bo goc rieng, va tren moi hang may lai mot
 * kieu. Dat no canh mot tab Lich da ve bang bang mau FlowyX thi nguoi
 * dung gap hai ngon ngu thi giac trong cung mot thao tac. Voi nguoi de
 * qua tai thi cai do khong phai "hoi le" - no lam man hinh thanh kho doc.
 *
 * Va DatePicker he thong khong the hien duoc thu quan trong nhat o day:
 * NGAY NAO CO VIEC. Xem muc "ba tang thong tin" duoi.
 *
 * ----- Ba tang thong tin tren mot o ngay -----
 *
 *   1. SO NGAY        - luon co.
 *   2. CHAM DUOI SO   - ngay do co ke hoach. Mot cham, khong dem so:
 *                       "co viec" la du de quyet dinh cham vao xem;
 *                       con so lam o ngay thanh mot bang thong ke.
 *   3. VONG TRON NEN  - ngay dang chon (nen dam) va hom nay (chi vien).
 *                       Hai thu khac nhau va phai phan biet duoc: "hom
 *                       nay" la moc co dinh, "dang chon" thi di theo tay
 *                       nguoi dung.
 *
 * ----- Mau va tuong phan -----
 *
 * Tat ca lay tu `colors.xml`, nen ban dem tu dung. Chu tren nen dam dung
 * `chu_tren_nhan`; ngay ngoai thang dung `chu_phu` - van doc duoc nhung
 * ro rang la khong thuoc thang nay.
 */
object ChonThangNam {

    /**
     * @param ngay   ngay dang chon, so ngay tu 1970
     * @param coViec tra ve true neu ngay do co ke hoach - de cham mot cham
     * @param xong   nhan ngay moi duoc chon
     */
    fun hien(a: Activity, ngay: Long, coViec: (Long) -> Boolean, xong: (Long) -> Unit) {
        val (namDau, thangDau, _) = Lich.ngayThang(ngay)
        var nam = namDau
        var thang = thangDau

        val d = Dialog(a)
        val goc = LinearLayout(a).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(a, 16), dp(a, 14), dp(a, 16), dp(a, 12))
            background = GradientDrawable().apply {
                cornerRadius = dp(a, 24).toFloat()
                setColor(mau(a, R.color.the_3))
            }
        }

        // --- Hang tieu de: < Thang 9, 2026 > ---
        val tvThang = TextView(a).apply {
            textSize = 17f
            typeface = Typeface.DEFAULT_BOLD
            gravity = Gravity.CENTER
            setTextColor(mau(a, R.color.chu))
            if (android.os.Build.VERSION.SDK_INT >= 28) isAccessibilityHeading = true
        }
        val luoi = LinearLayout(a).apply { orientation = LinearLayout.VERTICAL }

        fun veThang() {
            tvThang.text = a.getString(R.string.thang_nam, thang, nam)
            veLuoi(a, luoi, nam, thang, ngay, coViec) { chon -> xong(chon); d.dismiss() }
        }

        fun doiThang(buoc: Int) {
            thang += buoc
            while (thang > 12) { thang -= 12; nam++ }
            while (thang < 1) { thang += 12; nam-- }
            veThang()
        }

        val hangDau = LinearLayout(a).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        hangDau.addView(nutMuiTen(a, a.getString(R.string.thang_truoc)) { doiThang(-1) })
        hangDau.addView(tvThang, LinearLayout.LayoutParams(0, -2, 1f))
        hangDau.addView(nutMuiTen(a, a.getString(R.string.thang_sau), quay = true) { doiThang(1) })
        goc.addView(hangDau, LinearLayout.LayoutParams(-1, -2))

        // --- Hang ten thu ---
        val hangThu = LinearLayout(a).apply { orientation = LinearLayout.HORIZONTAL }
        for (i in 0 until 7) {
            hangThu.addView(TextView(a).apply {
                text = a.getString(Lich.TEN_THU_NGAN[i])
                textSize = 12f
                gravity = Gravity.CENTER
                setTextColor(mau(a, R.color.chu_phu))
                importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
            }, LinearLayout.LayoutParams(0, -2, 1f))
        }
        goc.addView(hangThu, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(a, 10) })

        goc.addView(luoi, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(a, 4) })

        // --- Nut "Hom nay": duong ve nhanh, luon o cung mot cho ---
        goc.addView(TextView(a).apply {
            text = a.getString(R.string.hom_nay)
            textSize = 15f
            typeface = Typeface.DEFAULT_BOLD
            gravity = Gravity.CENTER
            minHeight = dp(a, 46)
            setTextColor(mau(a, R.color.chu_lien_ket))
            setOnClickListener { Rung.nhe(it); xong(SoLich.homNay()); d.dismiss() }
        }, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(a, 6) })

        veThang()
        d.requestWindowFeature(Window.FEATURE_NO_TITLE)
        d.setContentView(goc)
        d.window?.setBackgroundDrawable(android.graphics.drawable.ColorDrawable(0))
        d.window?.setLayout((a.resources.displayMetrics.widthPixels * 0.90f).toInt(), -2)
        GiaoDien.apFont(goc, a)
        d.hien()
    }

    // ---------------------------------------------------------------

    private fun veLuoi(a: Activity, luoi: LinearLayout, nam: Int, thang: Int,
                       ngayChon: Long, coViec: (Long) -> Boolean, chon: (Long) -> Unit) {
        luoi.removeAllViews()
        val homNay = SoLich.homNay()
        val dau1 = Lich.tuNgayThang(nam, thang, 1)
        // Luoi luon bat dau tu Thu Hai cua tuan chua ngay 1.
        val batDau = Lich.dauTuan(dau1)

        // Sau hang la du cho moi thang duong lich: 31 ngay + toi da 6 o
        // dem o dau = 37 o, vua trong 42.
        for (h in 0 until 6) {
            val hang = LinearLayout(a).apply { orientation = LinearLayout.HORIZONTAL }
            var coONaoTrongThang = false
            for (c in 0 until 7) {
                val ngay = batDau + h * 7 + c
                val (n2, t2, d2) = Lich.ngayThang(ngay)
                val trongThang = n2 == nam && t2 == thang
                if (trongThang) coONaoTrongThang = true
                hang.addView(oNgay(a, d2, ngay, trongThang, ngay == ngayChon,
                    ngay == homNay, coViec(ngay), chon),
                    LinearLayout.LayoutParams(0, dp(a, 44), 1f))
            }
            // Hang cuoi toan ngay thang sau thi bo han - khong de mot hang
            // trong lam hop thoai cao them vo co.
            if (h < 4 || coONaoTrongThang) luoi.addView(hang, LinearLayout.LayoutParams(-1, -2))
        }
    }

    private fun oNgay(a: Activity, so: Int, ngay: Long, trongThang: Boolean,
                      dangChon: Boolean, laHomNay: Boolean, coViec: Boolean,
                      chon: (Long) -> Unit): View {
        val o = LinearLayout(a).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
        }
        o.addView(TextView(a).apply {
            text = "$so"
            textSize = 15f
            gravity = Gravity.CENTER
            includeFontPadding = false
            setTextColor(mau(a, when {
                dangChon -> R.color.chu_tren_nhan
                !trongThang -> R.color.chu_phu
                else -> R.color.chu
            }))
            if (dangChon || laHomNay) {
                background = GradientDrawable().apply {
                    shape = GradientDrawable.OVAL
                    if (dangChon) setColor(mau(a, R.color.nhan))
                    // Hom nay ma khong phai ngay dang chon: CHI vien. Hai
                    // trang thai nay phai phan biet duoc ngay lap tuc.
                    else setStroke(dp(a, 1), mau(a, R.color.nhan))
                }
            }
        }, LinearLayout.LayoutParams(dp(a, 34), dp(a, 34)))

        // Cham bao "ngay nay co viec". Luon chiem cho du khong co viec -
        // khong thi ca hang ngay bi day len xuong khi luoi doi thang.
        o.addView(View(a).apply {
            if (coViec) background = GradientDrawable().apply {
                shape = GradientDrawable.OVAL
                setColor(mau(a, if (dangChon) R.color.nhan else R.color.cam))
            }
        }, LinearLayout.LayoutParams(dp(a, 4), dp(a, 4)).apply { topMargin = dp(a, 3) })

        o.isClickable = trongThang
        o.contentDescription = a.getString(
            if (coViec) R.string.o_ngay_co_viec else R.string.o_ngay_trong, so)
        if (trongThang) o.setOnClickListener { Rung.nhe(it); chon(ngay) }
        return o
    }

    private fun nutMuiTen(a: Activity, moTa: String, quay: Boolean = false, khi: () -> Unit) =
        ImageView(a).apply {
            setImageResource(R.drawable.ic_quay_lai)
            setColorFilter(mau(a, R.color.chu))
            if (quay) rotation = 180f
            val p = dp(a, 12); setPadding(p, p, p, p)
            contentDescription = moTa
            layoutParams = LinearLayout.LayoutParams(dp(a, 44), dp(a, 44))
            setOnClickListener { Rung.nhe(it); khi() }
        }

    private fun dp(c: Context, n: Int) = (n * c.resources.displayMetrics.density).toInt()
    private fun mau(a: Activity, id: Int) = a.resources.getColor(id, a.theme)
}
