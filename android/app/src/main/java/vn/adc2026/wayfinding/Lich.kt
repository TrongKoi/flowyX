package vn.adc2026.wayfinding

import android.content.Context

/**
 * LICH - ke hoach theo ngay, kieu Tiimo. Phan logic THUAN, khong Android.
 *
 * --------------------------------------------------------------------
 * VI SAO LICH NAM TRONG FLOWY
 * --------------------------------------------------------------------
 *
 * Mu thoi gian khong chi la "con bao nhieu phut" trong mot phien. No con
 * la khong THAY duoc ca ngay: viec nao truoc, viec nao sau, giua hai viec
 * con trong bao lau. Tiimo giai bang dong thoi gian khoi mau - moi viec la
 * mot khoi, khoi dai hon thi viec lau hon. Flowy lam cung cach.
 *
 * Va lich noi thang vao phien lam viec: "Bat dau viec nay" dien san ba o
 * y dinh thuc thi (viec gi / khi nao / o dau), gio hen = gio ket thuc,
 * uoc luong = thoi luong da dat. Tuc la moi ke hoach trong lich tu dong
 * thanh du lieu cho co che hoc "lan truoc ban uoc 30, thuc te 45".
 *
 * --------------------------------------------------------------------
 * LICH KHONG DI QUA CAU NOI
 * --------------------------------------------------------------------
 *
 * Ten ke hoach la du lieu ca nhan. Giong SoNhac va SoNhatKy, lich song
 * tron tren may. Chi khi NGUOI DUNG bam "Bat dau viec nay" thi ten do moi
 * thanh `viec_gi` cua phien - dung cot "dang lam viec gi" trong bang o
 * dau bridge.py.
 *
 * --------------------------------------------------------------------
 * NGAY LA SO NGAY TU 1970-01-01, KHONG PHAI java.time
 * --------------------------------------------------------------------
 *
 * java.time can API 26, app ho tro tu 24. Va de test tren JVM thuong thi
 * lop nay khong duoc cham Calendar/TimeZone. Nen ngay la mot so nguyen;
 * doi sang gio that (co mui gio) nam o `LichBao`.
 */
/**
 * HANG_TUAN giu lai de doc du lieu cu (cung thu voi ngay bat dau).
 * Giao dien v4 chi tao THEO_THU: nguoi dung chon cac thu cu the (T2, T5...).
 */
enum class LapLai { KHONG, HANG_NGAY, HANG_TUAN, THEO_THU }

/**
 * Muc uu tien. KHONG co "khan cap": ADHD nhin chu "khan" la thay moi viec
 * deu khan. Ba muc la du de chon mot viec lam truoc.
 */
/*
enum class UuTien(val nhan: String) {
    CAO(resources.getString(R.string.nh_uu_tien_cao)),
    VUA(resources.getString(R.string.nh_uu_tien_vua)),
    THAP(resources.getString(R.string.nh_uu_tien_thap)
}
*/

enum class UuTien(val resID: Int) {
    CAO(R.string.nh_uu_tien_cao),
    VUA(R.string.nh_uu_tien_vua),
    THAP(R.string.nh_uu_tien_thap)
}

data class KeHoach(
    val id: String,
    val ten: String,
    val emoji: String = "📝",
    /** 0..4, chi so vao bang mau buoc_1..buoc_5. */
    val mau: Int = 0,
    /** Ngay bat dau (so ngay tu 1970-01-01). */
    val ngay: Long,
    /** Phut tinh tu nua dem. */
    val batDau: Int,
    /** Phut. */
    val thoiLuong: Int = 30,
    val lapLai: LapLai = LapLai.KHONG,
    /** Nhac truoc bao nhieu phut. 0 = dung gio. */
    val nhacTruoc: List<Int> = listOf(15, 0),
    val oDau: String? = null,
    /** Chi dung khi lapLai = THEO_THU. 0 = Thu Hai ... 6 = Chu Nhat. */
    val thuLap: Set<Int> = emptySet(),
    val uuTien: UuTien = UuTien.VUA,
    /**
     * Ghim len dau danh sach (vuot phai). Khac uu tien: uu tien noi viec
     * nay QUAN TRONG the nao, ghim chi noi "hom nay toi muon nhin thay no
     * truoc". Mot viec uu tien Thap van ghim duoc.
     */
    val ghim: Boolean = false,
) {
    val ketThuc: Int get() = batDau + thoiLuong
}

