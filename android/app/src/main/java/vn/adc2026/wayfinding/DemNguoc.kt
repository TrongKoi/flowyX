package vn.adc2026.wayfinding

import org.json.JSONObject

/**
 * DONG HO DEM NGUOC cho tab Focus - logic THUAN, test duoc tren JVM.
 *
 * Chi dem NGUOC, toi da 2 gio. Khong co bam gio xuoi: dem len la mot con
 * so lon dan ma khong co moc dung - dung thu nguoi mu thoi gian khong cam
 * nhan duoc. Dem nguoc cho mot DIEN TICH thu nho dan va mot diem ket thuc.
 *
 * Luu MOC KET THUC (gio he thong), khong luu "con bao nhieu giay": app bi
 * dong, may khoa man hinh, Activity dung lai - moc ket thuc van dung, va
 * so con lai luon tinh lai tu no. Khong co bo dem nao phai "chay ngam".
 */
data class DemNguoc(
    /** Tong thoi luong da dat, mili giay. */
    val tongMs: Long = 25 * 60_000L,
    /** Dang chay: gio he thong luc het. Null = chua chay hoac dang dung. */
    val ketThucLuc: Long? = null,
    /** Dang tam dung: con bao nhieu. Null = khong tam dung. */
    val conLaiKhiDungMs: Long? = null,
    /** Luc bam Bat dau lan dau, de ghi thoi luong that khi xong. */
    val batDauLuc: Long? = null,
) {
    val dangChay: Boolean get() = ketThucLuc != null
    val dangDung: Boolean get() = conLaiKhiDungMs != null
    val chuaBatDau: Boolean get() = !dangChay && !dangDung

    fun conLaiMs(bayGio: Long): Long = when {
        ketThucLuc != null -> (ketThucLuc - bayGio).coerceAtLeast(0)
        conLaiKhiDungMs != null -> conLaiKhiDungMs
        else -> tongMs
    }

    /** 0..1: phan CON LAI. 1 = day, 0 = het. Ve dien tich thu nho dan. */
    fun tyLe(bayGio: Long): Float =
        if (tongMs <= 0) 0f else (conLaiMs(bayGio).toFloat() / tongMs).coerceIn(0f, 1f)

    fun daHet(bayGio: Long): Boolean = dangChay && conLaiMs(bayGio) == 0L

    fun datThoiLuong(phut: Int): DemNguoc =
        if (!chuaBatDau) this else copy(tongMs = kep(phut) * 60_000L)

    fun batDau(bayGio: Long): DemNguoc = when {
        dangChay -> this
        dangDung -> copy(ketThucLuc = bayGio + conLaiKhiDungMs!!, conLaiKhiDungMs = null)
        else -> copy(ketThucLuc = bayGio + tongMs, batDauLuc = bayGio)
    }

    fun tamDung(bayGio: Long): DemNguoc =
        if (!dangChay) this else copy(ketThucLuc = null, conLaiKhiDungMs = conLaiMs(bayGio))

    /** Ve trang thai chua bat dau, GIU thoi luong da chon. */
    fun datLai(): DemNguoc = DemNguoc(tongMs = tongMs)

    /**
     * Them phut khi dang chay. Van giu tran 2 gio cho phan con lai, va
     * noi rong tong de vong khong "nhay" ve day.
     */
    fun themPhut(phut: Int, bayGio: Long): DemNguoc {
        if (chuaBatDau) return datThoiLuong((tongMs / 60_000L).toInt() + phut)
        val con = conLaiMs(bayGio)
        val moi = (con + phut * 60_000L).coerceAtMost(TOI_DA_PHUT * 60_000L)
        val them = moi - con
        return if (dangChay) copy(ketThucLuc = ketThucLuc!! + them, tongMs = tongMs + them)
        else copy(conLaiKhiDungMs = moi, tongMs = tongMs + them)
    }

    /** So phut da lam THAT (tru phan tam dung khong tinh duoc chinh xac -> dung tong - con lai). */
    fun daLamPhut(bayGio: Long): Double = (tongMs - conLaiMs(bayGio)) / 60_000.0

    fun toJson(): String = JSONObject()
        .put("tong", tongMs)
        .put("ket_thuc", ketThucLuc ?: JSONObject.NULL)
        .put("con_lai_dung", conLaiKhiDungMs ?: JSONObject.NULL)
        .put("bat_dau", batDauLuc ?: JSONObject.NULL)
        .toString()

    companion object {
        const val TOI_DA_PHUT = 120
        const val TOI_THIEU_PHUT = 1
        /**
         * Phim tat theo brief v5: 5 phut - 15 - 30 - 1 tieng - 2 tieng.
         * Nam moc la vua mot hang, khong phai cuon ngang. Bo 10/25/45/90:
         * moc nao cung keo duoc bang vanh, danh sach dai chi them mot lan
         * phai can nhac.
         */
        val PHIM_TAT = listOf(5, 15, 30, 60, 120)

        /** Giu ten cu cho code/test cu. */
        val NHANH = PHIM_TAT

        fun kep(phut: Int): Int = phut.coerceIn(TOI_THIEU_PHUT, TOI_DA_PHUT)

        /**
         * So PHUT de hien o giua mat dong ho - lam tron LEN, khong hien giay.
         *
         * Lam tron len de "1" nghia la "van con it nhat mot chut", va de con
         * so khong nhay ve 0 trong khi dong ho van chay. Duoi 60 giay tra ve
         * 0; man hinh doi no thanh chu "Sắp xong".
         */
        fun soPhutHien(ms: Long): Int = if (ms < 60_000L) 0 else ((ms + 59_999L) / 60_000L).toInt()

        /** "mm:ss" duoi mot gio, "h:mm:ss" tu mot gio. Lam tron LEN giay. */
        fun dinhDang(ms: Long): String {
            val giay = (ms + 999) / 1000
            val h = giay / 3600; val m = (giay % 3600) / 60; val s = giay % 60
            return if (h > 0) String.format(java.util.Locale.US, "%d:%02d:%02d", h, m, s)
                   else String.format(java.util.Locale.US, "%02d:%02d", m, s)
        }

        fun tuJson(s: String?): DemNguoc {
            if (s.isNullOrBlank()) return DemNguoc()
            return try {
                val o = JSONObject(s)
                fun l(k: String): Long? = if (o.isNull(k) || !o.has(k)) null else o.optLong(k)
                val tong = (l("tong") ?: 25 * 60_000L).coerceIn(60_000L, TOI_DA_PHUT * 60_000L * 2)
                DemNguoc(tong, l("ket_thuc"), l("con_lai_dung"), l("bat_dau"))
            } catch (_: Exception) {
                DemNguoc()
            }
        }
    }
}
