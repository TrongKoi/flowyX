package vn.adc2026.wayfinding

import android.Manifest
import android.app.Activity
import android.app.AlertDialog
import android.app.TimePickerDialog
import android.content.Context
import android.content.Intent
import android.content.pm.ActivityInfo
import android.content.pm.PackageManager
import android.graphics.drawable.GradientDrawable
import android.net.Uri
import android.os.BatteryManager
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.text.InputType
import android.util.Log
import android.view.View
import android.view.inputmethod.EditorInfo
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import vn.adc2026.frontend.TimerTronView
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicReference
import kotlin.math.ceil
import kotlin.math.roundToInt

/**
 * Man hinh chinh cua Flowy.
 *
 * --------------------------------------------------------------------
 * GIAO DIEN V2 (16/09) - HUONG C
 * --------------------------------------------------------------------
 *
 * Sang + toi theo may (hoac chon trong Cai dat), ba khoi thong tin CO
 * DINH: thoi gian, buoc hien tai, ban dong hanh. Dien thoai mot cot; may
 * tinh bang (rong tu 600 dp) hai cot - xem layout-sw600dp.
 *
 * Moi khoi luon o dung cho cua no. Khong co du lieu thi hien dau gach,
 * khoi KHONG co lai hay bien mat (UIUX_QUYET_DINH cau 3).
 *
 * --------------------------------------------------------------------
 * PHAN CHIA VIEC: DIEN THOAI LAM MAN HINH, LAPTOP LAM BO NAO
 * --------------------------------------------------------------------
 *
 * Lop nay KHONG chua quy tac nao cua Flowy. No khong biet khi nao nen
 * hoi gi, khi nao nen doi net mat, hay mot buoc coi la ket bao lau.
 * Tat ca nam o `run_flowy.py`, va ban iOS se chay cung logic do.
 *
 * Viec cua lop nay dung ba thu:
 *
 *     1. gui SU KIEN NGUOI DUNG len cau noi
 *     2. hien va doc len nhung gi cau noi tra ve
 *     3. GIU cac so cua rieng may nay (xem muc ranh gioi ben duoi)
 *
 * Viet quy tac o day la co hai ban quy tac phai giu khop nhau bang tay,
 * va chung se lech.
 *
 * --------------------------------------------------------------------
 * RANH GIOI DU LIEU
 * --------------------------------------------------------------------
 *
 * Xem bang o dau `bridge.py`. Ba so nam tren may nay:
 *
 *     SoThoiLuong   lich su thoi luong. Gui LEN phan cua DUNG MOT cong
 *                   viec dang lam, laptop tinh xong roi quen.
 *     SoNhac        ten cac loi nhac. KHONG BAO GIO len duong truyen.
 *     SoNhatKy      nhat ky. KHONG BAO GIO len duong truyen.
 *
 * Hai so sau khong duoc cham vao `Payload` hay `BridgeClient`.
 *
 * --------------------------------------------------------------------
 * APP KHONG BAO GIO CHU DONG BAT CHUYEN (nhan vat da bo, nguyen tac giu)
 * --------------------------------------------------------------------
 *
 * docs/luu-tru/NHAN_VAT_BRIEF.md muc 2.4 (nhan vat da bo, nguyen tac giu).
 * Nut Goi y la loi moi DUY NHAT de app len tieng voi mot cau hoi.
 *
 * Nen [chamNhanVat] la mot co MOT LAN: dat khi nguoi dung cham, xoa
 * ngay sau khi goi tin mang no di. Neu de no dinh lai, moi goi tin sau
 * do deu thanh mot cu cham, va app se hoi lien tuc - dung thu ma
 * ban mo ta cam.
 */
class MainActivity : Activity() {

    private lateinit var settings: AppSettings
    private lateinit var a11y: Accessibility

    private lateinit var oTraLoi: EditText
    private lateinit var tvCauHoi: TextView
    private lateinit var tvCauNoi: TextView
    private lateinit var tvTrangThai: TextView
    private lateinit var dongHo: TimerTronView
    private lateinit var khoiTiepTheo: View
    private lateinit var ttEmoji: TextView
    private lateinit var ttNhan: TextView
    private lateinit var ttTen: TextView

    private lateinit var tvViec: TextView
    private lateinit var tvKhiDau: TextView
    private lateinit var tvConLai: TextView
    private lateinit var tvGoiY: TextView
    private lateinit var tvBuocHienTai: TextView
    private lateinit var dsBuoc: LinearLayout
    private lateinit var nutChinh: Button
    private lateinit var nutTamDung: Button
    private lateinit var nutKetThuc: Button
    private lateinit var nutGioHen: Button
    private lateinit var nutUocLuong: Button
    private lateinit var chipMuc: Map<String, Button>

    private var speaker: Speaker? = null
    private var bridge: BridgeClient? = null
    private val voiceInput by lazy { VoiceInput(this) }

    // ---------------------------------------------------------------
    // Ba so cua rieng may nay
    // ---------------------------------------------------------------

    private lateinit var soThoiLuong: SoThoiLuong
    private lateinit var soNhac: SoNhac
    private lateinit var soNhatKy: SoNhatKy
    private lateinit var soTienDo: SoTienDo
    private lateinit var soLich: SoLich

    /** Ke hoach dang hien o the "Tiep theo". */
    private var keHoachTiepTheo: KeHoach? = null
    private var lanVeTiepTheo = 0L

    /**
     * Chuoi goi tin dien san y dinh tu mot ke hoach, gui LAN LUOT.
     *
     * Laptop gan cau noi vao o y dinh con thieu THEO THU TU (viec gi ->
     * khi nao -> o dau), nen moi o phai la mot goi rieng, va goi sau chi
     * di khi goi truoc da duoc tra loi.
     */
    private data class GoiCho(
        val lenh: String? = null, val voice: String? = null,
        val gioHen: Double? = null, val uoc: Double? = null,
    )
    private val hangDoiKeHoach = java.util.concurrent.ConcurrentLinkedQueue<GoiCho>()
    @Volatile private var choTraLoiHangDoiTu = 0L

    /**
     * Phien dang chay: bat dau luc nao, va ten viec do cau noi bao ve.
     *
     * `batDauMs` chi con la duong du phong: tu v2 laptop gui `da_lam_giay`
     * da TRU thoi gian tam dung, va do moi la con so ghi vao so.
     */
    private var batDauMs: Long = 0L
    private var tenViecDangLam: String? = null

    /** Uoc luong da gui cho viec nay - ghi kem thoi luong that khi xong. */
    private var uocDaGui: Double? = null

    /** Cau tra loi gan nhat. Nut chinh doi nhan va lenh theo no. */
    private var traCuoi: Reply = Reply()

    /** Cau hoi dang hien la tu mot cu cham (giu den khi tra loi). */
    private var hoiTuCham = false

    /** Chi ve lai danh sach buoc khi no DOI - xem [veCacBuoc]. */
    private var khoaBuoc: String? = null

    /** Giao dien luc tao man hinh - doi trong Cai dat thi dung lai. */
    private var dauVetGiaoDien = ""
    private var urlLucNoi = ""

    // ---------------------------------------------------------------
    // Trang thai gui goi tin
    // ---------------------------------------------------------------

    /**
     * App co dang o tien canh khong.
     *
     * Day la tin hieu phan tam CHINH. `@Volatile` vi no duoc GHI tu
     * luong chinh (onPause/onResume) va DOC tu luong gui goi tin.
     */
    @Volatile private var trenManHinh = true