/** Mot lan nhac cu the. `phutTuyetDoi` = ngay * 1440 + phut, gio dia phuong. */
data class LanNhac(
    val keHoach: KeHoach,
    /** Ngay cua LAN dien ra (khong phai ngay nhac). */
    val ngayDienRa: Long,
    val truoc: Int,
    val phutTuyetDoi: Long,
)

object Lich {

    /**
     * So ky tu it nhat cua ten mot ke hoach.
     *
     * v5 ha tu 3 xuong 1. Ban cu bao loi khi go "b" - nhung "b" co the la
     * ca mot viec ("bơi"), va quan trong hon: BAT nguoi dung go them chu
     * de "du dai" la mot rao can vo nghia dung o buoc tao viec, dung luc
     * ho dang co gang bat dau. Ten rong van khong luu duoc, vi luc do
     * khong con gi de nhan ra ca.
     */
    const val MIN_KY_TU = 1

    /** Nhac truoc lau nhat app cho chon: 1 ngay. */
    const val NHAC_XA_NHAT = 24 * 60

    val MUC_NHAC = listOf(0, 5, 15, 30, 60, 24 * 60)

    /*
     * Viet Comparator TUONG MINH thay vi compareBy(vararg): ban vararg trong
     * kotlin-stdlib dung invokedynamic, ma dx (duong build khong Gradle)
     * khong dich duoc cho minSdk 24. Ket qua sap xep y het.
     */
    /**
     * Viec ghim luon len dau, roi moi den thu tu thuong.
     *
     * Hai bo sap xep GHEP duoi day cung phai viet tay, khong dung ham
     * ghep comparator cua stdlib: ham do CUNG sinh invokedynamic va dx
     * bao "invalid opcode ba" y het ban vararg. Loi chi lo ra o buoc DEX,
     * sau khi Kotlin da dich xong - nen de nham la mat ca mot vong build
     * day du moi biet.
     */
    private val GHIM_TRUOC = Comparator<KeHoach> { a, b ->
        if (a.ghim != b.ghim) (if (a.ghim) -1 else 1) else 0
    }

    private val THEO_GIO = Comparator<KeHoach> { a, b ->
        if (a.batDau != b.batDau) a.batDau.compareTo(b.batDau) else a.ten.compareTo(b.ten)
    }
    private val THEO_UU_TIEN = Comparator<KeHoach> { a, b ->
        when {
            a.uuTien != b.uuTien -> a.uuTien.ordinal.compareTo(b.uuTien.ordinal)
            else -> THEO_GIO.compare(a, b)
        }
    }

    /** GHIM_TRUOC roi THEO_GIO. */
    private val GHIM_ROI_GIO = Comparator<KeHoach> { a, b ->
        val g = GHIM_TRUOC.compare(a, b)
        if (g != 0) g else THEO_GIO.compare(a, b)
    }

    /** GHIM_TRUOC roi THEO_UU_TIEN. */
    private val GHIM_ROI_UU_TIEN = Comparator<KeHoach> { a, b ->
        val g = GHIM_TRUOC.compare(a, b)
        if (g != 0) g else THEO_UU_TIEN.compare(a, b)
    }

    /** Nhac som nhat cho phep khi nguoi dung tu nhap: 7 ngay. */
    const val NHAC_TUY_CHON_TOI_DA = 7 * 24 * 60
    val MUC_THOI_LUONG = listOf(15, 30, 45, 60, 90)
    val EMOJI = listOf("📝", "📚", "💻", "🧹", "🍳", "🏃", "💊", "🛒", "📞", "🚿", "😴", "🎧")

    /** Ke hoach co dien ra vao `ngay` khong. */
    fun coTrongNgay(kh: KeHoach, ngay: Long): Boolean = when (kh.lapLai) {
        LapLai.KHONG -> ngay == kh.ngay
        LapLai.HANG_NGAY -> ngay >= kh.ngay
        LapLai.HANG_TUAN -> ngay >= kh.ngay && (ngay - kh.ngay) % 7 == 0L
        LapLai.THEO_THU -> ngay >= kh.ngay &&
            thu(ngay) in (kh.thuLap.ifEmpty { setOf(thu(kh.ngay)) })
    }

    /** Sap theo gio, cung gio thi uu tien cao len truoc. */
    fun trongNgay(ds: List<KeHoach>, ngay: Long): List<KeHoach> =
        ds.filter { coTrongNgay(it, ngay) }.sortedWith(GHIM_ROI_GIO)

