package vn.adc2026.wayfinding

import android.content.Context

/**
 * Cai dat luu lai giua cac lan mo app.
 *
 * Rat it muc, va co ly do: moi muc them vao la mot thu co the dat sai
 * ngay demo. Chi giu nhung thu BAT BUOC phai doi theo tung buoi chay.
 */
class AppSettings(context: Context) {

    private val prefs = context.getSharedPreferences("wayfinding", Context.MODE_PRIVATE)

    /** Toc do doc. Mac dinh co y dat cao hon binh thuong. */
    var speechRate: Float
        get() = prefs.getFloat(KEY_RATE, Speaker.DEFAULT_RATE)
        set(v) = prefs.edit().putFloat(KEY_RATE, v).apply()

    /** Che do phan hoi: "ca_hai", "chi_am_thanh", "chi_rung". */
    var feedbackMode: String
        get() = prefs.getString(KEY_MODE, MODE_BOTH) ?: MODE_BOTH
        set(v) = prefs.edit().putString(KEY_MODE, v).apply()

    /**
     * ====================================================================
     * KIEU CHU (v5) - ba lua chon, TAT CA deu du dau tieng Viet
     * ====================================================================
     *
     * Da do bang fontTools tren bo 74 ky tu tieng Viet kho nhat (a/e/o/u
     * co dau, o+ u+, chu hoa co dau):
     *
     *   Lexend                       0/74 thieu  -> mac dinh
     *   Andika (SIL)                 0/74 thieu  -> cho nguoi kho doc
     *   Inter                        0/74 thieu  -> net trung tinh
     *   Atkinson Hyperlegible Next  50/74 THIEU  -> LOAI
     *   OpenDyslexic                   thieu     -> LOAI
     *
     * Hai font "dyslexia" noi tieng nhat deu khong dung duoc cho tieng
     * Viet: chu se hien o vuong, hoac he thong tron hai font trong mot tu
     * - te hon la khong doi font. Andika do SIL lam cho nguoi moi hoc doc:
     * chu rong, a/g mot tang, b/d/p/q khac han nhau, du dau tieng Viet.
     */
    var kieuChu: String
        get() = prefs.getString(KEY_KIEU_CHU, CHU_LEXEND) ?: CHU_LEXEND
        set(v) = prefs.edit().putString(KEY_KIEU_CHU, v).apply()

    /**
     * Co chu: 0.9 / 1.0 / 1.15.
     *
     * Khong chi phong to chu: `GiaoDien.apCoChu` gian ca chieu cao nut,
     * le va khoang cach theo CUNG mot he so, nen layout khong vo va vung
     * cham khong bi hep lai.
     */
    var coChu: Float
        get() = prefs.getFloat(KEY_CO_CHU, 1f)
        set(v) = prefs.edit().putFloat(KEY_CO_CHU, v.coerceIn(0.9f, 1.15f)).apply()

    /**
     * Cuong do rung: 0 Tat / 1 Nhe / 2 Vua / 3 Manh.
     *
     * Thay cho nut bat-tat cu. Nguoi nhay cam giac quan can muc that nhe
     * chu khong phai tat han; nguoi de dien thoai trong tui can muc manh.
     * Mot cong tac hai trang thai khong phuc vu duoc ca hai.
     */
    var mucRung: Int
        get() = prefs.getInt(KEY_MUC_RUNG, 2)
        set(v) = prefs.edit().putInt(KEY_MUC_RUNG, v.coerceIn(0, 3)).apply()

    /**
     * ====================================================================
     * CHE DO SANG / TOI (v5.1) - ba lua chon
     * ====================================================================
     *
     * `""` theo he thong (mac dinh) · `"sang"` · `"toi"`
     *
     * Mac dinh la THEO HE THONG chu khong phai sang: nguoi dung da tra
     * loi cau hoi nay mot lan o muc he thong roi, hoi lai la bat ho chon
     * hai lan cho cung mot thu.
     *
     * Cach ep nam o `CheDoToi.kt` - doc ghi chu dau tep do truoc khi sua,
     * co mot duong da tung lam app vang tren may that.
     */
    var cheDoToi: String
        get() = prefs.getString(KEY_CHE_DO_TOI, "") ?: ""
        set(v) = prefs.edit().putString(KEY_CHE_DO_TOI, v).apply()

    /**
     * ====================================================================
     * NHAC VIEC (v5.1, muc 3.3) - bon truc, xem `NhacCaiDat.kt`
     * ====================================================================
     */

    /** Gio yen tinh co bat khong. */
    var gioYenBat: Boolean
        get() = prefs.getBoolean(KEY_YEN_BAT, false)
        set(v) = prefs.edit().putBoolean(KEY_YEN_BAT, v).apply()

    /** Dau gio yen tinh, so phut tu 00:00. Mac dinh 22:00. */
    var gioYenTu: Int
        get() = prefs.getInt(KEY_YEN_TU, 22 * 60)
        set(v) = prefs.edit().putInt(KEY_YEN_TU, v.coerceIn(0, 24 * 60 - 1)).apply()