    /** Co MOT LAN cho cu cham - xem phan dau file. */
    private val chamNhanVat = AtomicBoolean(false)

    /** Cau nguoi dung vua noi hoac vua go, dang cho gui di. */
    private val loiChoGui = AtomicReference<String?>(null)

    /** Lenh nut bam dang cho gui, kem noi dung. */
    private val lenhChoGui = AtomicReference<Pair<String, String?>?>(null)

    /** Gio hen / uoc luong vua chon, gui MOT lan. */
    private val gioHenChoGui = AtomicReference<Double?>(null)
    private val uocChoGui = AtomicReference<Double?>(null)

    /** Nguoi dung bam Noi khi chua co quyen micro -> nghe ngay khi duoc cap. */
    private var choNgheSauKhiCapQuyen = false

    /** Hop thoai giong Viet chi hoi MOT lan moi lan mo app. */
    private var daHoiGiongViet = false

    /** Trang thai quyen bao thuc lan truoc - doi thi dat lai chuong. */
    private var baoThucChinhXacTruoc: Boolean? = null

    private val tay = Handler(Looper.getMainLooper())
    private var nhipMs = Payload.NHIP_MAC_DINH_MS
    private var dangChay = false

    private val vongLap = object : Runnable {
        override fun run() {
            guiMotGoi()
            if (dangChay) tay.postDelayed(this, nhipMs.toLong())
        }
    }

    // ---------------------------------------------------------------
    // Vong doi
    // ---------------------------------------------------------------

    /**
     * Ban truoc goi thang `super.attachBaseContext(base)` - tuc la KHONG
     * boc gi ca. Man hinh nay vi vay khong he theo cai dat ngon ngu: doi
     * sang English thi 14 man hinh kia doi, rieng no van tieng Viet.
     * Loi im lang, khong lam test nao do.
     */
    override fun attachBaseContext(base: Context) {
        super.attachBaseContext(GiaoDien.boc(base))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        GiaoDien.apTheme(this)
        super.onCreate(savedInstanceState)

        // Dien thoai: khoa doc. May tinh bang: xoay tu do - hai cot dung
        // duoc ca doc lan ngang, va nhieu nguoi dat iPad/tab nam ngang.
        if (resources.configuration.smallestScreenWidthDp < 600) {
            requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_PORTRAIT
        }

        setContentView(R.layout.activity_main)

        settings = AppSettings(this)
        a11y = Accessibility(this)
        dauVetGiaoDien = GiaoDien.dauVet(this)

        soThoiLuong = SoThoiLuong.doc(this)
        soNhac = SoNhac.doc(this)
        soNhatKy = SoNhatKy.doc(this)
        soTienDo = SoTienDo.doc(this)
        soLich = SoLich.doc(this)

        oTraLoi = findViewById(R.id.o_tra_loi)
        tvCauHoi = findViewById(R.id.cau_hoi)
        tvCauNoi = findViewById(R.id.cau_noi)
        tvTrangThai = findViewById(R.id.trang_thai)
        dongHo = findViewById(R.id.dong_ho)
        khoiTiepTheo = findViewById(R.id.khoi_tiep_theo)
        ttEmoji = findViewById(R.id.tt_emoji)
        ttNhan = findViewById(R.id.tt_nhan)
        ttTen = findViewById(R.id.tt_ten)
        tvViec = findViewById(R.id.y_viec)
        tvKhiDau = findViewById(R.id.y_khi_dau)
        tvConLai = findViewById(R.id.tv_con_lai)
        tvGoiY = findViewById(R.id.tv_goi_y)
        tvBuocHienTai = findViewById(R.id.tv_buoc_hien_tai)
        dsBuoc = findViewById(R.id.ds_buoc)
        nutChinh = findViewById(R.id.nut_chinh)
        nutTamDung = findViewById(R.id.nut_tam_dung)
        nutKetThuc = findViewById(R.id.nut_ket_thuc)
        nutGioHen = findViewById(R.id.nut_gio_hen)
        nutUocLuong = findViewById(R.id.nut_uoc_luong)
        chipMuc = mapOf(
        )

        dongHo.datMau(getColor(R.color.dh_con_nhieu), getColor(R.color.dh_sap_den),
            getColor(R.color.dh_di_ngay), getColor(R.color.dh_ranh),
            getColor(R.color.chu), getColor(R.color.chu_phu))
        dongHo.datFont(GiaoDien.font(this, datDam = true))

        findViewById<View>(R.id.nut_cai_dat).setOnClickListener {
            startActivity(Intent(this, CaiDatActivity::class.java))
        }

        findViewById<Button>(R.id.nut_gui).setOnClickListener { guiLoiGo() }
        oTraLoi.setOnEditorActionListener { _, hanhDong, _ ->
            if (hanhDong == EditorInfo.IME_ACTION_SEND) { guiLoiGo(); true } else false
        }
        findViewById<Button>(R.id.nut_noi_mieng).setOnClickListener { ngheMotCau() }

        nutChinh.setOnClickListener { bamNutChinh() }
        nutTamDung.setOnClickListener {
            if (!traCuoi.trongPhien) return@setOnClickListener
            guiLenh(if (traCuoi.tamDung) Payload.LENH_TIEP_TUC else Payload.LENH_TAM_DUNG)
        }
        nutKetThuc.setOnClickListener {
            if (traCuoi.trongPhien) guiLenh(Payload.LENH_KET_THUC)
        }
        findViewById<Button>(R.id.nut_viec_moi).setOnClickListener { hoiViecMoi() }
        nutGioHen.setOnClickListener { chonGioHen() }
        nutUocLuong.setOnClickListener { chonUocLuong() }
        for ((muc, chip) in chipMuc) {
            chip.setOnClickListener {
                settings.mucNhac = muc
                veMucNhac()
                guiNgay()
            }
        }

        // Nut Goi y: loi moi DUY NHAT de app doc len mot cau hoi. Thay cho
        // cu cham vao nhan vat dong hanh (da bo 16/09). Truong goi tin van
        // ten `cham_nhan_vat` de khong pha hop dong voi laptop.
        findViewById<Button>(R.id.nut_goi_y).setOnClickListener {
            chamNhanVat.set(true)
            guiNgay()
        }

        // v5: `khoi_thanh_duoi.xml` da xoa han khoi kho - khong bo cuc nao
        // con include no, nen ba nut Lich / Loi nhac / Nhat ky o day khong
        // bao gio ton tai luc chay. Dieu huong da chuyen het sang thanh tab.
        findViewById<Button>(R.id.tt_bat_dau).setOnClickListener {
            keHoachTiepTheo?.let { batDauTuKeHoach(it) }
        }


        ThanhTab.noi(this, ThanhTab.FOCUS)
        theoLenhMo(intent)

        speaker = Speaker(this) { coGiongViet ->
            // Callback cua TTS chay tren luong KHAC luong chinh.
            if (!coGiongViet) runOnUiThread { hoiCaiGiongViet() }
        }
        speaker?.setRate(settings.speechRate)

        // Quyen thong bao: khong co no thi loi nhac im lang khong hien.
        // Xin mot lan luc mo app, khong chan gi neu nguoi dung tu choi.
        if (android.os.Build.VERSION.SDK_INT >= 33 &&
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
            != PackageManager.PERMISSION_GRANTED
        ) {
            KiemQuyen.xin(this, Manifest.permission.POST_NOTIFICATIONS,
                KiemQuyen.MA_THONG_BAO)
        }
        baoThucChinhXacTruoc = BaoGio.coTheDatChinhXac(this)
        BaoGio.datLai(this, soNhac)
        LichBao.datLai(this, soLich)

        // Ve trang thai rong ngay, truoc goi tin dau: man hinh khong bao
        // gio trong tron trong luc cho laptop.
        veTrangThai(Reply())
        veMucNhac()
        GiaoDien.apFont(findViewById(android.R.id.content), this)

        datTrangThai(
            if (settings.serverUrl.isBlank()) getString(R.string.chao_can_dia_chi)
            else getString(R.string.chao_san_sang)
        )
    }

