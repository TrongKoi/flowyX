package vn.adc2026.frontend

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.graphics.Typeface
import android.os.Bundle
import android.util.AttributeSet
import android.view.MotionEvent
import android.view.View
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import kotlin.math.abs
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.min
import kotlin.math.roundToInt
import kotlin.math.sin

/**
 * ====================================================================
 * DONG HO TAP TRUNG - CO CHE TIIMO (v5)
 * ====================================================================
 *
 * Mot VANH khac vach bao quanh mot MAT tron. Phan thoi gian da chon duoc
 * to mau tren vanh; dau vanh co mot TAY CAM de keo. Mot vong = 60 phut,
 * gio thu hai la vanh mong ben ngoai, toi da 2 tieng.
 *
 * ----- Bon quyet dinh, va ly do -----
 *
 * 1. MAT TUYET DOI 60 PHUT, khong phai "luon day luc bat dau".
 *    15 phut LUC NAO cung la mot phan tu vanh. Nguoi mu thoi gian khong
 *    thieu con so - ho thieu cam nhan "15 phut dai co nao". Voi vanh
 *    luon day thi 15 phut va 90 phut trong y het nhau, khong hoc duoc gi.
 *
 * 2. KHONG HIEN GIAY. Giay nhay lien tuc keo mat nhin va tao lo au. O
 *    giua chi co SO PHUT; mat vanh chi ghi bon moc 15 / 30 / 45 / 60.
 *    Duoi mot phut thi ghi "sap xong" chu khong dem lui tung giay.
 *
 * 3. MAU DOI THEO CHANG. Con nhieu -> mau lanh (khong giuc). Con it ->
 *    vang. Sap het -> cam. Mau la mot kenh thong tin nua ve thoi gian,
 *    cho nguoi khong doc duoc con so trong mot cai liec.
 *
 * 4. RUNG LUY TIEN KHI KEO. Moi moc 5 phut co mot nhip rung; keo cang
 *    dai thi nhip cang manh, co tran an toan (xem `Rung.luyTien`). Tay
 *    "nghe" duoc do dai ma khong can nhin so.
 *
 * View nay khong biet gi ve dem nguoc: no chi ve va bao ra so phut. Logic
 * dem o `DemNguoc`, da co test tren JVM.
 */