    /**
     * Cac lan nhac SAP TOI, sap theo thoi gian.
     *
     * Chi xet `soNgay` ngay toi va lay toi da `toiDa` lan: AlarmManager va
     * iOS deu gioi han so chuong dat cung luc. Moi lan mot chuong reo, app
     * tinh lai danh sach - nen ke hoach lap lai van reo mai.
     */
    fun lanNhacToi(ds: List<KeHoach>, bayGio: Long, soNgay: Int = 8,
                   toiDa: Int = 48): List<LanNhac> {
        val homNay = Math.floorDiv(bayGio, 1440L)
        val het = bayGio + soNgay * 1440L
        val ra = mutableListOf<LanNhac>()
        // Bat dau tu hom nay; nhac truoc toi da 1 ngay nen xet them ngay mai
        // la du de khong sot lan nao trong khoang [bayGio, het].
        // Nhac truoc co the toi 7 ngay: xet them bay nhieu ngay phia sau.
        val xaNhat = ds.flatMap { it.nhacTruoc }.maxOrNull() ?: 0
        val ngayThem = (xaNhat + 1439) / 1440
        for (ngay in homNay..(homNay + soNgay + ngayThem + 1)) {
            for (kh in ds) {
                if (!coTrongNgay(kh, ngay)) continue
                for (truoc in kh.nhacTruoc.distinct()) {
                    val luc = ngay * 1440L + kh.batDau - truoc
                    if (luc > bayGio && luc <= het) ra += LanNhac(kh, ngay, truoc, luc)
                }
            }
        }
        return ra.sortedBy { it.phutTuyetDoi }.take(toiDa)
    }

    /**
     * Ke hoach dang dien ra hoac sap toi HOM NAY, chua danh dau xong.
     * Dang dien ra uu tien hon sap toi.
     */
    fun tiepTheo(ds: List<KeHoach>, bayGio: Long, daXong: Set<String>): KeHoach? {
        val ngay = Math.floorDiv(bayGio, 1440L)
        val phut = (bayGio - ngay * 1440L).toInt()
        return trongNgay(ds, ngay)
            .filter { khoaXong(it.id, ngay) !in daXong }
            .firstOrNull { it.ketThuc > phut }
    }

    fun khoaXong(id: String, ngay: Long) = "$id|$ngay"

    // ---------------------------------------------------------------
    // Cau chu - bon quy tac o FLOWY_THIET_KE muc 4.4
    // ---------------------------------------------------------------

    /**
     * Noi dung thong bao. Moi cau ket thuc bang THOI DIEM cu the, khong
     * phai khoang thoi gian troi noi - neo vao dong ho (muc 3.1).
     */
    fun cauNhac(ln: LanNhac): String {
        val kh = ln.keHoach
        val gio = gioPhut(kh.batDau)
        return when {
            ln.truoc == 0 -> "Đến giờ rồi: ${kh.ten}."
            ln.truoc >= 24 * 60 -> "Ngày mai lúc $gio: ${kh.ten}."
            else -> "Còn ${moTaPhut(ln.truoc)} nữa, lúc $gio: ${kh.ten}."
        }
    }

    fun moTaNhac(truoc: Int): String = when {
        truoc == 0 -> "Đúng giờ"
        truoc % 1440 == 0 -> "${truoc / 1440} ngày trước"
        truoc % 60 == 0 -> "${truoc / 60} giờ trước"
        else -> "${moTaPhut(truoc)} trước"
    }

    fun moTaPhut(phut: Int): String = when {
        phut < 60 -> "$phut phút"
        phut % 60 == 0 -> "${phut / 60} giờ"
        else -> "${phut / 60} giờ ${phut % 60} phút"
    }

    fun moTaLapLai(l: LapLai): Int = when (l) {
        LapLai.KHONG -> R.string.nh_lap_lai_khong_lap
        LapLai.HANG_NGAY -> R.string.nh_lap_lai_hang_ngay
        LapLai.HANG_TUAN -> R.string.nh_lap_lai_hang_tuan
        LapLai.THEO_THU -> R.string.nh_lap_lai_theo_thu
    }

