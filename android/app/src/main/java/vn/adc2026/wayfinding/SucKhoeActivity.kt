package vn.adc2026.wayfinding

import android.app.Activity
import android.app.AlertDialog
import android.content.Context
import android.content.Intent
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Build
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView

/**
 * ====================================================================
 * KET NOI DU LIEU SUC KHOE
 * ====================================================================
 *
 * Man hinh dong y, khong phai mot cong tac trong danh sach Cai dat.
 *
 * ----- Vi sao mot man hinh rieng -----
 *
 * Du lieu suc khoe la "nhom du lieu dac biet" theo Dieu 9 GDPR: co so
 * phap ly duy nhat dung duoc o day la SU DONG Y RO RANG. Mot cong tac
 * nam lan giua muoi cong tac khac khong phai su dong y ro rang - nguoi
 * dung gat no trong luc dang tim thu khac va khong he doc dong nao.
 *
 * Nen: mot man hinh, noi ro doc gi, de lam gi, di dau, va giu bao lau;
 * hai o tich rieng cho hai loai chi so; mot nut dong y. Tat nam ngay
 * duoi, khong giau trong menu, va tat la XOA (xem SucKhoe.tat).
 *
 * ----- Vi sao khong xin quyen ngay khi mo man -----
 *
 * Hop thoai quyen cua he thong bat len truoc khi nguoi dung kip doc se
 * bi gat theo phan xa, va Health Connect chi cho hoi lai mot so lan.
 * O day nguoi dung doc truoc, bam dong y, ROI he thong moi hoi.
 */
class SucKhoeActivity : Activity() {

    private var ngu = true
    private var buoc = true

    companion object {
        private const val MA_XIN_QUYEN = 7301
    }

    override fun attachBaseContext(moi: Context) {
        super.attachBaseContext(GiaoDien.boc(moi))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        GiaoDien.apTheme(this)
        super.onCreate(savedInstanceState)
        ngu = SucKhoe.docNgu(this)
        buoc = SucKhoe.docBuoc(this)
        ve()
    }

