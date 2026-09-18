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

    /**
     * Dia chi laptop, dang http://192.168.x.x:8765
     *
     * run_flowy.py in dia chi nay ra man hinh khi khoi dong. Doi moi
     * lan doi mang WiFi, nen phai luu lai va cho sua de khong phai go
     * lai tren dien thoai giua luc demo.
     */
    var serverUrl: String
        get() = prefs.getString(KEY_URL, DEFAULT_URL) ?: DEFAULT_URL
        set(v) = prefs.edit().putString(KEY_URL, v.trim()).apply()

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

    /** Ngon ngu: "vi" | "en" | "" (theo may). */
    var ngonNgu: String
        get() = prefs.getString(KEY_NGON_NGU, "") ?: ""
        set(v) = prefs.edit().putString(KEY_NGON_NGU, v).apply()

    /** Tuong thich ban cu: code nao con doc `fontDeDoc` van chay dung. */
    var fontDeDoc: Boolean
        get() = kieuChu != CHU_HE_THONG
        set(v) { kieuChu = if (v) CHU_LEXEND else CHU_HE_THONG }

    /**
     * Muc nhac gio: "it" | "vua" | "nhieu". Luu tren may va gui kem MOI
     * goi tin - laptop khong ghi gi xuong dia nen khong tu nho duoc.
     */
    var mucNhac: String
        get() = prefs.getString(KEY_MUC_NHAC, Payload.MUC_VUA) ?: Payload.MUC_VUA
        set(v) = prefs.edit().putString(KEY_MUC_NHAC, v).apply()

    val useSpeech: Boolean get() = feedbackMode != MODE_HAPTIC_ONLY
    val useHaptic: Boolean get() = feedbackMode != MODE_SPEECH_ONLY

    companion object {
        private const val KEY_URL = "server_url"
        private const val KEY_RATE = "speech_rate"
        private const val KEY_MODE = "feedback_mode"
        private const val KEY_KIEU_CHU = "kieu_chu"
        private const val KEY_CO_CHU = "co_chu"
        private const val KEY_MUC_RUNG = "muc_rung"
        private const val KEY_NGON_NGU = "ngon_ngu"
        private const val KEY_MUC_NHAC = "muc_nhac"

        private const val DEFAULT_URL = "http://192.168.1.100:8765"

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