    /** "T2, T5 hằng tuần" - doc duoc ngay, khong can nho quy uoc. */
    fun moTaLapLai(kh: KeHoach, ctx: Context): String = when (kh.lapLai) {
        LapLai.THEO_THU -> {
            val thu = kh.thuLap.ifEmpty { setOf(thu(kh.ngay)) }
            if (thu.size == 7) "Hằng ngày"
            else thu.sorted().joinToString(", ") { ctx.getString(TEN_THU_NGAN[it]) } + " hằng tuần"
        }
        LapLai.HANG_TUAN -> ctx.getString(TEN_THU_NGAN[thu(kh.ngay)]) + " hằng tuần"
        else -> ctx.getString(moTaLapLai(kh.lapLai))
    }

    /** Uu tien cao truoc, roi theo gio. Dung cho phan tom tat tab Ke hoach. */
    fun theoUuTien(ds: List<KeHoach>): List<KeHoach> =
        ds.sortedWith(GHIM_ROI_UU_TIEN)

    /**
     * Doi gio bat dau / ket thuc thanh thoi luong. Ket thuc truoc hoac bang
     * bat dau nghia la qua nua dem (vd 23:00 -> 01:00 = 120 phut).
     */
    fun thoiLuongGiua(batDau: Int, ketThuc: Int): Int {
        val d = ketThuc - batDau
        return if (d > 0) d else d + 1440
    }

    fun gioPhut(phut: Int): String {
        val p = ((phut % 1440) + 1440) % 1440
        return String.format(java.util.Locale.US, "%02d:%02d", p / 60, p % 60)
    }

    // ---------------------------------------------------------------
    // Ngay <-> nam/thang/ngay (thuat toan civil cua Howard Hinnant)
    // ---------------------------------------------------------------

    fun tuNgayThang(nam: Int, thang: Int, ngay: Int): Long {
        val y = if (thang <= 2) nam - 1 else nam
        val era = Math.floorDiv(y, 400)
        val yoe = y - era * 400
        val mp = (thang + 9) % 12
        val doy = (153 * mp + 2) / 5 + ngay - 1
        val doe = yoe * 365 + yoe / 4 - yoe / 100 + doy
        return era * 146097L + doe - 719468L
    }

    /** Tra (nam, thang 1..12, ngay 1..31). */
    fun ngayThang(soNgay: Long): Triple<Int, Int, Int> {
        val z = soNgay + 719468L
        val era = Math.floorDiv(z, 146097L)
        val doe = z - era * 146097L
        val yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365
        val doy = doe - (365 * yoe + yoe / 4 - yoe / 100)
        val mp = (5 * doy + 2) / 153
        val d = (doy - (153 * mp + 2) / 5 + 1).toInt()
        val m = (if (mp < 10) mp + 3 else mp - 9).toInt()
        val y = (yoe + era * 400 + if (m <= 2) 1 else 0).toInt()
        return Triple(y, m, d)
    }

    /** 0 = Thu Hai ... 6 = Chu Nhat. 1970-01-01 la Thu Nam. */
    fun thu(soNgay: Long): Int = Math.floorMod(soNgay + 3, 7L).toInt()

    /** Thu Hai cua tuan chua `soNgay`. */
    fun dauTuan(soNgay: Long): Long = soNgay - thu(soNgay)

    val TEN_THU_NGAN: List<Int> =
        listOf(
            R.string.nh_thu_hai_short,
            R.string.nh_thu_ba_short,
            R.string.nh_thu_tu_short,
            R.string.nh_thu_nam_short,
            R.string.nh_thu_sau_short,
            R.string.nh_thu_bay_short,
            R.string.nh_chu_nhat_short
        )
    val TEN_THU: List<Int> =
        listOf(
            R.string.nh_thu_hai_full,
            R.string.nh_thu_ba_full,
            R.string.nh_thu_tu_full,
            R.string.nh_thu_nam_full,
            R.string.nh_thu_sau_full,
            R.string.nh_thu_bay_full,
            R.string.nh_chu_nhat_full
        )

    fun tenNgay(soNgay: Long, homNay: Long, ctx: Context): String {
        val (_, m, d) = ngayThang(soNgay)
        val ten = when (soNgay - homNay) {
            0L -> ctx.getString(R.string.nh_ngay_hom_nay)
            1L -> ctx.getString(R.string.nh_ngay_mai)
            -1L -> ctx.getString(R.string.nh_ngay_hom_qua)
            else -> ctx.getString(TEN_THU[thu(soNgay)])
        }
        return "$ten, $d/$m"
    }
}
