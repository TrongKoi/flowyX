package vn.adc2026.wayfinding

import android.app.Activity
import android.graphics.Typeface
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView

/**
 * TRANG CO TAB - lop goc cho bon tab khong phai Focus.
 *
 * Lo phan khung (`khung_trang.xml`), noi thanh tab, va cho lop con vai
 * ham dung the/tieu de. Lop con chi con viec DO NOI DUNG vao.
 *
 * --------------------------------------------------------------------
 * VI SAO DUNG THE BANG CODE, KHONG PHAI XML
 * --------------------------------------------------------------------
 *
 * Danh sach o day deu dong: so loi nhac, so muc nhat ky, so ke hoach hom
 * nay - khong biet truoc bao nhieu. Viet XML cho chung thi van phai dung
 * bang code luc chay, va luc do co HAI cho dinh nghia cung mot cai the.
 *
 * Cac the tinh (tieu de, khoi trong) cung dung ham o day de chung khop
 * voi the dong - cung bo goc, cung dem, cung mau.
 */
abstract class TrangCoTab : Activity() {

    protected lateinit var noiDung: LinearLayout
    /** Da dung xong khung trang (sau super.onCreate). */
    protected val daDung: Boolean get() = ::noiDung.isInitialized

    /** Nut hanh dong co chu tren thanh tieu de - an mac dinh. */
    protected lateinit var nutHanhDong: TextView

    /** Tab nao dang chon - lop con tra ve mot trong `ThanhTab.*`. */
    protected abstract fun tab(): Int

    /** Ngon ngu: xem NgonNgu.boc. Theo may thi khong tao context moi. */
    override fun attachBaseContext(moi: android.content.Context) {
        super.attachBaseContext(GiaoDien.boc(moi))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        GiaoDien.apTheme(this)
        super.onCreate(savedInstanceState)
        setContentView(R.layout.khung_trang)
        noiDung = findViewById(R.id.noi_dung)
        nutHanhDong = findViewById(R.id.nut_hanh_dong)
        ThanhTab.noi(this, tab())
        ThanhTieuDe.noiCaiDat(this)
        ChuyenLoiNhac.chayMotLan(this)
    }

    /** Do lai noi dung. Goi o `onResume` de so tren may luon moi. */
    private var dauVetLucVe = ""

    override fun onResume() {
        super.onResume()
        // Doi kieu chu / co chu / ngon ngu o Cai dat -> ve lai NGAY khi quay ve,
        // khong phai mo lai app. Ngon ngu doi thi phai dung lai ca Activity vi
        // chuoi duoc nap luc attachBaseContext.
        val vet = GiaoDien.dauVet(this)
        if (dauVetLucVe.isNotEmpty() && dauVetLucVe != vet) {
            val doiNgonNgu = dauVetLucVe.split("|").getOrNull(2) != vet.split("|").getOrNull(2)
            dauVetLucVe = vet
            if (doiNgonNgu) { recreate(); return }
        }
        dauVetLucVe = vet
        // Tu diem danh: mo app la duoc tinh vao chuoi ngay (v4).
        SoTienDo.doc(this).also { if (it.diemDanh()) it.luu(this) }
        lamMoi()
    }

    override fun onPause() {
        super.onPause()
        HoanTac.dong()
    }

    /** Ve lai toan bo noi dung, giu vi tri cuon. */
    protected fun lamMoi() {
        val cuon = findViewById<android.widget.ScrollView>(R.id.cuon_trang)
        val y = cuon?.scrollY ?: 0
        noiDung.removeAllViews()
        ve()
        GiaoDien.apFont(findViewById(android.R.id.content), this)
        cuon?.post { cuon.scrollTo(0, y) }
    }

    /**
     * Boc mot the de vuot: TRAI lo hai nut (Xong / Xoa), PHAI la ghim.
     * Truyen null cho hanh dong nao khong ap dung o man hinh do.
     */
    protected fun vuot(the: View, khiXong: (() -> Unit)? = null, khiXoa: (() -> Unit)? = null,
                       khiGhim: (() -> Unit)? = null, tren: Int = 8): KhungVuot {
        (the.parent as? android.view.ViewGroup)?.removeView(the)
        val k = KhungVuot(this, the, khiXong = khiXong, khiXoa = khiXoa, khiGhim = khiGhim)
        them(k, tren)
        return k
    }

