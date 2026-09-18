package vn.adc2026.frontend

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.util.AttributeSet
import android.view.View
import kotlin.math.min

/**
 * Dong ho dem nguoc dang DIEN TICH MAU THU NHO DAN.
 *
 * --------------------------------------------------------------------
 * VI SAO KHONG PHAI SO GIO:PHUT
 * --------------------------------------------------------------------
 *
 * Doc "còn 6 phút" doi nguoi dung tu dung mot hinh dung ve 6 phut la
 * bao lau - ma do dung la thu nguoi mu thoi gian kho lam. Mot mang mau
 * thu nho dan thi KHONG doi phep tinh nao: mat nhin thay truc tiep
 * "con chung nay".
 *
 * Nen so van co, nhung NHO va PHU. Dien tich mau moi la trong tam thi
 * giac. Day la khac biet co chu dinh, khong phai lua chon tham my.
 *
 * --------------------------------------------------------------------
 * VE BANG Canvas, KHONG DUNG COMPOSE
 * --------------------------------------------------------------------
 *
 * Du an co y khong dung androidx nao - xem ghi chu trong
 * build.gradle.kts. Compose keo theo khoang tam dependency androidx
 * cong compiler plugin phai khop phien ban Kotlin.
 *
 * Ca lop nay chi can drawArc va drawText. Doi lay mot rui ro build
 * ngay truoc buoi demo de lay cu phap gon hon la doi khong dang.
 *
 * --------------------------------------------------------------------
 * VE MOI GIAY MOT LAN, KHONG MUOT LIEN TUC
 * --------------------------------------------------------------------
 *
 * Chuyen dong lien tuc trong tam nhin ngoai vi la nguon phan tam.
 * Nguoi dung nhin man hinh nay trong luc dang di va dang lo tre - thu
 * cuoi cung ho can la mot thu nhuc nhich khong ngung o goc mat.
 *
 * Ben goi tu quyet dinh nhip goi [dat]. Lop nay khong tu chay dong ho.
 */
class TimerTronView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyle: Int = 0,
) : View(context, attrs, defStyle) {

    enum class Muc { CON_NHIEU, SAP_DEN_GIO, DI_NGAY }

    private var tyLe: Float = 1f          // 0..1, phan thoi gian con lai
    private var nhan: String = "—"
    private var muc: Muc = Muc.CON_NHIEU

    /**
     * Chua co gio hen. Ve vanh rong va dau gach, KHONG an view di.
     *
     * Giao dien v2 giu vi tri co dinh: khoi khong bao gio co lai hay
     * bien mat giua cac lan cap nhat (UIUX_QUYET_DINH cau 3).
     */
    private var trong: Boolean = true

    // Mau mac dinh = ban toi cu. MainActivity goi [datMau] theo theme.
    private var mauConNhieu = Color.parseColor("#5B8DEF")
    private var mauSapDen = Color.parseColor("#E0A030")
    private var mauDiNgay = Color.parseColor("#D4553F")

    private val nenVanh = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeCap = Paint.Cap.BUTT
        color = Color.parseColor("#2C2C2C")
    }
    private val vanh = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeCap = Paint.Cap.ROUND
    }
    private val chu = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#E8E8E8")
        textAlign = Paint.Align.CENTER
        isFakeBoldText = true
    }
    private val chuPhu = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#A8A39A")
        textAlign = Paint.Align.CENTER
    }
    private val o = RectF()

    /** Mau theo theme sang/toi. */
    fun datMau(conNhieu: Int, sapDen: Int, diNgay: Int, ranh: Int,
               chuChinh: Int, chuPhuMau: Int) {
        mauConNhieu = conNhieu; mauSapDen = sapDen; mauDiNgay = diNgay
        nenVanh.color = ranh
        chu.color = chuChinh
        chuPhu.color = chuPhuMau
        invalidate()
    }

    /** Doi font cho so o giua. null = font he thong. */
    fun datFont(tf: android.graphics.Typeface?) {
        chu.typeface = tf
        chuPhu.typeface = tf
        invalidate()
    }

    fun dat(conLai: Float, tongCong: Float, nhan: String, muc: Muc) {
        this.tyLe = if (tongCong <= 0f) 0f else (conLai / tongCong).coerceIn(0f, 1f)
        this.nhan = nhan
        this.muc = muc
        this.trong = false
        contentDescription = moTa()
        invalidate()
    }

    fun datTrong() {
        if (trong) return
        trong = true
        tyLe = 1f
        nhan = "—"
        contentDescription = "Chưa có giờ hẹn"
        invalidate()
    }

    private fun moTa(): String = when (muc) {
        Muc.DI_NGAY -> "Cần bắt tay vào ngay. Còn $nhan phút"
        Muc.SAP_DEN_GIO -> "Sắp đến giờ. Còn $nhan phút"
        Muc.CON_NHIEU -> "Còn $nhan phút"
    }

    private fun mauVanh(): Int = when (muc) {
        Muc.DI_NGAY -> mauDiNgay
        Muc.SAP_DEN_GIO -> mauSapDen
        Muc.CON_NHIEU -> mauConNhieu
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)

        val w = width.toFloat()
        val h = height.toFloat()
        val d = min(w, h)
        if (d <= 0f) return

        // Vanh day thay vi dia dac: so o giua nam tren nen cua the, nen
        // doc duoc o ca theme sang lan toi.
        val day = d * 0.12f
        nenVanh.strokeWidth = day
        vanh.strokeWidth = day

        val cx = w / 2f
        val cy = h / 2f
        val r = d / 2f - day / 2f - d * 0.02f
        o.set(cx - r, cy - r, cx + r, cy + r)

        canvas.drawCircle(cx, cy, r, nenVanh)

        if (!trong && tyLe > 0f) {
            vanh.color = mauVanh()
            // Bat dau o dinh, thu nho theo chieu kim dong ho.
            canvas.drawArc(o, -90f, 360f * tyLe, false, vanh)
        }

        chu.textSize = d * 0.20f
        chuPhu.textSize = d * 0.09f
        val giua = cy - (chu.descent() + chu.ascent()) / 2f -
            if (trong) 0f else d * 0.04f
        canvas.drawText(nhan, cx, giua, chu)
        if (!trong) {
            canvas.drawText("phút", cx, giua + chuPhu.textSize * 1.4f, chuPhu)
        }
    }
}