    /**
     * Man hinh nay duoc mo lai bang `REORDER_TO_FRONT`, nen `onCreate`
     * KHONG chay lan hai. Lenh mo hop thoai phai bat o day, neu khong
     * thi bam "Nhat ky" o tab Tien do se chi chuyen tab roi thoi.
     */
    override fun onNewIntent(moi: Intent?) {
        super.onNewIntent(moi)
        moi?.let { intent = it; theoLenhMo(it) }
    }

    private fun theoLenhMo(i: Intent?) {
        // Tab "Viec can lam" gui ID ke hoach sang: nguoi dung bam "Bat
        // dau" o do, va man hinh nay moi la cho so huu ket noi.
        i?.getStringExtra(EXTRA_KE_HOACH)?.let { id ->
            i.removeExtra(EXTRA_KE_HOACH)
            SoLich.doc(this).tim(id)?.let { batDauTuKeHoach(it) }
        }
    }

    override fun onResume() {
        super.onResume()

        // Vua doi FONT trong Cai dat -> dung lai man hinh. Laptop giu
        // trang thai phien, nen dung lai khong mat gi.
        //
        // Che do sang/toi da bo (17/09): chuoi attachBaseContext ->
        // createConfigurationContext -> recreate lam app vang ra ngoai
        // tren Galaxy Tab S7 FE. Gio chi con font, va font khong doi
        // context nen duong nay an toan.
        if (GiaoDien.dauVet(this) != dauVetGiaoDien) {
            recreate()
            return
        }

        trenManHinh = true
        speaker?.setRate(settings.speechRate)
        if (bridge == null || settings.serverUrl != urlLucNoi) noiLai() else batVongLap()
        veMucNhac()

        // Nguoi dung vua quay ve tu man hinh cap quyen bao thuc: dat lai
        // chuong de cac loi nhac cu cung duoc chinh xac. Chi lam khi
        // quyen DOI - dat lai moi lan onResume co the day mot loi nhac
        // sap toi sang ngay mai.
        val chinhXac = BaoGio.coTheDatChinhXac(this)
        if (chinhXac != baoThucChinhXacTruoc) {
            baoThucChinhXacTruoc = chinhXac
            BaoGio.datLai(this, soNhac)
            LichBao.datLai(this, soLich)
        }

        // Lich co the vua duoc sua.
        soLich = SoLich.doc(this)
        veTiepTheo(batBuoc = true)
    }

    override fun onPause() {
        super.onPause()
        // KHONG dung vong lap o day.
        //
        // Ra khoi app CHINH LA tin hieu phan tam ma he thong can thay.
        // Dung gui thi laptop khong bao gio biet nguoi dung da di dau,
        // va cau dung lai ngu canh - thu co gia tri nhat sau mot lan
        // phan tam - se khong bao gio duoc noi.
        trenManHinh = false
        luuBaSo()
    }

    override fun onDestroy() {
        super.onDestroy()
        dangChay = false
        tay.removeCallbacks(vongLap)
        bridge?.close()
        speaker?.close()
        voiceInput.cancel()
        luuBaSo()
    }

    private fun luuBaSo() {
        soThoiLuong.luu(this)
        soNhac.luu(this)
        soNhatKy.luu(this)
    }

    // ---------------------------------------------------------------
    // Cau noi
    // ---------------------------------------------------------------

    private fun noiLai() {
        urlLucNoi = settings.serverUrl
        bridge?.close()
        bridge = BridgeClient(
            baseUrl = settings.serverUrl,
            onReply = { tra -> runOnUiThread { nhan(tra) } },
            onError = { loi ->
                runOnUiThread {
                    datTrangThai(getString(R.string.loi_mang, loi))
                }
            },
        )
        batVongLap()
        datTrangThai(getString(R.string.da_noi))
    }

    private fun batVongLap() {
        if (dangChay) return
        dangChay = true
        tay.post(vongLap)
    }

    /**
     * Gui ngay, khong doi het nhip.
     *
     * Luc ranh nhip la 2 giay - bam nut ma 2 giay sau man hinh moi doi la
     * du lau de nguoi dung bam lai lan nua.
     */
    private fun guiNgay() {
        if (!dangChay) return
        tay.removeCallbacks(vongLap)
        tay.post(vongLap)
    }

    private fun guiLenh(lenh: String, noiDung: String? = null) {
        lenhChoGui.set(lenh to noiDung)
        guiNgay()
    }

    private fun guiMotGoi() {
        val b = bridge ?: return

        // Chuoi dien san tu ke hoach: mot o moi goi, doi tra loi (hoac 3
        // giay, phong mat goi) roi moi gui o tiep theo.
        val bay = System.currentTimeMillis()
        val cho = if (hangDoiKeHoach.isNotEmpty() && bay - choTraLoiHangDoiTu > 3000) {
            hangDoiKeHoach.poll()?.also { choTraLoiHangDoiTu = bay }
        } else null

        val lenh = cho?.lenh?.let { it to null } ?: lenhChoGui.getAndSet(null)
        val voice = cho?.voice ?: if (cho?.lenh == null) loiChoGui.getAndSet(null) else null
        val gioHen = cho?.gioHen ?: gioHenChoGui.getAndSet(null)
        val uoc = cho?.uoc ?: uocChoGui.getAndSet(null)
        val cham = chamNhanVat.getAndSet(false)

        // Chi gui lich su cua DUNG cong viec dang lam. Khong co ten thi
        // khong gui gi - gui ca so la dua lich su lam viec len duong
        // truyen, va bang trong bridge.py cam dieu do.
        val lichSu = tenViecDangLam?.let { soThoiLuong.jsonMotViec(it) }

        // Goi co thao tac nguoi dung thi KHONG duoc mat - xem BridgeClient.
        val quanTrong = cho != null || lenh != null || voice != null || cham ||
            gioHen != null || uoc != null

        b.send(Payload.buildUpdate(
            tSeconds = System.currentTimeMillis() / 1000.0,
            trenManHinh = trenManHinh,
            // getAndSet o tren: co mot lan, xoa ngay khi goi tin mang no di.
            chamNhanVat = cham,
            voice = voice,
            lenh = lenh?.first,
            noiDung = lenh?.second,
            battery = mucPin(),
            lichSu = lichSu,
            gioHen = gioHen,
            uocPhut = uoc,
            mucNhac = settings.mucNhac,
        ), quanTrong)
    }