    private fun ve() {
        val goc = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(24), dp(20), dp(24), dp(30))
        }

        goc.addView(ImageView(this).apply {
            setImageResource(R.drawable.ic_quay_lai)
            setColorFilter(mau(R.color.chu_phu))
            val p = dp(8); setPadding(p, p, p, p)
            contentDescription = getString(R.string.quay_lai)
            background = GradientDrawable().apply {
                shape = GradientDrawable.OVAL; setColor(mau(R.color.the))
            }
            setOnClickListener { Rung.nhe(it); finish() }
        }, LinearLayout.LayoutParams(dp(40), dp(40)))

        goc.addView(TextView(this).apply {
            text = getString(R.string.sk_tieu_de)
            textSize = 24f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(mau(R.color.chu))
            if (Build.VERSION.SDK_INT >= 28) isAccessibilityHeading = true
        }, lp(22))

        goc.addView(TextView(this).apply {
            text = getString(R.string.sk_phu)
            textSize = 14f
            setLineSpacing(0f, 1.5f)
            setTextColor(mau(R.color.chu_phu))
        }, lp(10))

        if (!SucKhoe.coNguon(this)) {
            goc.addView(theVang(getString(R.string.sk_khong_co_nguon)), lp(22))
            datNoiDung(goc)
            return
        }

        // --- hai o tich ---
        goc.addView(nhanNhom(getString(R.string.sk_doc_gi)), lp(26))
        goc.addView(oTich(getString(R.string.sk_ngu), getString(R.string.sk_ngu_phu), ngu) {
            ngu = it; if (!ngu && !buoc) { buoc = true; ve() }
        }, lp(10))
        goc.addView(oTich(getString(R.string.sk_buoc), getString(R.string.sk_buoc_phu), buoc) {
            buoc = it; if (!ngu && !buoc) { ngu = true; ve() }
        }, lp(8))

        // --- bon dong cam ket ---
        goc.addView(nhanNhom(getString(R.string.sk_cam_ket)), lp(26))
        for (s in listOf(R.string.sk_ck_1, R.string.sk_ck_2, R.string.sk_ck_3, R.string.sk_ck_4)) {
            goc.addView(dongCamKet(getString(s)), lp(10))
        }

        goc.addView(TextView(this).apply {
            text = getString(R.string.pl_rieng_tu)
            textSize = 13.5f
            typeface = Typeface.DEFAULT_BOLD
            minHeight = dp(44)
            gravity = Gravity.CENTER_VERTICAL
            setTextColor(mau(R.color.chu_lien_ket))
            paintFlags = paintFlags or android.graphics.Paint.UNDERLINE_TEXT_FLAG
            setOnClickListener {
                Rung.nhe(it)
                startActivity(Intent(this@SucKhoeActivity, PhapLyActivity::class.java)
                    .putExtra(PhapLyActivity.PHAN, PhapLyActivity.RIENG_TU))
            }
        }, lp(16))

        if (SucKhoe.dangBat(this)) {
            goc.addView(theVang(getString(R.string.sk_dang_bat)), lp(18))
            goc.addView(nut(getString(R.string.sk_tat), do1 = true) { hoiTat() }, lp(16))
        } else {
            goc.addView(nut(getString(R.string.sk_dong_y)) { dongY() }, lp(24))
        }

        datNoiDung(goc)
    }

    private fun dongY() {
        SucKhoe.bat(this, ngu, buoc)
        val quyen = SucKhoe.quyenCan(this)
        if (quyen.isEmpty()) { ve(); return }
        // Tu day la hop thoai cua he dieu hanh - Flowy khong con quyet dinh gi.
        requestPermissions(quyen, MA_XIN_QUYEN)
    }

    override fun onRequestPermissionsResult(ma: Int, quyen: Array<out String>, ketQua: IntArray) {
        super.onRequestPermissionsResult(ma, quyen, ketQua)
        if (ma != MA_XIN_QUYEN) return
        val duocCai = ketQua.any { it == android.content.pm.PackageManager.PERMISSION_GRANTED }
        if (!duocCai) {
            // Bi tu choi het: khong giu trang thai "da bat" gia - no se
            // hien so lieu rong mai mai ma nguoi dung khong hieu vi sao.
            SucKhoe.tat(this)
            ve()
            AlertDialog.Builder(this)
                .setMessage(getString(R.string.sk_bi_tu_choi))
                .setPositiveButton(R.string.xong, null)
                .hien()
            return
        }
        SucKhoe.lamMoi(this) { duoc ->
            runOnUiThread {
                ve()
                if (!duoc) android.widget.Toast.makeText(
                    this, getString(R.string.sk_doc_hong), android.widget.Toast.LENGTH_LONG).show()
            }
        }
    }

    private fun hoiTat() {
        AlertDialog.Builder(this)
            .setTitle(getString(R.string.sk_tat_tieu_de))
            .setMessage(getString(R.string.sk_tat_noi_dung))
            .setNegativeButton(R.string.huy, null)
            .setPositiveButton(getString(R.string.sk_tat_lam)) { _, _ ->
                SucKhoe.tat(this)
                Rung.xong(window.decorView)
                ve()
            }
            .hien()
    }

    // --- khuon nho ---

    private fun datNoiDung(goc: LinearLayout) {
        val cuon = ScrollView(this).apply {
            setBackgroundColor(mau(R.color.nen)); isFillViewport = true
        }
        cuon.addView(goc)
        setContentView(cuon)
        GiaoDien.apFont(goc, this)
    }

    private fun oTich(ten: String, phu: String, bat: Boolean, doi: (Boolean) -> Unit): View {
        val hang = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(dp(16), dp(14), dp(16), dp(14))
            minimumHeight = dp(64)
            background = GradientDrawable().apply {
                cornerRadius = dp(18).toFloat()
                setColor(mau(if (bat) R.color.nhan_nhat else R.color.the))
                setStroke(dp(if (bat) 2 else 1), mau(if (bat) R.color.nhan_vien else R.color.vien))
            }
            isClickable = true
            setOnClickListener { Rung.nhe(it); doi(!bat); ve() }
            contentDescription = "$ten, $phu, " +
                getString(if (bat) R.string.da_chon else R.string.chua_chon)
        }
        val cot = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        cot.addView(TextView(this).apply {
            text = ten; textSize = 16f
            typeface = if (bat) Typeface.DEFAULT_BOLD else Typeface.DEFAULT
            setTextColor(mau(R.color.chu))
        })
        cot.addView(TextView(this).apply {
            text = phu; textSize = 12.5f
            setLineSpacing(0f, 1.35f)
            setTextColor(mau(R.color.chu_phu))
        }, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(3) })
        hang.addView(cot, LinearLayout.LayoutParams(0, -2, 1f))
        if (bat) hang.addView(ImageView(this).apply {
            setImageResource(R.drawable.ic_tick)
            setColorFilter(mau(R.color.cam))
        }, LinearLayout.LayoutParams(dp(22), dp(22)).apply {
            gravity = Gravity.CENTER_VERTICAL; marginStart = dp(10)
        })
        return hang
    }

    private fun dongCamKet(s: String) = LinearLayout(this).apply {
        orientation = LinearLayout.HORIZONTAL
        addView(ImageView(this@SucKhoeActivity).apply {
            setImageResource(R.drawable.ic_tick)
            setColorFilter(mau(R.color.xanh_xong))
            importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
        }, LinearLayout.LayoutParams(dp(17), dp(17)).apply {
            topMargin = dp(3); marginEnd = dp(11)
        })
        addView(TextView(this@SucKhoeActivity).apply {
            text = s; textSize = 13.5f
            setLineSpacing(0f, 1.45f)
            setTextColor(mau(R.color.chu_phu))
        }, LinearLayout.LayoutParams(-1, -2))
    }

    private fun theVang(s: String) = TextView(this).apply {
        text = s
        textSize = 13.5f
        setLineSpacing(0f, 1.5f)
        setPadding(dp(16), dp(14), dp(16), dp(14))
        setTextColor(mau(R.color.chu))
        background = GradientDrawable().apply {
            cornerRadius = dp(16).toFloat()
            setColor(mau(R.color.nhan_nhat))
        }
    }

    private fun nhanNhom(s: String) = TextView(this).apply {
        text = s; textSize = 11.5f
        typeface = Typeface.DEFAULT_BOLD
        letterSpacing = 0.05f
        setTextColor(mau(R.color.chu_phu))
    }

    private fun nut(s: String, do1: Boolean = false, khi: () -> Unit) = TextView(this).apply {
        text = s; textSize = 17f; gravity = Gravity.CENTER
        typeface = Typeface.DEFAULT_BOLD
        minHeight = dp(54); includeFontPadding = false
        if (do1) {
            setTextColor(mau(R.color.do_xoa))
            background = getDrawable(R.drawable.nut_phu)
        } else {
            setTextColor(mau(R.color.chu_tren_nhan))
            background = getDrawable(R.drawable.nut_chinh)
        }
        setOnClickListener { Rung.nhe(it); khi() }
    }

    private fun lp(tren: Int) = LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(tren) }
    private fun dp(n: Int) = (n * resources.displayMetrics.density).toInt()
    private fun mau(id: Int) = resources.getColor(id, theme)
}
