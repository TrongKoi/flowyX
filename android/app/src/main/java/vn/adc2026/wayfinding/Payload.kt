package vn.adc2026.wayfinding

/**
 * Dung va doc goi tin cua cau noi.
 *
 * Hop dong day du xem `adc_wayfinding/wayfinding/loi_chung/bridge.py`.
 * Hai ben PHAI khop nhau; lech mot ten truong la cau noi im lang hong
 * ma khong bao gi.
 *
 * --------------------------------------------------------------------
 * CO Y KHONG DUNG org.json
 * --------------------------------------------------------------------
 *
 * Lop nay phai chay duoc trong unit test JVM thuong - khong can may that
 * hay emulator. `org.json` trong unit test chi la ban rong nem
 * UnsupportedOperationException.
 *
 * Goi tin co hinh dang co dinh va rat don gian, nen tu sinh chuoi la du
 * va doi lai duoc bo test chay trong mot giay.
 *
 * --------------------------------------------------------------------
 * RANH GIOI DU LIEU - DOC TRUOC KHI THEM TRUONG
 * --------------------------------------------------------------------
 *
 * Bang trong `bridge.py` liet ke thu KHONG BAO GIO duoc di qua day:
 *
 *     duoc mang            | KHONG BAO GIO duoc mang
 *     ---------------------|---------------------------------
 *     dang lam viec gi     | nhat ky cam xuc
 *     con bao nhieu phut   | ghi chu ve trieu chung
 *     lenh hien thi        | ten cac loi nhac nguoi dung tu dat
 *     cau noi, ma rung     | so thoi luong (lich su lam viec)
 *
 * `SoNhac` va `SoNhatKy` khong duoc cham vao lop nay. Ben Python co hai
 * bai test canh gac dieu do; ben nay chua co cach kiem tu dong tuong
 * duong, nen no nam o day duoi dang mot dong chu - va o mat nguoi doc
 * review.
 *
 * `lich_su` la ngoai le CO KIEM SOAT: chi lich su cua DUNG MOT cong
 * viec dang lam, gui di roi thoi. Laptop khong ghi gi xuong dia.
 */
object Payload {

    // Lenh gui len, khop `bridge.LENH_*`.
    const val LENH_BAT_DAU = "bat_dau"
    const val LENH_XONG_BUOC = "xong_buoc"
    const val LENH_TAM_DUNG = "tam_dung"
    const val LENH_TIEP_TUC = "tiep_tuc"
    const val LENH_KET_THUC = "ket_thuc"
    const val LENH_VIEC_MOI = "viec_moi"

    /** Muc nhac. Phai khop MUC_NHAC_MOC trong bridge.py. */
    const val MUC_IT = "it"
    const val MUC_VUA = "vua"
    const val MUC_NHIEU = "nhieu"

    /** Gui gio hen am = bo gio hen. */
    const val BO_GIO_HEN = -1.0