    /**
     * Xu ly mot cau tra loi. Luon chay tren luong chinh.
     */
    private fun nhan(tra: Reply) {
        nhipMs = tra.nhipMs.coerceIn(100, 10_000)

        // Goi dien san truoc da ve -> gui o tiep theo ngay.
        if (choTraLoiHangDoiTu != 0L) {
            choTraLoiHangDoiTu = 0L
            if (hangDoiKeHoach.isNotEmpty()) tay.post { guiNgay() }
        }

        if (tra.tenViec != null) tenViecDangLam = tra.tenViec

        tra.say?.let { cau ->
            tvCauNoi.text = cau
            if (settings.useSpeech) speaker?.say(cau, urgent = false)
        }

        if (tra.hoi != null) {
            // HIEN thi luon. Man hinh trong tron thi nguoi dung khong
            // biet go gi - mot dong chu la nhan cua o nhap lieu.
            tvCauHoi.text = tra.hoi
            hoiTuCham = tra.listen

            // DOC LEN thi chi khi `listen` bat, tuc la chi sau mot cu
            // cham. Do la duong ranh cua muc 2.4 ban mo ta nhan vat:
            // chu tren man hinh la thu dong, cau doc len la bat chuyen.
            if (tra.listen && settings.useSpeech) {
                speaker?.say(tra.hoi, urgent = true)
            }
        } else if (!hoiTuCham) {
            // Cau hoi gom y dinh da duoc tra loi -> xoa, dung de mot cau
            // hoi cu nam lai tren man hinh.
            tvCauHoi.text = ""
        }

        if (settings.useHaptic) speaker?.vibrate(tra.haptic)
        speaker?.playAm(tra.am)

        // `listen` la mot co ro rang chu khong phai suy dien tu noi dung
        // cau noi: so chuoi thi doi mot chu trong ma la hong lop nghe, ma
        // hong im lang.
        if (tra.listen) ngheMotCau()

        // Phien vua xong -> ghi thoi luong THAT vao so cua may nay.
        // Day la ca co che hoc cua lop chong mu thoi gian: lan sau khong
        // phai doan nua.
        if (tra.xongPhien) ghiThoiLuong(tra)

        traCuoi = tra
        veTrangThai(tra)
        veTiepTheo()

        // Loi nhac den gio trong luc app dang mo. Chuong he thong van
        // chay khi app dong - xem `BaoGio`.
        kiemLoiNhac()
    }

    private fun ghiThoiLuong(tra: Reply) {
        val ten = tenViecDangLam ?: return
        // Uu tien so laptop gui: da tru thoi gian tam dung.
        val phut = tra.daLamGiay?.let { it / 60.0 }
            ?: if (batDauMs > 0L) (System.currentTimeMillis() - batDauMs) / 60_000.0
               else return
        soThoiLuong.ghi(ten, phut, uocDaGui)
        soThoiLuong.luu(this)

        // Mot phien xong = mot viec trong so tien do. Ghi o DAY chu
        // khong o TienDoActivity: man hinh do chi doc, nen mo di mo lai
        // no khong lam con so doi.
        soTienDo.ghi()
        soTienDo.luu(this)
        batDauMs = 0L
        uocDaGui = null
    }

    private fun mucPin(): Double? {
        val bm = getSystemService(BATTERY_SERVICE) as? BatteryManager ?: return null
        val p = bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        return if (p in 0..100) p.toDouble() else null
    }

    // ---------------------------------------------------------------
    // Ve giao dien tu mot cau tra loi
    // ---------------------------------------------------------------

    private fun veTrangThai(tra: Reply) {
        // ---- y dinh ----
        tvViec.text = tra.viecGi ?: getString(R.string.chua_co_viec)
        tvViec.setTextColor(getColor(if (tra.viecGi != null) R.color.chu else R.color.chu_phu))
        tvKhiDau.text = getString(R.string.khi_nao_o_dau,
            tra.khiNao ?: getString(R.string.gach), tra.oDau ?: getString(R.string.gach))

        val duYDinh = tra.viecGi != null && tra.khiNao != null && tra.oDau != null
        oTraLoi.hint = getString(if (duYDinh) R.string.hint_them_buoc else R.string.hint_tra_loi)

        // ---- khoi 1: thoi gian ----
        val con = tra.conLaiGiay
        val tong = tra.tongGiay
        if (con != null && tong != null && tong > 0.0) {
            val phan = con / tong
            val muc = when {
                phan > 0.5 -> TimerTronView.Muc.CON_NHIEU
                phan > 0.15 -> TimerTronView.Muc.SAP_DEN_GIO
                else -> TimerTronView.Muc.DI_NGAY
            }
            // Lam tron LEN: con 40 giay van la "1 phut", khong phai "0".
            val phut = ceil(con / 60.0).toInt()
            dongHo.dat(con.toFloat(), tong.toFloat(), nhan = "$phut", muc = muc)
            tvConLai.text = getString(R.string.phut_con_lai, "$phut")
        } else {
            dongHo.datTrong()
            tvConLai.text = getString(R.string.chua_co_gio_hen)
        }

        tvGoiY.text = when {
            tra.tamDung -> getString(R.string.dang_tam_dung)
            tra.trongPhien && tra.daLamGiay != null ->
                getString(R.string.da_lam, "${(tra.daLamGiay / 60.0).roundToInt()}")
            tra.goiYPhut != null ->
                getString(R.string.goi_y_thuong_mat, "${tra.goiYPhut.roundToInt()}")
            else -> ""
        }
        nutGioHen.text = tra.gioHen?.let { getString(R.string.gio_hen_la, it) }
            ?: getString(R.string.dat_gio_hen)
        // Uu tien con so nguoi dung VUA CHON, roi moi den con so laptop
        // gui ve.
        //
        // Ban truoc chi doc `tra.uocPhut`. Nghia la nut chi doi chu khi
        // laptop tra loi - va khi chua noi duoc laptop thi no DUNG YEN
        // mai. Nguoi dung chon 15 phut, khong thay gi doi, chon lai so
        // khac, van khong thay gi: trong nhu nut hong.
        //
        // Bug tu buoi test 17/09. Sua bang cach hien ngay roi de laptop
        // xac nhan sau - chon xong thay ngay la dung ky vong, va neu
        // laptop tra ve so khac thi so do de len.
        val uocHien = tra.uocPhut ?: uocDaGui
        nutUocLuong.text = uocHien?.let { getString(R.string.uoc_luong_la, "${it.roundToInt()}") }
            ?: getString(R.string.uoc_luong)

        // ---- khoi 2: buoc ----
        val conBuoc = tra.chiSoBuoc < tra.cacBuoc.size
        tvBuocHienTai.text = when {
            tra.trongPhien && conBuoc -> tra.cacBuoc[tra.chiSoBuoc]
            tra.trongPhien -> tra.viecGi ?: getString(R.string.gach)
            tra.cacBuoc.isNotEmpty() && !conBuoc -> getString(R.string.buoc_xong_het)
            else -> getString(R.string.gach)
        }
        veCacBuoc(tra.cacBuoc, if (tra.trongPhien) tra.chiSoBuoc else -1)

        // ---- nut ----
        nutChinh.setText(when {
            tra.tamDung -> R.string.tiep_tuc
            tra.trongPhien && conBuoc -> R.string.xong_buoc
            tra.trongPhien -> R.string.xong_viec
            else -> R.string.bat_dau
        })
        nutTamDung.setText(if (tra.tamDung) R.string.tiep_tuc else R.string.tam_dung)
        nutTamDung.isEnabled = tra.trongPhien
        nutKetThuc.isEnabled = tra.trongPhien
        nutTamDung.alpha = if (tra.trongPhien) 1f else 0.45f
        nutKetThuc.alpha = nutTamDung.alpha
    }

    private fun bamNutChinh() {
        val tra = traCuoi
        when {
            tra.tamDung -> guiLenh(Payload.LENH_TIEP_TUC)
            tra.trongPhien && tra.chiSoBuoc < tra.cacBuoc.size ->
                guiLenh(Payload.LENH_XONG_BUOC)
            tra.trongPhien -> guiLenh(Payload.LENH_KET_THUC)
            else -> {
                // Chu trong o tra loi di kem lenh: nguoi dung thuong go
                // o cuoi roi bam thang Bat dau, khong bam Gui truoc.
                val chu = oTraLoi.text.toString().trim().ifEmpty { null }
                oTraLoi.setText("")
                batDauMs = System.currentTimeMillis()
                guiLenh(Payload.LENH_BAT_DAU, chu)
            }
        }
    }