    /** Tao the KHONG gan vao trang (de boc vuot). */
    protected fun theRieng(vienCam: Boolean = false): LinearLayout =
        LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            background = getDrawable(if (vienCam) R.drawable.nen_the_cam else R.drawable.nen_the)
            setPadding(dp(14), dp(13), dp(14), dp(13))
        }

    protected abstract fun ve()

    // ---------------------------------------------------------------
    // Dung khoi
    // ---------------------------------------------------------------

    protected fun dp(n: Int): Int = (n * resources.displayMetrics.density).toInt()

    protected fun mau(id: Int): Int = resources.getColor(id, theme)

    /** Tieu de lon cua trang. Mot dong, khong the bao. */
    protected fun tieuDe(chu: String, phu: String? = null) {
        them(TextView(this).apply {
            text = chu
            textSize = 24f
            setTextColor(mau(R.color.chu))
            typeface = Typeface.DEFAULT_BOLD
            setPadding(0, dp(4), 0, 0)
        })
        if (phu != null) them(chuPhu(phu))
    }

    protected fun chuPhu(chu: String, co: Float = 13f): TextView =
        TextView(this).apply {
            text = chu
            textSize = co
            setTextColor(mau(R.color.chu_phu))
            setLineSpacing(0f, 1.45f)
        }

    /**
     * Mot the. `nenVang` cho the nhan; `vienCam` cho the dang dien ra.
     *
     * Tra ve chinh khoi do lop con nhoi them view vao.
     */
    protected fun the(nenVang: Boolean = false, vienCam: Boolean = false,
                      tren: Int = 12): LinearLayout {
        val v = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            background = getDrawable(
                when {
                    nenVang -> R.drawable.nen_the_vang
                    vienCam -> R.drawable.nen_the_cam
                    else -> R.drawable.nen_the
                })
            setPadding(dp(14), dp(13), dp(14), dp(13))
        }
        them(v, tren)
        return v
    }

    /** Nhan nho viet hoa o dau mot the. */
    protected fun nhan(chu: String, camMau: Boolean = true): TextView =
        TextView(this).apply {
            text = chu.uppercase()
            textSize = 10f
            letterSpacing = 0.07f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(mau(if (camMau) R.color.cam else R.color.chu_phu))
        }

    protected fun chuTo(chu: String, co: Float = 16f): TextView =
        TextView(this).apply {
            text = chu
            textSize = co
            setTextColor(mau(R.color.chu))
            typeface = Typeface.DEFAULT_BOLD
        }

    /** Nut chinh - nen vang, chu navy. Xem quy tac mau o `colors.xml`. */
    protected fun nutChinh(chu: String, khiCham: () -> Unit): TextView =
        TextView(this).apply {
            text = chu
            textSize = 15f
            gravity = Gravity.CENTER
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(mau(R.color.chu_tren_nhan))
            background = getDrawable(R.drawable.nut_chinh)
            setPadding(dp(14), dp(15), dp(14), dp(15))
            setOnClickListener { khiCham() }
        }

    protected fun nutPhu(chu: String, khiCham: () -> Unit): TextView =
        TextView(this).apply {
            text = chu
            textSize = 14f
            gravity = Gravity.CENTER
            setTextColor(mau(R.color.chu))
            background = getDrawable(R.drawable.nut_phu)
            setPadding(dp(14), dp(13), dp(14), dp(13))
            setOnClickListener { khiCham() }
        }

    /** Hai view canh nhau, chia deu be ngang. */
    protected fun hang(trai: View, phai: View, tren: Int = 8) {
        val h = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        val lp = LinearLayout.LayoutParams(0,
            LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
        h.addView(trai, LinearLayout.LayoutParams(lp))
        h.addView(phai, LinearLayout.LayoutParams(lp).apply { marginStart = dp(8) })
        them(h, tren)
    }

    protected fun them(v: View, tren: Int = 8) {
        noiDung.addView(v, LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT
        ).apply { topMargin = dp(tren) })
    }

    /** Khoi rong, dung khi chua co gi de hien. */
    protected fun khoiTrong(chu: String) {
        val v = TextView(this).apply {
            text = chu
            textSize = 13f
            gravity = Gravity.CENTER
            setTextColor(mau(R.color.chu_phu))
            background = getDrawable(R.drawable.nen_the_net_dut)
            setPadding(dp(16), dp(26), dp(16), dp(26))
        }
        them(v, 12)
    }
}
