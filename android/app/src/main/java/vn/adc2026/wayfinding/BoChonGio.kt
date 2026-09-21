package vn.adc2026.wayfinding

import android.app.Activity
import android.app.Dialog
import android.content.Context
import android.graphics.drawable.GradientDrawable
import android.view.Gravity
import android.view.View
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView
import vn.adc2026.frontend.TrongCuonView

/**
 * ====================================================================
 * BO CHON GIO / NGAY - trong cuon kieu bao thuc iOS, mau FlowyX
 * ====================================================================
 *
 * Thay cho `TimePickerDialog` / `DatePickerDialog` cua he thong. Ly do:
 * hop thoai he thong mang bang mau va bo goc rieng, khong nhan co chu cua
 * app, va tren moi hang may lai mot kieu - nguoi dung gap ba giao dien
 * khac nhau trong cung mot app.
 *
 * Bo chon nay:
 *   · Hai cot gio / phut, buoc 5 phut (co nut "phut le" khi can dung phut).
 *   · Dai chon sang mau vang nhat, dong giua to va dam hon hai dong kia.
 *   · Chieu cao 168dp - vua ba dong, khong che het man hinh.
 *   · Nut "Xong" o duoi, va bam ra ngoai la huy (khong am tham luu).
 */
object BoChonGio {

    /**
     * ================================================================
     * BUOC MOT PHUT, KHONG PHAI NAM (muc 5.3)
     * ================================================================
     *
     * Ly do cu: "nguoi ADHD hiem khi can dat 14:37". Dung voi gio BAT
     * DAU - nhung cung bo chon nay dung cho gio KET THUC, cho moc nhac,
     * va cho gio hen ma nguoi khac dat ra: cuoc hop 14:05, xe buyt 7:52,
     * uong thuoc 21:03. Voi nhung cai do thi buoc nam phut khong phai la
     * don gian hoa - no la SAI, va nguoi dung phai di tim mot nut khac
     * de sua lai cho dung.
     *
     * Nut "phut le" sinh ra chinh de vong qua han che nay, va no la mot
     * lua chon them ma nguoi dung phai hieu truoc khi dung duoc. Bo buoc
     * nam phut thi bo luon duoc nut do: mot muc bot khoi man hinh.
     *
     * Quan tinh that (xem `TrongCuonView.nem`) lam cho 60 nac cuon nhanh
     * khong kem 12 nac - day la dieu kien de bo duoc buoc nam.
     */
    private const val BUOC = 1

    /**
     * @param phut gia tri ban dau, tinh tu 00:00
     * @param xong nhan so phut moi
     */
    fun hien(a: Activity, tieuDe: String, phut: Int, xong: (Int) -> Unit) {
        var gio = (phut / 60).coerceIn(0, 23)
        var ph = phut % 60

        val d = Dialog(a)
        val goc = LinearLayout(a).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(a, 20), dp(a, 18), dp(a, 20), dp(a, 14))
            background = GradientDrawable().apply {
                cornerRadius = dp(a, 24).toFloat()
                setColor(a.resources.getColor(R.color.the_3, a.theme))
            }
        }
        goc.addView(TextView(a).apply {
            text = tieuDe
            textSize = 17f
            typeface = android.graphics.Typeface.DEFAULT_BOLD
            setTextColor(mau(a, R.color.chu))
            if (android.os.Build.VERSION.SDK_INT >= 28) isAccessibilityHeading = true
        })

        val khung = FrameLayout(a)
        // Dai sang danh dau dong dang chon.
        khung.addView(View(a).apply {
            background = GradientDrawable().apply {
                cornerRadius = dp(a, 12).toFloat()
                setColor(mau(a, R.color.nhan_nhat))
                setStroke(dp(a, 1), mau(a, R.color.nhan_vien))
            }
        }, FrameLayout.LayoutParams(-1, dp(a, 56), Gravity.CENTER_VERTICAL))

        val hang = LinearLayout(a).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER
        }
        fun cot(gt: List<String>, chon: Int, doi: (Int) -> Unit) = TrongCuonView(a).apply {
            gia = gt
            chiSo = chon
            chayVong = gt.size > 6
            datMau(mau(a, R.color.chu), mau(a, R.color.chu_phu))
            datFont(GiaoDien.font(a, true), dp(a, 26).toFloat() * AppSettings(a).coChu)
            khiDoi = { Rung.tich(this); doi(it) }
        }

        val cotGio = cot((0..23).map { "%02d".format(it) }, gio) { gio = it }
        val cotPhut = cot((0 until 60 step BUOC).map { "%02d".format(it) },
            (ph / BUOC).coerceIn(0, 59 / BUOC)) { ph = it * BUOC }

        hang.addView(cotGio, LinearLayout.LayoutParams(0, dp(a, 168), 1f))
        hang.addView(TextView(a).apply {
            text = ":"
            textSize = 24f
            setTextColor(mau(a, R.color.chu_phu))
            gravity = Gravity.CENTER
            importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
        }, LinearLayout.LayoutParams(dp(a, 16), dp(a, 168)))
        hang.addView(cotPhut, LinearLayout.LayoutParams(0, dp(a, 168), 1f))
        khung.addView(hang, FrameLayout.LayoutParams(-1, dp(a, 168)))
        goc.addView(khung, LinearLayout.LayoutParams(-1, dp(a, 168)).apply { topMargin = dp(a, 12) })

        // Nut "Phut le" da bo: buoc 1 phut lam no thua. Xem ghi chu o `BUOC`.

        goc.addView(TextView(a).apply {
            text = a.getString(R.string.xong)
            textSize = 16f
            typeface = android.graphics.Typeface.DEFAULT_BOLD
            gravity = Gravity.CENTER
            minHeight = dp(a, 50)
            setTextColor(mau(a, R.color.chu_tren_nhan))
            background = GradientDrawable().apply {
                cornerRadius = dp(a, 16).toFloat()
                setColor(mau(a, R.color.nhan))
            }
            setOnClickListener {
                Rung.xong(it)
                xong(gio * 60 + ph)
                d.dismiss()
            }
        }, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(a, 6) })

        d.requestWindowFeature(android.view.Window.FEATURE_NO_TITLE)
        d.setContentView(goc)
        d.window?.setBackgroundDrawable(android.graphics.drawable.ColorDrawable(0))
        d.window?.setLayout((a.resources.displayMetrics.widthPixels * 0.86f).toInt(), -2)
        GiaoDien.apFont(goc, a)
        d.hien()
    }

    private fun dp(c: Context, n: Int) = (n * c.resources.displayMetrics.density).toInt()
    private fun mau(a: Activity, id: Int) = a.resources.getColor(id, a.theme)
}
