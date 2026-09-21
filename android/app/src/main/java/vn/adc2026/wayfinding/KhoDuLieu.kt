package vn.adc2026.wayfinding

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import android.util.Base64
import java.security.SecureRandom
import javax.crypto.SecretKeyFactory
import javax.crypto.spec.PBEKeySpec

/**
 * ====================================================================
 * KHO DU LIEU CUC BO (v5)
 * ====================================================================
 *
 * SQLite tren may, KHONG co may chu. Day la quyet dinh kien truc, khong
 * phai su tam bo:
 *
 *   · Toan bo thu app biet ve nguoi dung deu la du lieu suc khoe tinh
 *     than theo cach hieu cua GDPR dieu 9 (du lieu ve suc khoe) - nhat
 *     ky, cam xuc, gio nao ho khong lam duoc viec gi. Day khong phai thu
 *     nen nam tren may chu cua mot doi sinh vien.
 *   · Khong co may chu thi khong co ro ri may chu, khong co yeu cau xoa
 *     tai khoan phuc tap, khong co chi phi van hanh sau hackathon.
 *
 * Tai khoan cung nam tren may: no de KHOA APP lai (nguoi khac cam may
 * khong doc duoc nhat ky), khong phai de dong bo. Man hinh dang nhap noi
 * ro dieu nay, khong de nguoi dung tuong minh dang gui gi len may chu.
 *
 * ----- Bang -----
 *
 *   nguoi_dung : mot hang duy nhat. Mat khau luu duoi dang BAM.
 *   ke_hoach   : ke hoach + lap lai + uu tien + ghim.
 *   nhat_ky    : tieu de, noi dung, cam xuc - TAT CA da ma hoa AES-GCM.
 *   bien_ban   : bien ban cuoc hop.
 *   thoi_luong : uoc luong so voi thuc te, de hoc dan.
 *   suc_khoe   : so lieu doc tu Health Connect (neu nguoi dung cho phep).
 *
 * ----- Bam mat khau: PBKDF2-HMAC-SHA256, 210.000 vong -----
 *
 * Vi sao khong Argon2id (tot hon ve ly thuyet): Android khong co san
 * Argon2; keo them thu vien native lam APK phinh va them mot phan phu
 * thuoc phai tin. PBKDF2 nam trong thu vien chuan, va 210.000 vong la con
 * so OWASP khuyen nghi cho PBKDF2-HMAC-SHA256 (2023). Moi tai khoan mot
 * muoi ngau nhien 16 byte.
 *
 * Bam chay tren luong nen: 210.000 vong mat khoang 200-400 ms tren may
 * tam trung - du de chan do mat khau hang loat, du nhanh de khong ai thay
 * app dung hinh.
 */
class KhoDuLieu(ctx: Context) : SQLiteOpenHelper(ctx, TEN, null, PHIEN_BAN) {

    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL("""
            CREATE TABLE nguoi_dung (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                ho_ten        TEXT    NOT NULL,
                email         TEXT    NOT NULL UNIQUE,
                mat_khau_bam  TEXT    NOT NULL,
                muoi          TEXT    NOT NULL,
                so_dien_thoai TEXT,
                dong_y_dk     INTEGER NOT NULL DEFAULT 0,
                tao_luc       INTEGER NOT NULL
            )""".trimIndent())

        db.execSQL("""
            CREATE TABLE ke_hoach (
                id         TEXT    PRIMARY KEY,
                ten        TEXT    NOT NULL,
                emoji      TEXT    NOT NULL DEFAULT '',
                mau        INTEGER NOT NULL DEFAULT 0,
                ngay       INTEGER NOT NULL,
                bat_dau    INTEGER NOT NULL,
                thoi_luong INTEGER NOT NULL,
                lap_lai    TEXT    NOT NULL DEFAULT 'KHONG',
                thu_lap    TEXT    NOT NULL DEFAULT '',
                nhac_truoc TEXT    NOT NULL DEFAULT '',
                uu_tien    TEXT    NOT NULL DEFAULT 'VUA',
                ghim       INTEGER NOT NULL DEFAULT 0,
                o_dau      TEXT,
                nguon      TEXT    NOT NULL DEFAULT 'app'
            )""".trimIndent())
        db.execSQL("CREATE INDEX idx_ke_hoach_ngay ON ke_hoach(ngay)")

        // Ba cot chu deu la BAN MA base64 (AES-256-GCM, khoa o Keystore).
        db.execSQL("""
            CREATE TABLE nhat_ky (
                luc      INTEGER PRIMARY KEY,
                tieu_de  TEXT    NOT NULL DEFAULT '',
                noi_dung TEXT    NOT NULL,
                the_nao  TEXT
            )""".trimIndent())