    /**
     * Goi tin POST /update.
     *
     * Khac han ban dieu huong: khong con tu the, do sau, hay anh. Dien
     * thoai gio chi bao SU KIEN NGUOI DUNG va vai chi so may.
     *
     * @param trenManHinh app co dang o tien canh khong. Day la tin hieu
     *   phan tam CHINH, thay cho tin hieu chuyen dong cua ban dieu
     *   huong: mo app khac chinh la dinh nghia thuc te cua "bi sao
     *   nhang" o boi canh nay.
     * @param chamNhanVat nguoi dung vua cham vao nhan vat. Cu cham la
     *   loi moi DUY NHAT de app len tieng voi mot cau hoi - xem
     *   docs/NHAN_VAT_BRIEF.md muc 2.4.
     * @param lichSu so thoi luong cua CONG VIEC DANG LAM. Dien thoai so
     *   huu tep luu; laptop chi muon phan can cho lan tinh nay.
     */
    fun buildUpdate(
        tSeconds: Double,
        trenManHinh: Boolean,
        chamNhanVat: Boolean = false,
        voice: String? = null,
        lenh: String? = null,
        noiDung: String? = null,
        battery: Double? = null,
        thermal: Double? = null,
        lichSu: String? = null,
        gioHen: Double? = null,
        uocPhut: Double? = null,
        mucNhac: String? = null,
    ): String {
        val sb = StringBuilder(192)
        sb.append("{\"t\":").append(num(tSeconds))
            .append(",\"tren_man_hinh\":").append(trenManHinh)
            .append(",\"cham_nhan_vat\":").append(chamNhanVat)

        // Cau nguoi dung vua noi, da nhan dang tren may. Nhan dang phai
        // chay o day vi no can micro - laptop khong nghe duoc.
        if (voice != null) {
            sb.append(",\"voice\":\"").append(escape(voice)).append('"')
        }
        if (lenh != null) {
            sb.append(",\"lenh\":\"").append(escape(lenh)).append('"')
        }
        if (noiDung != null) {
            sb.append(",\"noi_dung\":\"").append(escape(noiDung)).append('"')
        }
        if (battery != null) sb.append(",\"battery\":").append(num(battery))
        if (thermal != null) sb.append(",\"thermal\":").append(num(thermal))

        // Da la JSON san do SoThoiLuong sinh ra - ghep thang vao, khong
        // boc lai. Boc lai la mot cho nua co the lam hong dau tieng Viet
        // trong ten cong viec.
        if (lichSu != null) sb.append(",\"lich_su\":").append(lichSu)
        if (gioHen != null) sb.append(",\"gio_hen\":").append(num(gioHen))
        if (uocPhut != null) sb.append(",\"uoc_phut\":").append(num(uocPhut))
        if (mucNhac != null) {
            sb.append(",\"muc_nhac\":\"").append(escape(mucNhac)).append('"')
        }

        sb.append('}')
        return sb.toString()
    }

    /**
     * Doc cau tra loi cua cau noi.
     *
     * Moi truong deu co gia tri mac dinh: mot goi tin hong khong duoc
     * phep dung ca phien lam viec cua nguoi dung.
     */
    fun parseReply(json: String): Reply = Reply(
        say = stringField(json, "say"),
        haptic = stringField(json, "haptic"),
        am = stringField(json, "am"),
        ban = stringField(json, "ban"),
        tuThe = intField(json, "tu_the") ?: 0,
        hoi = stringField(json, "hoi"),
        listen = boolField(json, "listen"),
        conLaiGiay = numField(json, "con_lai_giay"),
        tongGiay = numField(json, "tong_giay"),
        nhipMs = intField(json, "nhip_ms") ?: NHIP_MAC_DINH_MS,
        xongPhien = boolField(json, "xong_phien"),
        tenViec = stringField(json, "ten_viec"),
        viecGi = stringField(json, "viec_gi"),
        khiNao = stringField(json, "khi_nao"),
        oDau = stringField(json, "o_dau"),
        cacBuoc = stringArrayField(json, "cac_buoc"),
        chiSoBuoc = intField(json, "chi_so_buoc") ?: 0,
        trongPhien = boolField(json, "trong_phien"),
        tamDung = boolField(json, "tam_dung"),
        daLamGiay = numField(json, "da_lam_giay"),
        gioHen = stringField(json, "gio_hen"),
        uocPhut = numField(json, "uoc_phut"),
        goiYPhut = numField(json, "goi_y_phut"),
        mucNhac = stringField(json, "muc_nhac") ?: MUC_VUA,
    )

