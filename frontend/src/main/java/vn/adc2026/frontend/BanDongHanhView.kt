package vn.adc2026.frontend

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import android.util.AttributeSet
import android.view.View
import kotlin.math.min

/**
 * BAN DONG HANH - mot khuon mat don gian doi theo su kien.
 *
 * --------------------------------------------------------------------
 * RANG BUOC CUNG: KHONG CO TRANG THAI TIEU CUC
 * --------------------------------------------------------------------
 *
 * Khong co net mat buon, that vong, hay trach moc - ke ca khi nguoi
 * dung tre gio, di lac, hay bo do chuyen di.
 *
 * Day khong phai lua chon ve giong dieu. ADHD thuong di kem NHAY CAM
 * VOI SU TU CHOI / THAT BAI: mot nhan vat to ra that vong se lam nguoi
 * dung TRANH MO APP, va luc do moi tinh nang khac deu thanh vo dung.
 *
 * Bon trang thai o duoi, ba tich cuc mot trung tinh. Trang thai xau
 * nhat co the xay ra la BINH_THUONG - tuc la khong khen, chu khong bao
 * gio la che.
 *
 * Phia Python co test khoa dieu nay (`test_dongvien.py`).
 *
 * --------------------------------------------------------------------
 * VE BANG Canvas, KHONG DUNG ANH
 * --------------------------------------------------------------------
 *
 * Mot khuon mat gom hai hinh tron va mot duong cong. Ve bang code thi
 * khong phai them tai nguyen anh cho tung trang thai, khong phai lo
 * nhieu do phan giai man hinh, va doi net mat chi la doi vai con so.
 *
 * --------------------------------------------------------------------
 * TINH, NHUNG KHONG DUNG YEN: TU THE DOI THUA VA ROI RAC
 * --------------------------------------------------------------------
 *
 * Xem docs/NHAN_VAT_BRIEF.md muc 2.6. Nhan vat TU LAM viec cua no, va
 * doi tu the moi 3-8 phut (8-15 phut khi nguoi dung dang tap trung).
 *
 * Khong phai hoat hinh chay lien tuc: chuyen dong lap lai trong tam
 * nhin ngoai vi la nguon phan tam, ma man hinh nay nam ngay canh cong
 * viec nguoi dung dang lam. Doi tu the la mot buoc NHAY roi lai dung
 * yen, giong mot nguoi ngoi canh doi tu the.
 *
 * Khi nao doi la do `dongvien.BoDoiTuThe` ben Python quyet dinh; lop
 * nay chi ve cai duoc bao.
 *
 * --------------------------------------------------------------------
 * CHI TUONG TAC KHI DUOC CHAM
 * --------------------------------------------------------------------
 *
 * Muc 2.4 cua ban mo ta: nhan vat KHONG BAO GIO chu dong bat chuyen.
 * Cu cham la loi moi DUY NHAT de app len tieng voi mot cau hoi.
 *
 * Phan biet hai thu de lan:
 *
 *     doi net mat  - thu dong, phan anh su kien, khong doi hoi gi
 *     tuong tac    - CHI khi duoc cham, va no doi mot cau tra loi
 *
 * Nen lop nay co [onCham] nhung KHONG co duong nao de tu goi len tren.
 */