    /** Cuoi gio yen tinh. Mac dinh 07:00 - khung nay VAT QUA nua dem. */
    var gioYenDen: Int
        get() = prefs.getInt(KEY_YEN_DEN, 7 * 60)
        set(v) = prefs.edit().putInt(KEY_YEN_DEN, v.coerceIn(0, 24 * 60 - 1)).apply()

    /**
     * Bao truoc bao nhieu phut truoc gio bat dau. Mac dinh 10.
     *
     * Khong phai 0: nhac DUNG gio bat dau la nhac muon. Nguoi dung con
     * phai roi viec dang lam, di toi cho, mo tep ra - va chinh khoang dem
     * do la thu nguoi mu thoi gian khong uoc duoc.
     */
    var nhacTruocPhien: Int
        get() = prefs.getInt(KEY_TRUOC_PHIEN, 10)
        set(v) = prefs.edit().putInt(KEY_TRUOC_PHIEN, v.coerceIn(0, 60)).apply()

    /** Toi gio ma chua dong toi thi nhac lai sau bao lau. 0 = khong. */
    var nhacLai: Int
        get() = prefs.getInt(KEY_NHAC_LAI, 10)
        set(v) = prefs.edit().putInt(KEY_NHAC_LAI, v.coerceIn(0, 60)).apply()

    /**
     * Viec da qua gio duoc dung am bao KHAN.
     *
     * Mac dinh TAT. Am khan la mot cong cu manh, va neu no keu cho moi
     * viec tre thi chi sau vai ngay no thanh tieng on nen - luc do no
     * khong con danh thuc duoc ai, ke ca khi that su can.
     */
    var amKhanChoViecTre: Boolean
        get() = prefs.getBoolean(KEY_AM_KHAN, false)
        set(v) = prefs.edit().putBoolean(KEY_AM_KHAN, v).apply()

    /**
     * Bo mau vong dong ho Tap trung. "" = bang mau FlowyX goc.
     *
     * Day la MUC DUY NHAT trong app cho doi mau, va co ly do - xem ghi
     * chu dau `MauDongHo.kt`. Dung mo rong sang cac mau khac: moi mau
     * con lai trong app deu mang mot nghia co dinh.
     */
    var mauDongHo: String
        get() = prefs.getString(KEY_MAU_DONG_HO, "") ?: ""
        set(v) = prefs.edit().putString(KEY_MAU_DONG_HO, v).apply()

    /** Ngon ngu: "vi" | "en" | "" (theo may). */
    var ngonNgu: String
        get() = prefs.getString(KEY_NGON_NGU, "") ?: ""
        set(v) = prefs.edit().putString(KEY_NGON_NGU, v).apply()

    /** Tuong thich ban cu: code nao con doc `fontDeDoc` van chay dung. */
    var fontDeDoc: Boolean
        get() = kieuChu != CHU_HE_THONG
        set(v) { kieuChu = if (v) CHU_LEXEND else CHU_HE_THONG }

    val useSpeech: Boolean get() = feedbackMode != MODE_HAPTIC_ONLY
    val useHaptic: Boolean get() = feedbackMode != MODE_SPEECH_ONLY

    companion object {
        private const val KEY_RATE = "speech_rate"
        private const val KEY_MODE = "feedback_mode"
        private const val KEY_KIEU_CHU = "kieu_chu"
        private const val KEY_CO_CHU = "co_chu"
        private const val KEY_MUC_RUNG = "muc_rung"
        private const val KEY_NGON_NGU = "ngon_ngu"
        private const val KEY_CHE_DO_TOI = "che_do_toi"
        private const val KEY_MAU_DONG_HO = "mau_dong_ho"
        private const val KEY_YEN_BAT = "gio_yen_bat"
        private const val KEY_YEN_TU = "gio_yen_tu"
        private const val KEY_YEN_DEN = "gio_yen_den"
        private const val KEY_TRUOC_PHIEN = "nhac_truoc_phien"
        private const val KEY_NHAC_LAI = "nhac_lai"
        private const val KEY_AM_KHAN = "am_khan"

        const val CHU_LEXEND = "lexend"
        const val CHU_ANDIKA = "andika"
        const val CHU_INTER = "inter"
        const val CHU_HE_THONG = "he_thong"

        /** Tep trong assets/fonts cho tung kieu chu: (thuong, dam). */
        val TEP_CHU = mapOf(
            CHU_LEXEND to Pair("Lexend-Regular.ttf", "Lexend-SemiBold.ttf"),
            CHU_ANDIKA to Pair("Andika-Regular.ttf", "Andika-Bold.ttf"),
            CHU_INTER to Pair("Inter-Regular.ttf", "Inter-SemiBold.ttf"),
        )

        const val MODE_BOTH = "ca_hai"
        const val MODE_SPEECH_ONLY = "chi_am_thanh"
        const val MODE_HAPTIC_ONLY = "chi_rung"
    }
}