    /**
     * Mang chuoi, vd `"cac_buoc":["mở tệp","viết một câu"]`.
     *
     * Viet tay cung kieu voi cac ham ben canh thay vi dung org.json: ban
     * org.json trong android.jar chi la ban rong o unit test, va ca file
     * nay chu y khong phu thuoc no.
     */
    internal fun stringArrayField(json: String, key: String): List<String> {
        var i = viTriGiaTri(json, key) ?: return emptyList()
        if (i >= json.length || json[i] != '[') return emptyList()
        i++
        val ra = mutableListOf<String>()
        while (i < json.length) {
            while (i < json.length && (json[i].isWhitespace() || json[i] == ',')) i++
            if (i >= json.length || json[i] == ']') break
            if (json[i] != '"') return ra          // phan tu khong phai chuoi
            // Dung lai stringField tren mot khoa gia de doc chuoi tai day.
            val (chuoi, sau) = docChuoi(json, i) ?: return ra
            ra.add(chuoi)
            i = sau
        }
        return ra
    }

    /** Doc mot chuoi JSON bat dau o `batDau` (dau nhay). Tra chuoi va vi tri sau no. */
    private fun docChuoi(json: String, batDau: Int): Pair<String, Int>? {
        var i = batDau + 1
        val sb = StringBuilder()
        while (i < json.length) {
            val c = json[i]
            when {
                c == '\\' && i + 1 < json.length -> {
                    when (val e = json[i + 1]) {
                        'n' -> sb.append('\n')
                        't' -> sb.append('\t')
                        'r' -> sb.append('\r')
                        'u' -> if (i + 5 < json.length) {
                            sb.append(json.substring(i + 2, i + 6).toInt(16).toChar())
                            i += 4
                        }
                        else -> sb.append(e)
                    }
                    i += 2
                }
                c == '"' -> return sb.toString() to (i + 1)
                else -> { sb.append(c); i++ }
            }
        }
        return null
    }

    /** Nhip mac dinh khi goi tin thieu truong - khop `bridge.py`. */
    const val NHIP_MAC_DINH_MS = 500

    /** Lay mot truong bool o cap ngoai cung. Thieu truong -> false. */
    internal fun boolField(json: String, key: String): Boolean {
        val i = viTriGiaTri(json, key) ?: return false
        return json.startsWith("true", i)
    }

    /** Lay mot truong so. Thieu truong hoac JSON null -> null. */
    internal fun numField(json: String, key: String): Double? {
        var i = viTriGiaTri(json, key) ?: return null
        if (json.startsWith("null", i)) return null
        val dau = i
        if (i < json.length && (json[i] == '-' || json[i] == '+')) i++
        while (i < json.length && (json[i].isDigit() || json[i] == '.'
                    || json[i] == 'e' || json[i] == 'E'
                    || json[i] == '-' || json[i] == '+')) i++
        return json.substring(dau, i).toDoubleOrNull()
    }

    internal fun intField(json: String, key: String): Int? =
        numField(json, key)?.toInt()

    /**
     * Lay mot truong chuoi o cap ngoai cung. Tra ve null neu la JSON null.
     *
     * Du dung cho goi tin nay vi cac truong deu phang va do cau noi tu
     * sinh, khong phai chuoi tuy y tu nguoi dung.
     */
    internal fun stringField(json: String, key: String): String? {
        var i = viTriGiaTri(json, key) ?: return null
        if (json.startsWith("null", i)) return null
        if (json[i] != '"') return null
        i++
        val sb = StringBuilder()
        while (i < json.length) {
            val c = json[i]
            when {
                c == '\\' && i + 1 < json.length -> {
                    when (val e = json[i + 1]) {
                        'n' -> sb.append('\n')
                        't' -> sb.append('\t')
                        'r' -> sb.append('\r')
                        'u' -> {
                            if (i + 5 < json.length) {
                                sb.append(json.substring(i + 2, i + 6)
                                    .toInt(16).toChar())
                                i += 4
                            }
                        }
                        else -> sb.append(e)
                    }
                    i += 2
                }
                c == '"' -> return sb.toString()
                else -> { sb.append(c); i++ }
            }
        }
        return null
    }