        db.execSQL("""
            CREATE TABLE bien_ban (
                luc       INTEGER PRIMARY KEY,
                ten       TEXT    NOT NULL,
                da_chot   TEXT    NOT NULL DEFAULT '',
                viec      TEXT    NOT NULL DEFAULT '',
                tom_tat   TEXT    NOT NULL DEFAULT '',
                nguoi_du  TEXT    NOT NULL DEFAULT '',
                cau_hoi   TEXT    NOT NULL DEFAULT '',
                thoi_luong INTEGER,
                nguon     TEXT    NOT NULL DEFAULT 'tay'
            )""".trimIndent())

        db.execSQL("""
            CREATE TABLE thoi_luong (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                ten_viec TEXT    NOT NULL,
                uoc_phut REAL,
                that_phut REAL   NOT NULL,
                luc      INTEGER NOT NULL
            )""".trimIndent())
        db.execSQL("CREATE INDEX idx_thoi_luong_ten ON thoi_luong(ten_viec)")

        // Du lieu suc khoe: chi so TONG HOP theo ngay, khong luu chuoi do
        // chi tiet. Xem `SucKhoe` de biet vi sao chi giu bay ngay.
        db.execSQL("""
            CREATE TABLE suc_khoe (
                ngay        TEXT PRIMARY KEY,
                ngu_phut    INTEGER,
                buoc_chan   INTEGER,
                thu_gian_phut INTEGER,
                cang_thang  INTEGER,
                nhip_tim_nghi INTEGER,
                cap_nhat    INTEGER NOT NULL
            )""".trimIndent())
    }

    /**
     * Di tru TUNG BUOC MOT, va khong bao gio drop bang co du lieu nguoi dung.
     *
     * Moi buoc phai chay duoc doc lap va phai chiu duoc viec chay lai:
     * nguoi dung co the nhay tu ban 1 thang len ban moi nhat, hoac da
     * cai ban trung gian roi. Viet kieu `if (cu < N)` lien tiep - khong
     * dung `when` - de mot may dang o ban 1 chay qua DU moi buoc.
     */
    override fun onUpgrade(db: SQLiteDatabase, cu: Int, moi: Int) {
        // 1 -> 2: them nhip tim nghi (muc 7.2).
        //
        // `ALTER TABLE ... ADD COLUMN` giu nguyen moi hang da co, va cot
        // moi nhan NULL - dung y, vi nhung ngay do that su khong co so do
        // nay. `SucKhoe.Ngay.nhipTimNghi` la kieu co the null chinh vi vay.
        if (cu < 2) {
            db.execSQL("ALTER TABLE suc_khoe ADD COLUMN nhip_tim_nghi INTEGER")
        }
    }

    override fun onConfigure(db: SQLiteDatabase) {
        super.onConfigure(db)
        db.setForeignKeyConstraintsEnabled(true)
    }

    // ---------------------------------------------------------------
    // Tai khoan
    // ---------------------------------------------------------------

    data class NguoiDung(val id: Long, val hoTen: String, val email: String, val soDienThoai: String?)

    /** Tra ve null neu email da co. */
    fun dangKy(hoTen: String, email: String, matKhau: String, dienThoai: String?): NguoiDung? {
        val e = email.trim().lowercase()
        if (coEmail(e)) return null
        val muoi = muoiMoi()
        val v = ContentValues().apply {
            put("ho_ten", hoTen.trim())
            put("email", e)
            put("mat_khau_bam", bam(matKhau, muoi))
            put("muoi", Base64.encodeToString(muoi, Base64.NO_WRAP))
            put("so_dien_thoai", dienThoai?.trim()?.ifBlank { null })
            put("dong_y_dk", 1)
            put("tao_luc", System.currentTimeMillis())
        }
        val id = writableDatabase.insert("nguoi_dung", null, v)
        return if (id < 0) null else NguoiDung(id, hoTen.trim(), e, dienThoai)
    }

    fun coEmail(email: String): Boolean =
        readableDatabase.rawQuery("SELECT 1 FROM nguoi_dung WHERE email = ? LIMIT 1",
            arrayOf(email.trim().lowercase())).use { it.moveToFirst() }

    /** Dung mat khau thi tra ve nguoi dung, sai thi null. */
    fun dangNhap(email: String, matKhau: String): NguoiDung? {
        readableDatabase.rawQuery(
            "SELECT id, ho_ten, email, so_dien_thoai, mat_khau_bam, muoi FROM nguoi_dung WHERE email = ?",
            arrayOf(email.trim().lowercase())).use { c ->
            if (!c.moveToFirst()) return null
            val luu = c.getString(4)
            val muoi = Base64.decode(c.getString(5), Base64.NO_WRAP)
            if (!bangNhau(bam(matKhau, muoi), luu)) return null
            return NguoiDung(c.getLong(0), c.getString(1), c.getString(2), c.getString(3))
        }
    }

    fun doiMatKhau(email: String, moi: String): Boolean {
        val muoi = muoiMoi()
        val v = ContentValues().apply {
            put("mat_khau_bam", bam(moi, muoi))
            put("muoi", Base64.encodeToString(muoi, Base64.NO_WRAP))
        }
        return writableDatabase.update("nguoi_dung", v, "email = ?",
            arrayOf(email.trim().lowercase())) > 0
    }

    fun nguoiDau(): NguoiDung? =
        readableDatabase.rawQuery(
            "SELECT id, ho_ten, email, so_dien_thoai FROM nguoi_dung ORDER BY id LIMIT 1", null).use { c ->
            if (c.moveToFirst()) NguoiDung(c.getLong(0), c.getString(1), c.getString(2), c.getString(3)) else null
        }

    /** Xoa sach tai khoan va MOI du lieu - dung cho nut "Xoa tai khoan". */
    fun xoaTatCa() {
        writableDatabase.apply {
            for (b in listOf("nguoi_dung", "ke_hoach", "nhat_ky", "bien_ban", "thoi_luong", "suc_khoe")) {
                execSQL("DELETE FROM $b")
            }
        }
    }

    companion object {
        const val TEN = "flowy.db"
        const val PHIEN_BAN = 2

        /** OWASP 2023 khuyen nghi cho PBKDF2-HMAC-SHA256. */
        const val VONG = 210_000
        const val DAI_KHOA = 256

        fun muoiMoi(): ByteArray = ByteArray(16).also { SecureRandom().nextBytes(it) }

        /**
         * PBKDF2-HMAC-SHA256, roi ghi ra HEX.
         *
         * Truoc day ghi ra bang `android.util.Base64`. Trong test JVM,
         * cac lop `android.*` chi la vo rong - `encodeToString` tra ve
         * null, nen ba bai trong `XacThucTest` do vi NullPointerException
         * chu khong phai vi thuat toan sai. Bai kiem quan trong nhat
         * trong so do la "ban bam khong chua mat khau thuong", va no da
         * khong he chay lan nao.
         *
         * Hex khong dinh toi Android, chay duoc o ca ba noi (app, test,
         * va ban Python doi chieu), va dai hon Base64 dung 33% - khong
         * dang ke voi mot chuoi 32 byte.
         *
         * Doi dinh dang nay lam moi ban bam CU khong con khop. App chua
         * phat hanh cho ai ngoai nhom, nen tai khoan thu chi can dang ky
         * lai; khong co du lieu that nao mat.
         */
        fun bam(matKhau: String, muoi: ByteArray): String {
            val spec = PBEKeySpec(matKhau.toCharArray(), muoi, VONG, DAI_KHOA)
            val f = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256")
            return f.generateSecret(spec).encoded.joinToString("") { "%02x".format(it) }
        }

        /**
         * So sanh khong phu thuoc thoi gian.
         *
         * `String.equals` dung ngay khi gap ky tu khac nhau, nen thoi gian
         * tra loi he lo duoc bao nhieu ky tu dau la dung. Voi mot app cuc
         * bo thi kha nang bi do la rat thap, nhung day la thoi quen dung
         * va khong ton them gi.
         */
        fun bangNhau(a: String, b: String): Boolean {
            if (a.length != b.length) return false
            var khac = 0
            for (i in a.indices) khac = khac or (a[i].code xor b[i].code)
            return khac == 0
        }

        /**
         * Kiem email o muc du dung: DUNG MOT dau @, co ten truoc no, va co
         * dau cham o phan ten mien phia sau.
         *
         * Khong dung bieu thuc chinh quy RFC 5322 day du: bieu thuc do dai
         * hang tram ky tu, van tu choi mot so dia chi hop le, va o day no
         * khong giai quyet duoc gi - dia chi nay chi la TEN DANG NHAP tren
         * may nay, khong co thu nao duoc gui toi. Viec duy nhat can lam la
         * chan cac loi go nham ro rang.
         */
        fun emailHopLe(e: String): Boolean {
            val s = e.trim()
            if (s.count { it == '@' } != 1) return false
            val at = s.indexOf('@')
            return at > 0 && s.indexOf('.', at) > at + 1 && !s.endsWith(".") && ' ' !in s
        }

        /**
         * Do manh mat khau: 0 yeu / 1 tam / 2 tot.
         *
         * KHONG bat buoc ky tu dac biet hay chu hoa. Quy tac rac roi khien
         * nguoi ta chon "Matkhau@123" - de doan va de quen. Do dai la thu
         * quan trong nhat; man hinh dang ky noi ro dieu do va goi y cum ba
         * tu thay vi doi ky tu la.
         */
        fun doManh(mk: String): Int = when {
            mk.length < TOI_THIEU -> 0
            mk.length >= 12 || (mk.length >= 10 && mk.any { it.isDigit() }) -> 2
            else -> 1
        }

        const val TOI_THIEU = 8
    }
}