class VongTapTrungView @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null, defStyle: Int = 0,
) : View(context, attrs, defStyle) {

    /** Goi khi nguoi dung keo doi so phut (chi khi `choKeo`). */
    var khiDoiPhut: ((Int) -> Unit)? = null

    /** Goi moi khi qua mot moc 5 phut luc keo, kem ty le 0..1 de rung luy tien. */
    var khiQuaMoc: ((Float) -> Unit)? = null

    /** Cho phep keo dat gio. Dang chay thi tat, de cham nham khong doi gio. */
    var choKeo: Boolean = true

    /**
     * ----- KEO NGAY TRONG LUC DANG CHAY (muc 6.2) -----
     *
     * Dat gio xong roi moi nhan ra "minh can them muoi phut nua" la
     * chuyen thuong xuyen. Truoc day muon doi thi phai dung phien lai -
     * ma dung phien la mat luon cai da vao duoc.
     *
     * Nen luc dang chay VAN keo duoc, nhung sieu chat hon mot bac:
     *
     *   · Phai cham dung vao VANH, khong phai giua mat. Cham giua mat
     *     luc dang chay la cham nham (cat tui, dat may xuong), va no
     *     khong duoc doi gio.
     *   · Moi phut keo qua co mot nhip rung rieng - `khiKeoQuaPhut`.
     *     Dem bang ngon tay, khong can nhin so.
     *   · Chi keo DAI RA duoc, khong rut ngan. Rut ngan trong luc dang
     *     chay la mot duong ra khoi phien ma nguoi dung khong co y
     *     chon; muon dung thi da co nut Dung lai.
     */
    var choKeoKhiChay: Boolean = true

    /** Goi moi khi keo qua mot phut trong luc dang chay. */
    var khiKeoQuaPhut: (() -> Unit)? = null

    private var conLaiPhut: Float = 25f
    private var dangChay: Boolean = false

    // Mau - Activity bom vao tu res/values(-night)/colors.xml.
    private var mauMat = Color.WHITE
    private var mauMatKhiKeo = Color.WHITE
    private var mauVachKhac = Color.WHITE
    private var mauRanh = Color.LTGRAY
    private var mauChu = Color.DKGRAY
    private var mauChuPhu = Color.GRAY
    private var mauConNhieu = Color.parseColor("#4A4470")
    private var mauSapDen = Color.parseColor("#E8A200")
    private var mauDiNgay = Color.parseColor("#F0663A")
    private var mauDangKeo = Color.parseColor("#5B50B8")

    private val butMat = Paint(Paint.ANTI_ALIAS_FLAG)
    private val butVanh = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.STROKE }
    private val butVach = Paint(Paint.ANTI_ALIAS_FLAG).apply { strokeCap = Paint.Cap.ROUND }
    private val butTay = Paint(Paint.ANTI_ALIAS_FLAG)
    private val butSo = Paint(Paint.ANTI_ALIAS_FLAG).apply { textAlign = Paint.Align.CENTER }
    private val butGiua = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        textAlign = Paint.Align.CENTER; typeface = Typeface.DEFAULT_BOLD
    }
    private val butNhan = Paint(Paint.ANTI_ALIAS_FLAG).apply { textAlign = Paint.Align.CENTER }
    private val oVanh = RectF()

    private var nhanGiua = "25"
    private var nhanDuoi = "PHÚT"

    // Trang thai keo: goc cong don de keo qua 60 phut thi sang gio thu hai.
    private var gocTruoc = 0.0
    private var phutKeo = 25.0
    private var mocTruoc = 5
    private var dangKeo = false
    private var phutKeoTruoc = 25

    /**
     * ----- NHIP THO (muc 6.1) -----
     *
     * Mot vong sang rat mo quanh vanh, phinh ra va thu vao theo chu ky
     * BON GIAY - dung nhip mot hoi tho binh thuong cua nguoi lon.
     *
     * Vi sao can: mat dong ho khong hien giay (quyet dinh 2 o tren), nen
     * nhin vao mot dong ho dang chay va mot dong ho dang tam dung thay y
     * het nhau cho toi khi so phut doi - co the hai muoi giay sau. Nguoi
     * dung bam Bat dau roi khong chac no da chay chua, va bam lai - thanh
     * ra tam dung.
     *
     * Vi sao la hoi tho chu khong phai nhap nhay: nhap nhay keo mat va
     * gay lo au, dung thu Flowy tranh khap noi. Bon giay mot nhip cham
     * toi muc khong bat mat, nhung liec qua la biet no dang song.
     *
     * Bien do co y rat nho (3% ban kinh) va alpha toi da 46/255.
     */
    private var phaTho = 0f
    private var hoiTho: android.animation.ValueAnimator? = null
    private val butTho = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.STROKE }

    init {
        isFocusable = true
        importantForAccessibility = IMPORTANT_FOR_ACCESSIBILITY_YES
    }

    /**
     * @param matKhiKeo mau mat trong LUC DANG XOAY (muc 6.1).
     *
     * O ban sang, mat dong ho luc xoay toi hin lai gan nhu den - no lay
     * mau cua vanh dang duoc to dam, va o bang mau ngay thi vanh do rat
     * dam. Giua mot man hinh giay kem, mot dia den dot ngot la dung thu
     * keo su chu y di khoi viec nguoi dung dang lam: chon do dai.
     *
     * Nen luc xoay, mat doi sang mot sac RIENG - sang hon nen mot chut,
     * du de thay "dang o che do dat gio" ma khong hut mat.
     */
    fun datMau(mat: Int, matKhiKeo: Int, vachKhac: Int, ranh: Int, chu: Int, chuPhu: Int,
               conNhieu: Int, sapDen: Int, diNgay: Int, dangKeoMau: Int) {
        mauMat = mat; mauMatKhiKeo = matKhiKeo; mauVachKhac = vachKhac; mauRanh = ranh
        mauChu = chu; mauChuPhu = chuPhu
        mauConNhieu = conNhieu; mauSapDen = sapDen; mauDiNgay = diNgay
        mauDangKeo = dangKeoMau
        invalidate()
    }

    fun datFont(thuong: Typeface?, dam: Typeface?) {
        butSo.typeface = thuong; butNhan.typeface = thuong
        butGiua.typeface = dam ?: Typeface.DEFAULT_BOLD
        invalidate()
    }

    /**
     * @param conLai so phut con lai (co the le)
     * @param chay   dang dem nguoc hay dang dat gio
     * @param giua   chu o giua mat (so phut, hoac "Sắp xong")
     * @param duoi   nhan nho duoi so ("PHÚT" / "PHÚT CÒN LẠI")
     */
    fun dat(conLai: Float, chay: Boolean, giua: String, duoi: String) {
        conLaiPhut = conLai.coerceIn(0f, TOI_DA)
        val doiTrangThai = dangChay != chay
        dangChay = chay
        nhanGiua = giua; nhanDuoi = duoi
        contentDescription = "$giua $duoi"
        if (doiTrangThai) if (chay) batTho() else tatTho()
        invalidate()
    }

    private fun batTho() {
        if (hoiTho != null) return
        hoiTho = android.animation.ValueAnimator.ofFloat(0f, 1f).apply {
            duration = 4000                       // mot hoi tho
            repeatCount = android.animation.ValueAnimator.INFINITE
            repeatMode = android.animation.ValueAnimator.REVERSE
            interpolator = android.view.animation.AccelerateDecelerateInterpolator()
            addUpdateListener { phaTho = it.animatedValue as Float; invalidate() }
            start()
        }
    }

    private fun tatTho() {
        hoiTho?.cancel(); hoiTho = null
        phaTho = 0f
        invalidate()
    }

    // Man hinh tat / view roi khoi cay -> dung hoat hinh. Khong co hai dong
    // nay thi `ValueAnimator` cu chay va ve vao mot view khong con ai nhin.
    override fun onDetachedFromWindow() {
        super.onDetachedFromWindow()
        tatTho()
    }

    override fun onVisibilityChanged(changed: View, visibility: Int) {
        super.onVisibilityChanged(changed, visibility)
        if (visibility != VISIBLE) tatTho() else if (dangChay) batTho()
    }

    /** Dong bo khi so phut doi tu ngoai (chip chon nhanh). */
    fun datPhutKeo(p: Int) {
        phutKeo = p.toDouble().coerceIn(1.0, TOI_DA.toDouble())
        mocTruoc = (phutKeo / 5).toInt()
    }

    /**
     * ----- MAU DOI THEO CHANG (muc 6.1) -----
     *
     * Bon bac, khong phai ba. Bac moi o giua la mot buoc chuyen DAN tu
     * lanh sang vang trong khoang 45 -> 20 phut, thay vi nhay mot cai o
     * dung moc 45.
     *
     * Ly do: moc nhay lam mau thanh mot TIN HIEU BAO DONG - dang yen roi
     * bong doi. Chuyen dan lam mau thanh mot THUOC DO - liec vao la uoc
     * duoc con bao nhieu, ma khong co giay phut nao giat minh. Voi nguoi
     * mu thoi gian, cai can la thuoc do.
     *
     * Duoi 10 phut moi chuyen han sang cam, va o do thi dut khoat: day
     * dung la luc can biet "sap het that roi".
     */
    private fun mauChang(): Int = when {
        // Dang xoay -> mau rieng. Xem ghi chu `dh_dang_keo` trong colors.xml.
        dangKeo -> mauDangKeo
        !dangChay -> mauConNhieu
        conLaiPhut > 45f -> mauConNhieu
        conLaiPhut > 20f -> tron(mauConNhieu, mauSapDen, (45f - conLaiPhut) / 25f)
        conLaiPhut > 10f -> mauSapDen
        else -> mauDiNgay
    }

    /** Tron hai mau theo ty le 0..1, tung kenh mot. */
    private fun tron(a: Int, b: Int, t: Float): Int {
        val k = t.coerceIn(0f, 1f)
        fun lerp(x: Int, y: Int) = (x + (y - x) * k).toInt().coerceIn(0, 255)
        return Color.rgb(
            lerp(Color.red(a), Color.red(b)),
            lerp(Color.green(a), Color.green(b)),
            lerp(Color.blue(a), Color.blue(b)))
    }

    override fun onMeasure(w: Int, h: Int) {
        val rong = MeasureSpec.getSize(w)
        val cao = if (MeasureSpec.getMode(h) == MeasureSpec.UNSPECIFIED) rong
                  else min(rong, MeasureSpec.getSize(h))
        setMeasuredDimension(rong, cao)
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        val d = min(width, height).toFloat()
        if (d <= 0f) return
        val cx = width / 2f
        val cy = height / 2f
        val rNgoai = d / 2f - d * 0.02f
        val dayVanh = d * 0.096f                 // be day cua vanh khac vach
        val rVanh = rNgoai - dayVanh / 2f - d * 0.022f
        val rMat = rVanh - dayVanh / 2f - d * 0.012f
        val mau = mauChang()

        // 1. Vanh nen (phan chua chon)
        butVanh.color = mauRanh
        butVanh.strokeWidth = dayVanh
        canvas.drawCircle(cx, cy, rVanh, butVanh)

        // 2. Phan da chon - gio dau
        val gioDau = min(conLaiPhut, 60f)
        oVanh.set(cx - rVanh, cy - rVanh, cx + rVanh, cy + rVanh)
        if (gioDau > 0f) {
            butVanh.color = mau
            canvas.drawArc(oVanh, -90f, 360f * gioDau / 60f, false, butVanh)
        }

        // 3. Vach khac - ve DE LEN vanh bang mau nen, trong nhu khac vao
        for (i in 0 until SO_VACH) {
            val goc = Math.toRadians(i * (360.0 / SO_VACH) - 90.0)
            val moc5 = i % (SO_VACH / 12) == 0
            val dai = if (moc5) dayVanh * 0.62f else dayVanh * 0.40f
            butVach.color = mauVachKhac
            butVach.strokeWidth = if (moc5) d * 0.0095f else d * 0.006f
            val r1 = rVanh + dayVanh / 2f - d * 0.004f
            val r2 = r1 - dai
            canvas.drawLine(
                cx + r1 * cos(goc).toFloat(), cy + r1 * sin(goc).toFloat(),
                cx + r2 * cos(goc).toFloat(), cy + r2 * sin(goc).toFloat(), butVach)
        }

        // 3b. Nhip tho - mot quang sang rat mo quanh vanh, chi khi dang chay.
        if (dangChay && hoiTho != null) {
            butTho.color = mau
            butTho.alpha = (18 + 28 * phaTho).toInt()
            butTho.strokeWidth = dayVanh * (0.55f + 0.30f * phaTho)
            canvas.drawCircle(cx, cy, rVanh + dayVanh * (0.62f + 0.03f * phaTho), butTho)
            butTho.alpha = 255
        }

        // 4. Gio thu hai: vanh mong ben ngoai
        val gioHai = (conLaiPhut - 60f).coerceAtLeast(0f)
        if (gioHai > 0f) {
            val rHai = rNgoai - d * 0.012f
            butVanh.strokeWidth = d * 0.022f
            butVanh.color = mauRanh
            canvas.drawCircle(cx, cy, rHai, butVanh)
            butVanh.color = mau
            butVanh.strokeCap = Paint.Cap.ROUND
            oVanh.set(cx - rHai, cy - rHai, cx + rHai, cy + rHai)
            canvas.drawArc(oVanh, -90f, 360f * gioHai / 60f, false, butVanh)
            butVanh.strokeCap = Paint.Cap.BUTT
        }

        // 5. Mat tron o giua - doi mau trong luc dang xoay (muc 6.1)
        butMat.color = if (dangKeo) mauMatKhiKeo else mauMat
        canvas.drawCircle(cx, cy, rMat, butMat)

        // 6. Bon moc gio tren mat - CHI 15 / 30 / 45 / 60
        butSo.color = mauChuPhu
        butSo.textSize = d * 0.052f
        for ((phut, nhan) in MOC) {
            val goc = Math.toRadians(phut / 60.0 * 360.0 - 90.0)
            val rr = rMat - d * 0.055f
            canvas.drawText(nhan,
                cx + rr * cos(goc).toFloat(),
                cy + rr * sin(goc).toFloat() - (butSo.descent() + butSo.ascent()) / 2, butSo)
        }

        // 7. So phut o giua
        //
        // ----- "Sap xong" khong duoc de len moc 15 va 45 (muc 6.2) -----
        //
        // Ban truoc dung MOT nguong duy nhat: dai hon 3 ky tu thi thu nho
        // con 0,115d. Nhung "Sắp xong" la tam ky tu, va o co chu 0,115d no
        // rong hon khoang trong giua hai moc 15 (ben phai) va 45 (ben
        // trai) - hai con so do bi chu de len, dung vao phut cuoi cung, la
        // luc nguoi dung nhin man hinh nhieu nhat.
        //
        // Gio co chu tinh theo CHO CON TRONG THAT: do be ngang chu roi thu
        // cho toi khi no lot giua hai moc, tru mot khoang ho hai ben.
        //
        // Va khi la chu (khong phai so phut) thi BO LUON dong nhan duoi.
        // Ban cu ghi "Sắp xong" roi ngay duoi lai ghi "CÒN LẠI" - hai dong
        // noi cung mot y, va chinh dong thu hai day chu xuong cham vanh.
        val laChu = nhanGiua.length > 3
        butGiua.color = mauChu
        if (laChu) {
            // Cho trong giua hai moc 15 va 45, tru ho hai ben.
            val choTrong = (rMat - d * 0.055f) * 2f - d * 0.10f
            var co = d * 0.105f
            butGiua.textSize = co
            while (butGiua.measureText(nhanGiua) > choTrong && co > d * 0.055f) {
                co -= d * 0.004f
                butGiua.textSize = co
            }
            // Khong co dong nhan duoi -> can giua theo chieu doc cho can.
            canvas.drawText(nhanGiua, cx, cy - (butGiua.descent() + butGiua.ascent()) / 2, butGiua)
        } else {
            butGiua.textSize = d * 0.215f
            canvas.drawText(nhanGiua, cx, cy + butGiua.textSize * 0.33f, butGiua)
            butNhan.color = mauChuPhu
            butNhan.textSize = d * 0.048f
            butNhan.letterSpacing = 0.14f
            canvas.drawText(nhanDuoi, cx, cy + butGiua.textSize * 0.33f + d * 0.085f, butNhan)
        }

        // 8. Tay cam o dau vanh - chi hien khi dang dat gio
        if ((choKeo && !dangChay) || (dangChay && choKeoKhiChay)) {
            val goc = Math.toRadians(gioDau / 60.0 * 360.0 - 90.0)
            val tx = cx + rVanh * cos(goc).toFloat()
            val ty = cy + rVanh * sin(goc).toFloat()
            val rTay = dayVanh * 0.62f
            butTay.color = mauMat
            canvas.drawCircle(tx, ty, rTay, butTay)
            butTay.color = mau
            butTay.style = Paint.Style.STROKE
            butTay.strokeWidth = d * 0.011f
            canvas.drawCircle(tx, ty, rTay, butTay)
            // ----- TAY NAM: HAI VACH NGAN, KHONG PHAI MOT MUI TEN -----
            //
            // Ban truoc ve mot "mui ten" bang hai diem, va no sai ba cho:
            //
            //   1. `val a = Math.toRadians(gioDau / 60.0 * 360.0)` thieu
            //      `- 90.0` ma `goc` o tren co. Hai goc lech nhau dung mot
            //      phan tu vong, nen hinh ve khong lien quan gi toi huong
            //      cua tay nam.
            //   2. `- mui * sin(a).toFloat() * 0f` - nhan voi KHONG. Mot
            //      so hang chet, gan nhu chac chan la ma sot lai.
            //   3. Hai diem do khong doi xung qua tam, nen ke ca khi goc
            //      dung thi no van ra mot gach xien lech chu khong phai
            //      mui ten.
            //
            // Thay bang hai vach ngan song song, vuong goc voi chieu keo -
            // dung kieu tay nam cua mot thanh truot. Ve theo vector ban
            // kinh va vector tiep tuyen nen DUNG O MOI GOC, khong co cho
            // nao de lech nua.
            val bkx = cos(goc).toFloat()          // huong ban kinh
            val bky = sin(goc).toFloat()
            val ttx = -sin(goc).toFloat()         // huong tiep tuyen
            val tty = cos(goc).toFloat()
            val nua = rTay * 0.40f                // nua chieu dai mot vach
            val lech = rTay * 0.30f               // khoang cach hai vach
            butTay.strokeWidth = d * 0.008f
            butTay.strokeCap = Paint.Cap.ROUND
            for (k in intArrayOf(-1, 1)) {
                val ox = tx + ttx * lech * k
                val oy = ty + tty * lech * k
                canvas.drawLine(ox - bkx * nua, oy - bky * nua,
                                ox + bkx * nua, oy + bky * nua, butTay)
            }
            butTay.strokeCap = Paint.Cap.BUTT
            butTay.style = Paint.Style.FILL
        }
    }

    // ---------------------------------------------------------------
    // Keo de dat gio
    // ---------------------------------------------------------------

    /** 0 do o dinh, tang theo chieu kim dong ho. */
    private fun gocCua(x: Float, y: Float): Double {
        val a = Math.toDegrees(atan2((y - height / 2f).toDouble(), (x - width / 2f).toDouble())) + 90.0
        return (a + 360.0) % 360.0
    }

    /** Cham co roi vao VANH khong (khong phai giua mat, khong phai ngoai ria). */
    private fun chamVaoVanh(x: Float, y: Float): Boolean {
        val d = min(width, height).toFloat()
        val r = Math.hypot((x - width / 2f).toDouble(), (y - height / 2f).toDouble()).toFloat()
        val rNgoai = d / 2f - d * 0.02f
        val dayVanh = d * 0.096f
        val rVanh = rNgoai - dayVanh / 2f - d * 0.022f
        // Rong hon be day that mot chut moi cham trung duoc bang ngon tay.
        return abs(r - rVanh) <= dayVanh * 1.15f
    }

    override fun onTouchEvent(e: MotionEvent): Boolean {
        if (!isEnabled) return super.onTouchEvent(e)
        // Dang dat gio: keo o dau cung duoc. Dang chay: CHI tren vanh, va
        // chi keo dai ra - xem ghi chu o `choKeoKhiChay`.
        val duocKeo = if (dangChay) choKeoKhiChay else choKeo
        if (!duocKeo) return super.onTouchEvent(e)

        when (e.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                if (dangChay && !chamVaoVanh(e.x, e.y)) return super.onTouchEvent(e)
                parent?.requestDisallowInterceptTouchEvent(true)
                dangKeo = true
                val g = gocCua(e.x, e.y)
                if (!dangChay) {
                    // Cham xuong la NHAY toi goc do trong vong hien tai: cham vao
                    // "vi tri 20 phut" thi duoc 20 phut, khong phai keo tu 25 ve.
                    val vong = if (phutKeo > 60.0) 60.0 else 0.0
                    phutKeo = (vong + g / 6.0).coerceIn(1.0, TOI_DA.toDouble())
                    bao()
                } else {
                    // Dang chay thi KHONG nhay: mot cu cham nham se cat phut
                    // xuong mot cach khong the hoan tac. Chi keo tu cho hien tai.
                    phutKeo = conLaiPhut.toDouble().coerceIn(1.0, TOI_DA.toDouble())
                    phutKeoTruoc = phutKeo.roundToInt()
                }
                gocTruoc = g
                invalidate()
                return true
            }
            MotionEvent.ACTION_MOVE -> {
                val g = gocCua(e.x, e.y)
                var delta = g - gocTruoc
                if (delta > 180) delta -= 360
                if (delta < -180) delta += 360
                gocTruoc = g
                if (dangChay) {
                    // CHI DAI RA. Keo nguoc lai khong rut ngan phien.
                    if (delta <= 0) return true
                    phutKeo = (phutKeo + delta / 6.0).coerceIn(1.0, TOI_DA.toDouble())
                    val p = phutKeo.roundToInt()
                    if (p != phutKeoTruoc) {
                        phutKeoTruoc = p
                        khiKeoQuaPhut?.invoke()     // mot nhip rung moi phut
                        khiDoiPhut?.invoke(p)
                    }
                } else {
                    phutKeo = (phutKeo + delta / 6.0).coerceIn(1.0, TOI_DA.toDouble())
                    bao()
                }
                return true
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                parent?.requestDisallowInterceptTouchEvent(false)
                dangKeo = false
                if (e.actionMasked == MotionEvent.ACTION_UP && !dangChay) {
                    phutKeo = phutKeo.roundToInt().toDouble()
                    bao()
                    performClick()
                }
                invalidate()
                return true
            }
        }
        return super.onTouchEvent(e)
    }

    override fun performClick(): Boolean = super.performClick()

    private fun bao() {
        val p = phutKeo.roundToInt().coerceIn(1, TOI_DA.toInt())
        val moc = p / 5
        if (moc != mocTruoc) {
            mocTruoc = moc
            khiQuaMoc?.invoke(p / TOI_DA)          // ty le 0..1 cho rung luy tien
        }
        khiDoiPhut?.invoke(p)
    }

    // ---------------------------------------------------------------
    // TalkBack: khong vuot vong duoc, nen co tang/giam 5 phut
    // ---------------------------------------------------------------

    override fun onInitializeAccessibilityNodeInfo(info: AccessibilityNodeInfo) {
        super.onInitializeAccessibilityNodeInfo(info)
        info.className = "android.widget.SeekBar"
        if (choKeo && !dangChay) {
            info.addAction(AccessibilityNodeInfo.AccessibilityAction.ACTION_SCROLL_FORWARD)
            info.addAction(AccessibilityNodeInfo.AccessibilityAction.ACTION_SCROLL_BACKWARD)
        }
    }

    override fun performAccessibilityAction(action: Int, args: Bundle?): Boolean {
        if (choKeo && !dangChay) {
            val buoc = when (action) {
                AccessibilityNodeInfo.ACTION_SCROLL_FORWARD -> 5
                AccessibilityNodeInfo.ACTION_SCROLL_BACKWARD -> -5
                else -> 0
            }
            if (buoc != 0) {
                phutKeo = (phutKeo.roundToInt() + buoc).toDouble().coerceIn(1.0, TOI_DA.toDouble())
                khiDoiPhut?.invoke(phutKeo.toInt())
                sendAccessibilityEvent(AccessibilityEvent.TYPE_VIEW_SELECTED)
                return true
            }
        }
        return super.performAccessibilityAction(action, args)
    }

    private companion object {
        const val TOI_DA = 120f
        /** 120 vach = moi vach 30 giay; cu 10 vach (5 phut) co mot vach dai. */
        const val SO_VACH = 120
        val MOC = listOf(60 to "60", 15 to "15", 30 to "30", 45 to "45")
    }
}