    /** Vi tri ky tu dau tien cua gia tri sau `"key":`, hoac null. */
    private fun viTriGiaTri(json: String, key: String): Int? {
        val needle = "\"$key\""
        var i = json.indexOf(needle)
        if (i < 0) return null
        i += needle.length
        while (i < json.length && json[i] != ':') i++
        i++
        while (i < json.length && json[i].isWhitespace()) i++
        return if (i >= json.length) null else i
    }

    internal fun escape(s: String): String =
        s.replace("\\", "\\\\").replace("\"", "\\\"")

    /**
     * So thuc dang JSON, luon dung dau cham thap phan.
     *
     * String.format theo Locale mac dinh se sinh dau PHAY o may cai
     * tieng Viet, va goi tin thanh JSON hong. Loi nay chi lo ra tren
     * may that nen rat de bo sot.
     */
    internal fun num(v: Double): String {
        if (v.isNaN() || v.isInfinite()) return "0"
        return String.format(java.util.Locale.US, "%.3f", v)
            .trimEnd('0').trimEnd('.').ifEmpty { "0" }
    }
}

/**
 * Cau tra loi tu cau noi.
 *
 * Khop `bridge.BridgeReply`. Moi truong co mac dinh an toan.
 */
data class Reply(
    /** Cau doc len. Khac [hoi] o cho no KHONG doi cau tra loi. */
    val say: String? = null,
    val haptic: String? = null,

    /** Am ngan phat kem, khong phai giong noi. */
    val am: String? = null,

    /**
     * Net mat nhan vat: "binh_thuong", "vui", "thong_cam", "tu_hao".
     *
     * BON gia tri, BA trong so do tich cuc - khong co gia tri nao the
     * hien buon hay that vong. Xem `dongvien.py` ve ly do.
     */
    val ban: String? = null,

    /**
     * Chi so tu the "dang ban" cua nhan vat.
     *
     * Doi THUA va roi rac, khong phai hoat hinh chay lien tuc - xem
     * docs/NHAN_VAT_BRIEF.md muc 2.6.
     */
    val tuThe: Int = 0,

    /** Cau hoi DANG CHO nguoi dung tra loi. */
    val hoi: String? = null,

    /**
     * Bao dien thoai bat micro.
     *
     * Mot co ro rang thay vi de dien thoai doan tu noi dung cau noi: so
     * chuoi thi doi mot chu trong ma la hong lop nghe, ma hong im lang.
     */
    val listen: Boolean = false,

    /** Cho dong ho truc quan. null nghia la khong hien dong ho. */
    val conLaiGiay: Double? = null,
    val tongGiay: Double? = null,

    /** Nhip dien thoai NEN gui goi tin, mili giay. */
    val nhipMs: Int = Payload.NHIP_MAC_DINH_MS,

    /**
     * Phien vua ket thuc o goi tin NAY. Bat dung MOT lan.
     *
     * Dien thoai so huu so thoi luong (muc 7.3), nen no phai biet luc
     * nao mot phien xong de ghi lai thoi luong that. Khong co co nay thi
     * no phai doan tu cau noi - ma doan tu cau noi la hong ngay lan dau
     * ai do sua cau chu.
     */
    val xongPhien: Boolean = false,

    /**
     * Ten cong viec cua phien dang chay, de biet ghi so vao muc nao.
     *
     * Day la ten chinh nguoi dung vua go len, nen nhan nguoc ve khong
     * lam lo them gi.
     */
    val tenViec: String? = null,

    // ---- giao dien v2 - xem BridgeReply trong bridge.py ----
    val viecGi: String? = null,
    val khiNao: String? = null,
    val oDau: String? = null,
    val cacBuoc: List<String> = emptyList(),
    val chiSoBuoc: Int = 0,
    val trongPhien: Boolean = false,
    val tamDung: Boolean = false,
    val daLamGiay: Double? = null,
    /** "HH:MM" hoac null. */
    val gioHen: String? = null,
    val uocPhut: Double? = null,
    val goiYPhut: Double? = null,
    val mucNhac: String = Payload.MUC_VUA,
)