class BanDongHanhView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyle: Int = 0,
) : View(context, attrs, defStyle) {

    /** Khop `dongvien.TrangThai` ben Python. */
    enum class TrangThai { BINH_THUONG, VUI, THONG_CAM, TU_HAO }

    private var trangThai: TrangThai = TrangThai.BINH_THUONG

    /**
     * Tu the "dang ban" hien tai, 0 den [SO_TU_THE] - 1.
     *
     * Bon tu the duoi la BAN TAM: bon hinh ve don gian de he thong chay
     * duoc dau-cuoi truoc khi co tranh that. Ban ve tay cua nguoi ve se
     * thay cho chung, va chi can thay phan `veTuThe` - phan con lai cua
     * lop nay khong doi.
     */
    private var tuThe: Int = 0

    /**
     * Goi khi nguoi dung cham vao nhan vat.
     *
     * Ben goi dat cai nay. Lop nay khong tu goi len tren bao gio -
     * xem muc 2.4 o phan dau file.
     */
    var onCham: (() -> Unit)? = null

    init {
        isClickable = true
        isFocusable = true
        contentDescription = moTa()
        setOnClickListener { onCham?.invoke() }
    }

    private val mat = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.FILL
    }
    private val net = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#121212")
        style = Paint.Style.STROKE
        strokeCap = Paint.Cap.ROUND
    }
    private val duong = Path()
    private val o = RectF()

    /**
     * Doi trang thai.
     *
     * Nhan chuoi tu goi tin cua cau noi (`ban`). Chuoi la thi giu
     * nguyen trang thai cu - KHONG roi ve mac dinh: mot goi tin hong
     * khong co nghia la nguoi dung vua lam gi sai.
     */
    fun dat(ten: String?) {
        val moi = when (ten) {
            "vui" -> TrangThai.VUI
            "thong_cam" -> TrangThai.THONG_CAM
            "tu_hao" -> TrangThai.TU_HAO
            "binh_thuong" -> TrangThai.BINH_THUONG
            else -> return
        }
        if (moi == trangThai) return
        trangThai = moi
        contentDescription = moTa()
        invalidate()
    }

    /**
     * Doi tu the "dang ban".
     *
     * So ngoai khoang thi bo qua: mot goi tin hong khong duoc lam nhan
     * vat bien mat.
     */
    fun datTuThe(n: Int) {
        val moi = ((n % SO_TU_THE) + SO_TU_THE) % SO_TU_THE
        if (moi == tuThe) return
        tuThe = moi
        invalidate()
    }

    /**
     * Nhan cho TalkBack.
     *
     * Van co, du day la thanh phan thuan thi giac: hai che do khong
     * loai tru nhau, nguoi khiem thi van co the bat che do nhac gio.
     * Mot hinh khong co nhan la mot khoang trong voi ho.
     */
    private fun moTa(): String = when (trangThai) {
        TrangThai.VUI -> "Bạn đồng hành đang vui"
        TrangThai.TU_HAO -> "Bạn đồng hành đang tự hào"
        TrangThai.THONG_CAM -> "Bạn đồng hành đang ở cạnh bạn"
        TrangThai.BINH_THUONG -> "Bạn đồng hành"
    }

    private fun mauMat(): Int = when (trangThai) {
        TrangThai.TU_HAO -> Color.parseColor("#E0A030")   // ho phach
        TrangThai.VUI -> Color.parseColor("#7BC67B")      // xanh la diu
        TrangThai.THONG_CAM -> Color.parseColor("#8FA8D8")  // xanh lam nhat
        TrangThai.BINH_THUONG -> Color.parseColor("#6E6E6E")
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)

        if (width <= 0 || height <= 0) return

        // Chua cho cho hinh tu the ben phai khuon mat. Khong chua thi
        // hinh do bi cat mat o nhung man hinh hep - va loi do chi lo ra
        // tren may that, khong lo ra trong ban xem truoc.
        val d = min(width * PHAN_KHUON_MAT, height.toFloat())
        if (d <= 0f) return

        val cx = width * PHAN_KHUON_MAT / 2f
        val cy = height / 2f
        val r = d / 2f * 0.9f

        mat.color = mauMat()
        canvas.drawCircle(cx, cy, r, mat)

        net.strokeWidth = r * 0.10f

        // Hai mat. THONG_CAM ve mat lim thanh gach ngang - cu chi diu
        // xuong, khong phai cu chi buon.
        val mx = r * 0.36f
        val my = r * 0.25f
        val mr = r * 0.11f
        if (trangThai == TrangThai.THONG_CAM) {
            canvas.drawLine(cx - mx - mr, cy - my, cx - mx + mr, cy - my, net)
            canvas.drawLine(cx + mx - mr, cy - my, cx + mx + mr, cy - my, net)
        } else {
            val cham = Paint(net).apply { style = Paint.Style.FILL }
            canvas.drawCircle(cx - mx, cy - my, mr, cham)
            canvas.drawCircle(cx + mx, cy - my, mr, cham)
        }

        // Mieng: mot cung. Do CONG thay doi theo trang thai, va no
        // KHONG BAO GIO am - cung quay xuong la net mat buon, va day la
        // thu module nay cam.
        val cong = when (trangThai) {
            TrangThai.TU_HAO -> 0.55f
            TrangThai.VUI -> 0.45f
            TrangThai.THONG_CAM -> 0.12f     // gan thang, nhe nhang
            TrangThai.BINH_THUONG -> 0.18f
        }
        val rong = r * 0.9f
        val cao = r * cong
        o.set(cx - rong / 2f, cy + r * 0.05f,
              cx + rong / 2f, cy + r * 0.05f + cao)
        duong.reset()
        duong.addArc(o, 0f, 180f)
        canvas.drawPath(duong, net)

        veTuThe(canvas, cx, cy, r)
    }

    /**
     * Ve thu nhan vat DANG LAM, canh khuon mat.
     *
     * Bon hinh don gian, doi theo [tuThe]. Y do khong phai la lam nhan
     * vat thu vi - ma nguoc lai: muc 2.5 cua ban mo ta doi no phai KEM
     * THU VI HON cong viec cua nguoi dung.
     *
     * Nen moi tu the la MOT net, tinh, khong mau sac rieng. Vua du de
     * liec thay "no van dang o do va van dang lam gi do", khong du de
     * ngoi nhin.
     *
     * Day la ban tam cho toi khi co tranh ve tay.
     */
    private fun veTuThe(canvas: Canvas, cx: Float, cy: Float, r: Float) {
        val x = cx + r * 1.15f
        val y = cy + r * 0.35f
        val d = r * 0.42f
        net.strokeWidth = r * 0.09f

        when (tuThe) {
            // doc: mot trang mo
            0 -> {
                canvas.drawLine(x - d, y - d, x - d, y + d, net)
                canvas.drawLine(x + d, y - d, x + d, y + d, net)
                canvas.drawLine(x - d, y + d, x + d, y + d, net)
            }
            // viet: mot net cheo
            1 -> canvas.drawLine(x - d, y + d, x + d, y - d, net)
            // nghi: hai net ngang chong len nhau
            2 -> {
                canvas.drawLine(x - d, y - d * 0.3f, x + d, y - d * 0.3f, net)
                canvas.drawLine(x - d, y + d * 0.5f, x + d, y + d * 0.5f, net)
            }
            // uong nuoc: mot hinh thang hep
            else -> {
                canvas.drawLine(x - d * 0.7f, y - d, x - d * 0.4f, y + d, net)
                canvas.drawLine(x + d * 0.7f, y - d, x + d * 0.4f, y + d, net)
                canvas.drawLine(x - d * 0.4f, y + d, x + d * 0.4f, y + d, net)
            }
        }
    }

    companion object {
        /** Khop `dongvien.SO_TU_THE` ben Python. */
        const val SO_TU_THE = 4

        /** Phan be ngang danh cho khuon mat; phan con lai cho tu the. */
        private const val PHAN_KHUON_MAT = 0.62f
    }
}