    /**
     * Moi buoc mot khoi mau, xoay vong nam mau diu.
     *
     * Chi ve lai khi danh sach hoac chi so DOI. Goi tin toi moi nua giay;
     * ve lai moi lan thi TalkBack doc lai ca danh sach lien tuc.
     */
    private fun veCacBuoc(cacBuoc: List<String>, chiSo: Int) {
        val khoa = "$chiSo|" + cacBuoc.joinToString("\u0000")
        if (khoa == khoaBuoc) return
        khoaBuoc = khoa
        dsBuoc.removeAllViews()

        if (cacBuoc.isEmpty()) {
            dsBuoc.addView(TextView(this).apply {
                setText(R.string.buoc_trong)
                setTextColor(getColor(R.color.chu_phu))
                textSize = 15f
            })
            GiaoDien.apFont(dsBuoc, this)
            return
        }

        val mau = intArrayOf(R.color.buoc_1, R.color.buoc_2, R.color.buoc_3,
            R.color.buoc_4, R.color.buoc_5)
        cacBuoc.forEachIndexed { i, ten ->
            val xong = chiSo >= 0 && i < chiSo
            val dangLam = i == chiSo
            val o = TextView(this).apply {
                text = if (xong) "✓  $ten" else ten
                setTextColor(getColor(R.color.chu))
                textSize = if (dangLam) 17f else 15f
                if (dangLam) setTypeface(typeface, android.graphics.Typeface.BOLD)
                setPadding(dp(14), dp(12), dp(14), dp(12))
                background = GradientDrawable().apply {
                    cornerRadius = dp(14).toFloat()
                    setColor(getColor(mau[i % mau.size]))
                    if (dangLam) setStroke(dp(2), getColor(R.color.nhan))
                }
                // Buoc xong mo di - khong gach, khong to do.
                alpha = if (xong) 0.55f else 1f
                contentDescription = when {
                    xong -> "Đã xong: $ten"
                    dangLam -> "Đang làm: $ten"
                    else -> ten
                }
            }
            dsBuoc.addView(o, LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT).apply {
                if (i > 0) topMargin = dp(6)
            })
        }
        GiaoDien.apFont(dsBuoc, this)
    }

    private fun veMucNhac() {
        for ((muc, chip) in chipMuc) chip.isSelected = muc == settings.mucNhac
    }

    // ---------------------------------------------------------------
    // Lich: the "Tiep theo" va bat dau tu ke hoach
    // ---------------------------------------------------------------

    /**
     * The ke hoach tiep theo hom nay. An khi dang trong phien (luc do nguoi
     * dung dang lam roi) hoac khong con gi hom nay.
     *
     * Goi tin toi moi nua giay nhung the chi can tinh lai moi 30 giay.
     */
    private fun veTiepTheo(batBuoc: Boolean = false) {
        val bay = System.currentTimeMillis()
        if (!batBuoc && bay - lanVeTiepTheo < 30_000) return
        lanVeTiepTheo = bay

        val bayGio = SoLich.bayGio()
        val kh = if (traCuoi.trongPhien) null
                 else Lich.tiepTheo(soLich.danhSach, bayGio, soLich.daXong)
        keHoachTiepTheo = kh
        if (kh == null) {
            khoiTiepTheo.visibility = View.GONE
            return
        }
        val phut = (bayGio - SoLich.homNay() * 1440).toInt()
        ttEmoji.text = kh.emoji
        ttTen.text = kh.ten
        ttNhan.text = if (kh.batDau <= phut) {
            getString(R.string.dang_dien_ra_den, Lich.gioPhut(kh.ketThuc))
        } else {
            getString(R.string.tiep_theo_luc, Lich.gioPhut(kh.batDau)) +
                " (còn ${Lich.moTaPhut(kh.batDau - phut, this)})"
        }
        khoiTiepTheo.contentDescription = "${ttNhan.text}. ${kh.ten}"
        khoiTiepTheo.visibility = View.VISIBLE
    }

    /**
     * Bat dau phien tu mot ke hoach trong lich.
     *
     *     viec_moi            xoa y dinh cu
     *     ten ke hoach        -> o "viec gi"; gio hen = gio ket thuc; uoc = thoi luong
     *     "luc HH:MM"         -> o "khi nao"
     *     noi lam (neu co)    -> o "o dau"; khong co thi laptop hoi, hien tren man hinh
     *
     * Uoc luong = thoi luong nguoi dung da tu dat trong lich. Xong phien,
     * so thoi luong ghi ca uoc lan that - lan sau co cau doi chieu.
     */
    private fun batDauTuKeHoach(kh: KeHoach) {
        hangDoiKeHoach.clear()
        hangDoiKeHoach.add(GoiCho(lenh = Payload.LENH_VIEC_MOI))
        hangDoiKeHoach.add(GoiCho(voice = kh.ten,
            gioHen = kh.ketThuc.takeIf { it < 1440 }?.toDouble(),
            uoc = kh.thoiLuong.toDouble()))
        hangDoiKeHoach.add(GoiCho(voice = "lúc ${Lich.gioPhut(kh.batDau)}"))
        kh.oDau?.let { hangDoiKeHoach.add(GoiCho(voice = it)) }

        tenViecDangLam = kh.ten
        uocDaGui = kh.thoiLuong.toDouble()
        batDauMs = 0L
        hoiTuCham = false
        tvCauNoi.text = ""
        khoiTiepTheo.visibility = View.GONE
        choTraLoiHangDoiTu = 0L
        guiNgay()
        findViewById<View?>(R.id.cuon)?.let { (it as? android.widget.ScrollView)?.smoothScrollTo(0, 0) }
    }

    // ---------------------------------------------------------------
    // Gio hen, uoc luong, viec moi
    // ---------------------------------------------------------------

    /**
     * Dat gio hen.
     *
     * Truoc v2 gio hen chi dat duoc bang `--gio-hen` khi chay laptop, nen
     * dia thoi gian gan nhu khong bao gio hien tren dien thoai.
     */
    private fun chonGioHen() {
        if (traCuoi.gioHen == null) {
            moDongHoGioHen()
            return
        }
        AlertDialog.Builder(this)
            .setTitle(getString(R.string.gio_hen_la, traCuoi.gioHen))
            .setItems(arrayOf(getString(R.string.dat_gio_hen),
                getString(R.string.bo_gio_hen))) { _, i ->
                if (i == 0) moDongHoGioHen()
                else { gioHenChoGui.set(Payload.BO_GIO_HEN); guiNgay() }
            }
            .setNegativeButton(R.string.huy, null)
            .hien()
    }

    private fun moDongHoGioHen() {
        val cu = traCuoi.gioHen?.let { DocGio.doc(it) }
        val bayGio = java.util.Calendar.getInstance().apply { add(java.util.Calendar.MINUTE, 30) }
        val g = cu?.let { (it / 60).toInt() } ?: bayGio.get(java.util.Calendar.HOUR_OF_DAY)
        val p = cu?.let { (it % 60).toInt() } ?: (bayGio.get(java.util.Calendar.MINUTE) / 5 * 5)
        TimePickerDialog(this, { _, gio, phut ->
            gioHenChoGui.set(gio * 60.0 + phut)
            guiNgay()
        }, g, p, true).hien()
    }

    /**
     * Uoc luong. Nut san cho cac muc hay gap - go so la mot buoc them.
     *
     * Day la nua con thieu cua co che hoc o FLOWY_THIET_KE muc 3.1: khong
     * co uoc luong thi khong co cau "lan truoc ban uoc 20, thuc te 35".
     */
    private fun chonUocLuong() {
        val muc = intArrayOf(5, 10, 15, 25, 45, 60)
        val nhan = muc.map { "$it phút" } + getString(R.string.uoc_luong_khac)
        AlertDialog.Builder(this)
            .setCustomTitle(tieuDe(getString(R.string.uoc_luong_hoi),
                getString(R.string.uoc_luong_giai_thich)))
            .setItems(nhan.toTypedArray()) { _, i ->
                if (i < muc.size) datUoc(muc[i].toDouble()) else nhapUocTay()
            }
            .setNegativeButton(R.string.huy, null)
            .hien()
    }

    private fun nhapUocTay() {
        val o = EditText(this).apply {
            hint = getString(R.string.hint_so_phut)
            inputType = InputType.TYPE_CLASS_NUMBER
            minHeight = dp(48)
        }
        val khoi = LinearLayout(this).apply {
            setPadding(dp(24), dp(12), dp(24), 0)
            addView(o, LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT))
        }
        val hop = AlertDialog.Builder(this)
            .setTitle(R.string.uoc_luong_hoi)
            .setView(khoi)
            .setPositiveButton(R.string.luu, null)
            .setNegativeButton(R.string.huy, null)
            .create()
        hop.setOnShowListener {
            hop.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener {
                val n = o.text.toString().toIntOrNull()
                if (n == null || n !in 1..1440) {
                    o.error = getString(R.string.hint_so_phut)
                    return@setOnClickListener
                }
                datUoc(n.toDouble())
                hop.dismiss()
            }
        }
        hop.hien()
    }

    private fun datUoc(phut: Double) {
        uocDaGui = phut
        uocChoGui.set(phut)
        // Ve lai NGAY. `guiNgay()` chi day goi tin di; nut se doi chu o
        // lan laptop tra loi, ma co the khong bao gio den.
        nutUocLuong.text = getString(R.string.uoc_luong_la, "${phut.roundToInt()}")
        guiNgay()
    }

    private fun hoiViecMoi() {
        val tra = traCuoi
        val coGi = tra.trongPhien || tra.viecGi != null
        fun lam() {
            guiLenh(Payload.LENH_VIEC_MOI)
            tenViecDangLam = null
            uocDaGui = null
            batDauMs = 0L
            hoiTuCham = false
            tvCauNoi.text = ""
        }
        if (!coGi) { lam(); return }
        AlertDialog.Builder(this)
            .setMessage(R.string.viec_moi_hoi)
            .setPositiveButton(R.string.viec_moi) { _, _ -> lam() }
            .setNegativeButton(R.string.huy, null)
            .hien()
    }

    // ---------------------------------------------------------------
    // Dau vao cua nguoi dung
    // ---------------------------------------------------------------

    private fun guiLoiGo() {
        val chu = oTraLoi.text.toString().trim()
        if (chu.isEmpty()) return
        oTraLoi.setText("")
        loiChoGui.set(chu)
        tvCauHoi.text = ""
        hoiTuCham = false
        guiNgay()
    }

    /**
     * Nghe mot cau.
     *
     * Van luon co O GO ben canh: nhan dang giong noi hong o noi on, va
     * mot nguoi dang ket ma phai lap lai cau ba lan se bo app. Giong noi
     * la duong NHANH HON, khong phai duong duy nhat.
     */
    private fun ngheMotCau() {
        // Ban cu KHONG BAO GIO xin quyen micro, nen nut Noi luon im lang
        // bao "chua nghe duoc" tren may moi cai.
        if (!KiemQuyen.coQuyen(this, Manifest.permission.RECORD_AUDIO)) {
            choNgheSauKhiCapQuyen = true
            KiemQuyen.xin(this, Manifest.permission.RECORD_AUDIO, KiemQuyen.MA_MICRO)
            return
        }
        if (!voiceInput.available()) {
            datTrangThai(getString(R.string.chua_nghe_duoc))
            return
        }
        voiceInput.listenOnce { ketQua ->
            runOnUiThread {
                if (ketQua.isNullOrBlank()) {
                    datTrangThai(getString(R.string.chua_nghe_duoc))
                } else {
                    loiChoGui.set(ketQua)
                    tvCauHoi.text = ""
                    hoiTuCham = false
                    guiNgay()
                }
            }
        }
    }

    /**
     * Dong trang thai nho tren cung.
     *
     * Chi HIEN va de TalkBack doc (neu dang bat). KHONG tu doc bang TTS:
     * ban cu doc to moi dong trang thai, ke ca "Loi mang" lap lai - trai
     * voi muc 2.4 NHAN_VAT_BRIEF (app khong chu dong len tieng).
     */
    private fun datTrangThai(s: String) {
        tvTrangThai.text = s
        a11y.announce(tvTrangThai, s, speaker, useSpeech = false)
    }

    // ---------------------------------------------------------------
    // Nhom (a): loi nhac theo gio
    // ---------------------------------------------------------------

    private fun kiemLoiNhac() {
        val c = java.util.Calendar.getInstance()
        val phut = c.get(java.util.Calendar.HOUR_OF_DAY) * 60.0 +
            c.get(java.util.Calendar.MINUTE)
        val ngay = String.format(
            java.util.Locale.US, "%04d-%02d-%02d",
            c.get(java.util.Calendar.YEAR),
            c.get(java.util.Calendar.MONTH) + 1,
            c.get(java.util.Calendar.DAY_OF_MONTH))

        val ln = soNhac.denHan(phut, ngay) ?: return
        val cau = ln.cau()
        tvCauNoi.text = cau
        if (settings.useSpeech) speaker?.say(cau, urgent = true)
    }

    /**
     * Danh sach loi nhac.
     *
     * KHONG co cot "da lam", KHONG co ty le tuan thu, KHONG co canh bao
     * bo lo. Xem `adhd/nhacviec.py` ve ly do - ca ly do phap ly lan ly
     * do thuc te.
     */
    private fun moLoiNhac() {
        val ten = soNhac.danhSach.map { "${it.gioPhut}  ${it.ten}" }
        val ds = if (ten.isEmpty()) listOf(getString(R.string.chua_co_loi_nhac))
        else ten

        AlertDialog.Builder(this)
            .setTitle(R.string.loi_nhac)
            .setAdapter(ArrayAdapter(this,
                android.R.layout.simple_list_item_1, ds)) { _, i ->
                if (ten.isNotEmpty()) hoiXoaLoiNhac(i)
            }
            .setPositiveButton(R.string.them) { _, _ -> themLoiNhac() }
            .setNegativeButton(R.string.xong, null)
            .hien()
    }

    private fun hoiXoaLoiNhac(chiSo: Int) {
        AlertDialog.Builder(this)
            .setMessage(soNhac.danhSach.getOrNull(chiSo)?.ten ?: return)
            .setPositiveButton(R.string.xoa) { _, _ ->
                soNhac.xoa(chiSo)
                soNhac.luu(this)
                BaoGio.datLai(this, soNhac)
                moLoiNhac()
            }
            .setNegativeButton(R.string.huy) { _, _ -> moLoiNhac() }
            .hien()
    }

    /**
     * Them mot loi nhac.
     *
     * --------------------------------------------------------------
     * HAI BUG TU BUOI TEST, SUA O DAY
     * --------------------------------------------------------------
     *
     * 1. Thieu du lieu thi hop thoai DONG LUON va nguoi dung phai go lai
     *    tu dau. `AlertDialog` tu dong khi bam nut tich cuc - nen nut
     *    Them duoc ghi de trong `setOnShowListener`, va chi dong khi du
     *    lieu hop le. Thieu o nao thi o do hien loi ngay tai cho.
     *
     * 2. O gio mo ban phim chi co so, go "1400" bi bao sai. Gio cham vao
     *    o gio thi mo dong ho chon gio cua Android; van go tay duoc, va
     *    `DocGio` nhan ca "1400", "930", "14h30".
     *
     * Thu tu kiem tra: o ten TRUOC, o gio SAU - dung thu tu tren man
     * hinh, de con tro nhay toi o thieu dau tien tu tren xuong.
     */
    private fun themLoiNhac() {
        val oTen = EditText(this).apply {
            hint = getString(R.string.hint_ten_loi_nhac)
            inputType = InputType.TYPE_CLASS_TEXT or
                InputType.TYPE_TEXT_FLAG_CAP_SENTENCES
            minHeight = dp(48)
        }
        val oGio = EditText(this).apply {
            hint = getString(R.string.hint_gio_loi_nhac)
            // So + dau hai cham tren moi ban phim. TYPE_CLASS_DATETIME cu
            // bi Samsung hien thanh ban phim chi co so.
            inputType = InputType.TYPE_CLASS_TEXT
            minHeight = dp(48)
            // Cham vao la mo dong ho chon gio. Van go tay duoc sau do.
            setOnClickListener { chonGio(this) }
            setOnFocusChangeListener { v, coFocus ->
                if (coFocus && text.isNullOrBlank()) chonGio(v as EditText)
            }
        }
        val khoi = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(24), dp(12), dp(24), 0)
            addView(oTen)
            addView(oGio)
        }

        val hop = AlertDialog.Builder(this)
            .setTitle(R.string.them_loi_nhac)
            .setView(khoi)
            // Listener null: nut duoc ghi de ben duoi de KHONG tu dong.
            .setPositiveButton(R.string.them, null)
            .setNegativeButton(R.string.huy) { _, _ -> moLoiNhac() }
            .create()

        hop.setOnShowListener {
            hop.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener {
                val ten = oTen.text.toString().trim()
                val phut = DocGio.doc(oGio.text.toString())

                oTen.error = null
                oGio.error = null
                var oLoiDau: EditText? = null

                if (ten.length < SoNhac.MIN_KY_TU) {
                    oTen.error = getString(R.string.thieu_ten_loi_nhac)
                    oLoiDau = oLoiDau ?: oTen
                }
                if (phut == null) {
                    oGio.error = getString(R.string.thieu_gio_loi_nhac)
                    oLoiDau = oLoiDau ?: oGio
                }
                if (oLoiDau != null || phut == null) {
                    oLoiDau?.requestFocus()
                    return@setOnClickListener       // hop thoai VAN MO
                }

                if (!soNhac.them(ten, phut)) {
                    // Khong nen xay ra - da kiem o tren. Van giu hop thoai.
                    oTen.error = getString(R.string.loi_nhac_sai)
                    return@setOnClickListener
                }
                soNhac.luu(this)
                hop.dismiss()

                when (BaoGio.datLai(this, soNhac)) {
                    BaoGio.KetQua.CO_THE_TRE -> hoiQuyenBaoThuc()
                    BaoGio.KetQua.KHONG_DAT_DUOC -> {
                        datTrangThai(getString(R.string.bao_thuc_khong_dat_duoc))
                        moLoiNhac()
                    }
                    else -> {
                        datTrangThai(getString(R.string.da_dat_loi_nhac, DocGio.hien(phut)))
                        moLoiNhac()
                    }
                }
            }
        }
        hop.hien()
    }

    /** Dong ho chon gio 24h cua Android. Chon xong thi dien vao o. */
    private fun chonGio(o: EditText) {
        val cu = DocGio.doc(o.text.toString())
        val bayGio = java.util.Calendar.getInstance()
        val g = cu?.let { (it / 60).toInt() } ?: bayGio.get(java.util.Calendar.HOUR_OF_DAY)
        val p = cu?.let { (it % 60).toInt() } ?: bayGio.get(java.util.Calendar.MINUTE)
        TimePickerDialog(this, { _, gio, phut ->
            o.setText(DocGio.hien(gio * 60.0 + phut))
            o.error = null
        }, g, p, true).hien()
    }

    /**
     * Loi nhac da luu nhung co the tre -> hoi mot lan, co giai thich.
     *
     * KHONG mo thang trang Cai dat: nguoi dung bi day sang mot man hinh
     * la ma khong biet vi sao se bam Back ngay. Mot cau giai thich truoc
     * lam cho buoc do co nghia.
     */
    private fun hoiQuyenBaoThuc() {
        AlertDialog.Builder(this)
            .setTitle(R.string.bao_thuc_tieu_de)
            .setMessage(R.string.bao_thuc_giai_thich)
            .setPositiveButton(R.string.mo_cai_dat) { _, _ ->
                KiemQuyen.xuLy(this, KiemQuyen.danhSach(this, speaker)
                    .first { it.loai == KiemQuyen.Loai.BAO_THUC }, speaker)
            }
            .setNegativeButton(R.string.de_sau) { _, _ -> moLoiNhac() }
            .hien()
    }

    /** Giu lai cho code cu goi toi. Xem [DocGio]. */
    internal fun docGio(s: String): Double? = DocGio.doc(s)

    // ---------------------------------------------------------------
    // Nhom (b): nhat ky
    // ---------------------------------------------------------------

    /**
     * So nhat ky.
     *
     * App KHONG dien giai gi o day: khong trung binh, khong xu huong,
     * khong bieu do. Chi la cac muc theo thu tu thoi gian.
     */
    private fun moNhatKy() {
        val cacMuc = soNhatKy.ganDay(SO_MUC_HIEN)
        val dong = cacMuc.map { it.dong() }

        // --------------------------------------------------------------
        // BUG TU BUOI TEST: SO LUON HIEN TRONG
        // --------------------------------------------------------------
        //
        // Ban cu goi CA `setMessage` LAN `setAdapter` tren cung mot
        // AlertDialog. Android chi hien MOT trong hai: co message thi
        // danh sach bi bo di - im lang, khong bao loi. Du lieu van nam
        // trong so, nen xuat tep thi thay du.
        //
        // Gio cau "so nay o lai may" nam trong TIEU DE tu dung
        // (setCustomTitle), va tieu de + danh sach hien cung nhau duoc.
        val ghiChu = getString(R.string.so_nay_o_lai_may) +
            if (dong.isEmpty()) "" else "\n" + getString(R.string.cham_de_xoa)

        AlertDialog.Builder(this)
            .setCustomTitle(tieuDe(getString(R.string.nhat_ky), ghiChu))
            .setAdapter(ArrayAdapter(this, android.R.layout.simple_list_item_1,
                dong.ifEmpty { listOf(getString(R.string.chua_co_ghi_chu)) })) { _, viTri ->
                // Quyen xoa la mot phan cua quyen so huu (SoNhatKy.xoa).
                // Ban cu co ham xoa nhung giao dien khong goi toi.
                if (dong.isEmpty()) return@setAdapter
                // ganDay() tra ve DUOI danh sach -> doi ve chi so trong so.
                hoiXoaGhiChu(soNhatKy.muc.size - cacMuc.size + viTri)
            }
            .setPositiveButton(R.string.them_ghi_chu) { _, _ -> themGhiChu() }
            .setNeutralButton(R.string.xuat_tep) { _, _ -> xinChoLuu() }
            .setNegativeButton(R.string.xong, null)
            .hien()
    }

    /**
     * Tieu de hai dong: ten hop thoai, va mot cau ghi chu nho ben duoi.
     *
     * Dung thay cho setMessage o nhung hop thoai CO danh sach - xem bug
     * so trong o [moNhatKy].
     */
    private fun tieuDe(ten: String, ghiChu: String): View =
        LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(24), dp(20), dp(24), dp(4))
            addView(TextView(this@MainActivity).apply {
                text = ten
                setTextAppearance(android.R.style.TextAppearance_Material_Title)
            })
            addView(TextView(this@MainActivity).apply {
                text = ghiChu
                setTextAppearance(android.R.style.TextAppearance_Material_Body1)
                setPadding(0, dp(6), 0, 0)
            })
        }

    private fun hoiXoaGhiChu(chiSo: Int) {
        val m = soNhatKy.muc.getOrNull(chiSo) ?: return moNhatKy()
        AlertDialog.Builder(this)
            .setTitle(R.string.xoa_ghi_chu_hoi)
            .setMessage(m.dong())
            .setPositiveButton(R.string.xoa) { _, _ ->
                soNhatKy.xoa(chiSo)
                soNhatKy.luu(this)
                moNhatKy()
            }
            .setNegativeButton(R.string.huy) { _, _ -> moNhatKy() }
            .hien()
    }

    private fun themGhiChu() {
        val oNoiDung = EditText(this).apply {
            hint = getString(R.string.hint_ghi_chu)
            inputType = InputType.TYPE_CLASS_TEXT or
                InputType.TYPE_TEXT_FLAG_MULTI_LINE
            minLines = 3
        }
        // O nay la CHU, khong phai thang diem. Xem `SoNhatKy` ve ly do:
        // mot con so chi co ich khi co gi do cong no lai, ma cong lai la
        // thu khong duoc lam.
        val oTheNao = EditText(this).apply {
            hint = getString(R.string.hint_the_nao)
            inputType = InputType.TYPE_CLASS_TEXT
        }
        val khoi = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(48, 24, 48, 0)
            addView(oNoiDung)
            addView(oTheNao)
        }

        // Cung cach voi them loi nhac: rong thi hop thoai KHONG dong, de
        // chu da go o o kia khong mat.
        val hop = AlertDialog.Builder(this)
            .setTitle(R.string.them_ghi_chu)
            .setView(khoi)
            .setPositiveButton(R.string.them, null)
            .setNegativeButton(R.string.huy) { _, _ -> moNhatKy() }
            .create()
        hop.setOnShowListener {
            hop.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener {
                val ok = soNhatKy.ghi(oNoiDung.text.toString(),
                    oTheNao.text.toString().ifBlank { null })
                if (!ok) {
                    oNoiDung.error = getString(R.string.hint_ghi_chu)
                    oNoiDung.requestFocus()
                    return@setOnClickListener
                }
                soNhatKy.luu(this)
                hop.dismiss()
                moNhatKy()
            }
        }
        hop.hien()
    }

    /**
     * Xuat so ra tep.
     *
     * --------------------------------------------------------------
     * VI SAO DI QUA TRINH CHON TEP CUA HE DIEU HANH
     * --------------------------------------------------------------
     *
     * App khong tu chon cho ghi, va khong gui tep cho ai. Nguoi dung mo
     * trinh chon cua he dieu hanh, tu chon thu muc, tu dat ten.
     *
     * Ho co the muon dua so cho bac si - do la viec cua ho, va no huu
     * ich. Nhung buoc do phai nam trong tay ho, khong nam trong code.
     *
     * ACTION_CREATE_DOCUMENT lam dung viec do: app khong duoc cap quyen
     * vao bat cu thu muc nao, chi duoc ghi vao dung cai tep nguoi dung
     * vua chi.
     */
    private fun xinChoLuu() {
        val i = Intent(Intent.ACTION_CREATE_DOCUMENT).apply {
            addCategory(Intent.CATEGORY_OPENABLE)
            type = "text/plain"
            putExtra(Intent.EXTRA_TITLE, "nhat-ky-flowy.txt")
        }
        try {
            startActivityForResult(i, MA_XUAT)
        } catch (_: Exception) {
            datTrangThai(getString(R.string.khong_xuat_duoc))
        }
    }

    override fun onActivityResult(ma: Int, ketQua: Int, data: Intent?) {
        super.onActivityResult(ma, ketQua, data)
        if (ma == MA_LICH && ketQua == RESULT_OK) {
            soLich = SoLich.doc(this)
            soLich.tim(data?.getStringExtra(LichActivity.KET_QUA_ID))?.let { batDauTuKeHoach(it) }
            return
        }
        if (ma != MA_XUAT || ketQua != RESULT_OK) return
        val uri: Uri = data?.data ?: return
        try {
            contentResolver.openOutputStream(uri)?.use {
                it.write(soNhatKy.xuatVanBan().toByteArray(Charsets.UTF_8))
            }
            datTrangThai(getString(R.string.da_xuat))
        } catch (e: Exception) {
            Log.w(TAG, "xuat nhat ky hong", e)
            datTrangThai(getString(R.string.khong_xuat_duoc))
        }
    }

    // ---------------------------------------------------------------
    // Quyen va giong doc
    // ---------------------------------------------------------------

    /**
     * May khong co giong Viet -> hoi MOT lan, co nut mo dung cho cai.
     *
     * Danh sach day du cac quyen nam trong Cai dat -> Kiem tra quyen.
     */
    private fun hoiCaiGiongViet() {
        if (daHoiGiongViet || isFinishing) return
        daHoiGiongViet = true
        tvTrangThai.text = getString(R.string.khong_co_giong_viet)
        AlertDialog.Builder(this)
            .setTitle(R.string.giong_viet_tieu_de)
            .setMessage(R.string.giong_viet_giai_thich)
            .setPositiveButton(R.string.mo_cai_dat) { _, _ ->
                Speaker.moCaiDatGiongDoc(this)
            }
            .setNegativeButton(R.string.de_sau, null)
            .hien()
    }

    override fun onRequestPermissionsResult(ma: Int, quyen: Array<out String>,
                                            ketQua: IntArray) {
        super.onRequestPermissionsResult(ma, quyen, ketQua)
        val duoc = ketQua.isNotEmpty() &&
            ketQua[0] == PackageManager.PERMISSION_GRANTED
        if (ma == KiemQuyen.MA_MICRO) {
            if (duoc && choNgheSauKhiCapQuyen) ngheMotCau()
            else if (!duoc) datTrangThai(getString(R.string.can_micro))
            choNgheSauKhiCapQuyen = false
        }
    }

    private fun dp(n: Int): Int = (n * resources.displayMetrics.density).toInt()

    companion object {
        /** Lenh mo san mot hop thoai khi man hinh nay len tien canh. */
        /** ID ke hoach can bat dau ngay khi man hinh nay len tien canh. */
        const val EXTRA_KE_HOACH = "ke_hoach"

        const val TAG = "Flowy"
        const val MA_XUAT = 7001
        const val MA_LICH = 7002

        /** So muc nhat ky hien trong hop thoai. Xuat tep thi lay het. */
        const val SO_MUC_HIEN = 30
    }
}
