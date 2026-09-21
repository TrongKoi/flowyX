package vn.adc2026.wayfinding

import android.app.Activity
import android.app.AlertDialog
import android.content.Context
import android.content.Intent
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.text.InputType
import android.view.Gravity
import android.view.View
import android.widget.ArrayAdapter
import android.widget.EditText
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.SeekBar
import android.widget.TextView
import java.util.Locale

/**
 * ====================================================================
 * CAI DAT (v5) - BA NHOM
 * ====================================================================
 *
 *   1. TAI KHOAN   - ai dang dung may nay, va cac thao tac voi tai khoan
 *   2. BAO MAT & DU LIEU - du lieu di dau, ra vao the nao, van ban phap ly
 *   3. HE THONG & TRO NANG - cach app hien ra va phan hoi
 *
 * ----- Vi sao gom lai thanh ba -----
 *
 * Ban v4 la mot danh sach phang muoi may muc, xep theo thu tu chung duoc
 * viet ra. Nguoi dung tim "doi co chu" phai doc het ca danh sach vi khong
 * co gi noi cho ho biet nen nhin o dau. Ba nhom la ba cau hoi khac nhau -
 * "toi la ai", "du lieu cua toi the nao", "app hien ra sao" - va gan nhu
 * moi thu can tim deu roi ro rang vao mot trong ba.
 *
 * Ba, khong phai nam: qua bon nhom thi ban than viec chon nhom lai thanh
 * mot buoc phai nghi.
 *
 * ----- Vi sao dung ra bang ma, khong bang XML -----
 *
 * Man hinh nay doi hinh theo trang thai (da dang nhap chua, co nguon suc
 * khoe khong, dang bat hay tat) va phai VE LAI TUC THI khi nguoi dung keo
 * thanh co chu. Voi XML thi moi lan doi la mot vong tim view va set thuoc
 * tinh; voi ma thi chi goi `ve()` mot lan.
 *
 * ----- Ngoai le co chu dich -----
 *
 * MUC NHAC nam o man hinh chinh chu khong o day - xem UIUX_QUYET_DINH cau 4.
 */
class CaiDatActivity : Activity() {

    private lateinit var s: AppSettings
    private var speaker: Speaker? = null

    /** Dang mo man hinh kiem quyen -> mo lai khi quay ve tu Cai dat he thong. */
    private var dangKiemQuyen = false
    private val tay = Handler(Looper.getMainLooper())

    private var goc: LinearLayout? = null

    /**
     * ----- Giu nguyen cho dang cuon (muc 3.2) -----
     *
     * Doi ngon ngu goi `recreate()`, doi phong chu goi `recreate()`, doi co
     * chu va muc rung goi `ve()`, va ca `onResume()` cung goi `ve()`. Moi
     * duong trong so do deu dung lai TOAN BO cay view, ke ca `ScrollView`.
     *
     * `ScrollView` o day duoc tao bang ma va khong co `id`, nen Android
     * khong luu duoc vi tri cuon cua no - co `id` no moi nam trong bang
     * trang thai ma `onSaveInstanceState` ghi lai. Vi vay moi lan doi mot
     * tuy chon nam o cuoi trang la man hinh nhay bat ve dau.
     *
     * Cach lam: tu nho lay so `scrollY` truoc khi dung lai cay view, roi
     * dat lai sau khi bo cuc xong. `scrollTo` goi ngay sau `setContentView`
     * khong an thua - luc do moi view con cao 0, cuon toi dau cung bi kep
     * ve 0.
     */
    private var cuon: ScrollView? = null
    private var yCuon = 0


    override fun attachBaseContext(moi: Context) {
        super.attachBaseContext(GiaoDien.boc(moi))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        GiaoDien.apTheme(this)
        super.onCreate(savedInstanceState)
        s = AppSettings(this)
        speaker = Speaker(this) { }.also { it.setRate(s.speechRate) }
        // `recreate()` cho Activity di qua onSaveInstanceState -> onCreate,
        // nen day la cho nhan lai cho cuon cu.
        yCuon = savedInstanceState?.getInt(KHOA_CUON) ?: 0
        ve()
    }

    override fun onSaveInstanceState(out: Bundle) {
        super.onSaveInstanceState(out)
        cuon?.let { yCuon = it.scrollY }
        out.putInt(KHOA_CUON, yCuon)
    }

    override fun onDestroy() {
        super.onDestroy()
        speaker?.close()
    }

    override fun onResume() {
        super.onResume()
        if (dangKiemQuyen) {
            dangKiemQuyen = false
            // Mot so trang thai (thong bao, TTS) cap nhat cham hon onResume.
            tay.postDelayed({ moKiemQuyen() }, 300)
        } else {
            ve()   // quay ve tu man hinh Suc khoe / Nhap lich: trang thai co the da doi
        }
    }

    // ================================================================
    // VE MAN HINH
    // ================================================================

    private fun ve() {
        // Nho cho cuon TRUOC khi bo cay view cu di.
        cuon?.let { yCuon = it.scrollY }

        val cot = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(18), dp(16), dp(18), dp(40))
        }
        goc = cot

        // --- hang tieu de ---
        cot.addView(LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            addView(ImageView(this@CaiDatActivity).apply {
                setImageResource(R.drawable.ic_quay_lai)
                setColorFilter(mau(R.color.chu_phu))
                val p = dp(8); setPadding(p, p, p, p)
                contentDescription = getString(R.string.quay_lai)
                background = GradientDrawable().apply {
                    shape = GradientDrawable.OVAL; setColor(mau(R.color.the))
                }
                setOnClickListener { Rung.nhe(it); finish() }
            }, LinearLayout.LayoutParams(dp(40), dp(40)).apply { marginEnd = dp(14) })
            addView(TextView(this@CaiDatActivity).apply {
                text = getString(R.string.cai_dat)
                textSize = 22f
                typeface = Typeface.DEFAULT_BOLD
                setTextColor(mau(R.color.chu))
                if (Build.VERSION.SDK_INT >= 28) isAccessibilityHeading = true
            }, LinearLayout.LayoutParams(-1, -2))
        }, LinearLayout.LayoutParams(-1, -2))

        nhomTaiKhoan(cot)
        nhomBaoMat(cot)
        nhomHeThong(cot)

        val c = ScrollView(this).apply {
            id = R.id.cuon_cai_dat
            setBackgroundColor(mau(R.color.nen)); isFillViewport = true
        }
        c.addView(cot)
        setContentView(c)
        cuon = c
        GiaoDien.apFont(cot, this)
        traLaiChoCuon(c)
    }

    /**
     * Dat lai `scrollY` sau khi bo cuc xong.
     *
     * Phai doi `onGlobalLayout`: truoc do moi view deu cao 0, nen
     * `scrollTo` bi kep ve 0. `post` khong du o lan ve dau tien.
     */
    private fun traLaiChoCuon(c: ScrollView) {
        if (yCuon <= 0) return
        val y = yCuon
        c.viewTreeObserver.addOnGlobalLayoutListener(
            object : android.view.ViewTreeObserver.OnGlobalLayoutListener {
                override fun onGlobalLayout() {
                    c.viewTreeObserver.removeOnGlobalLayoutListener(this)
                    c.scrollTo(0, y)
                }
            })
    }

    // ---------------------------------------------------------------
    // NHOM 1 - TAI KHOAN
    // ---------------------------------------------------------------

    private fun nhomTaiKhoan(cot: LinearLayout) {
        cot.addView(tenNhom(getString(R.string.cd_nhom_tai_khoan)), lp(26))
        val the = the()

        val phien = TaiKhoan.dangDangNhap(this)
        if (phien == null) {
            the.addView(dong(getString(R.string.cd_chua_dang_nhap), null) {
                startActivity(Intent(this, DangNhapActivity::class.java))
            })
        } else {
            // Dong dau: ten + email. Khong bam duoc - day la thong tin,
            // khong phai nut; lam no bam duoc chi de nguoi ta thu bam.
            the.addView(LinearLayout(this).apply {
                orientation = LinearLayout.VERTICAL
                setPadding(dp(16), dp(16), dp(16), dp(14))
                addView(TextView(this@CaiDatActivity).apply {
                    text = phien.hoTen
                    textSize = 17f
                    typeface = Typeface.DEFAULT_BOLD
                    setTextColor(mau(R.color.chu))
                })
                addView(TextView(this@CaiDatActivity).apply {
                    text = phien.email
                    textSize = 13f
                    setTextColor(mau(R.color.chu_phu))
                }, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(3) })
            }, LinearLayout.LayoutParams(-1, -2))
            the.addView(vach())

            the.addView(dong(getString(R.string.cd_doi_mat_khau), null) { hopDoiMatKhau() })
            the.addView(vach())
            the.addView(dong(getString(R.string.cd_ma_moi),
                getString(R.string.cd_ma_moi_phu)) { hoiMaMoi() })
            the.addView(vach())
            the.addView(dong(getString(R.string.cd_dang_xuat), null) { hoiDangXuat() })
            the.addView(vach())
            the.addView(dong(getString(R.string.cd_xoa_tai_khoan), null,
                doCanh = true) { hoiXoaTaiKhoan() })
        }
        cot.addView(the, lp(10))
    }

    private fun hopDoiMatKhau() {
        val oCu = oMatKhau(getString(R.string.cd_mk_cu))
        val oMoi = oMatKhau(getString(R.string.cd_mk_moi))
        val oLai = oMatKhau(getString(R.string.cd_mk_lai))
        val hop = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(24), dp(12), dp(24), 0)
            addView(oCu); addView(oMoi); addView(oLai)
        }
        AlertDialog.Builder(this)
            .setTitle(getString(R.string.cd_doi_mat_khau))
            .setView(hop)
            .setNegativeButton(R.string.huy, null)
            .setPositiveButton(R.string.luu) { _, _ ->
                val cu = oCu.text.toString()
                val moi = oMoi.text.toString()
                if (moi.length < KhoDuLieu.TOI_THIEU) {
                    bao(getString(R.string.dk_loi_ngan, KhoDuLieu.TOI_THIEU)); return@setPositiveButton
                }
                if (moi != oLai.text.toString()) {
                    bao(getString(R.string.dk_loi_khac_nhau)); return@setPositiveButton
                }
                val email = TaiKhoan.dangDangNhap(this)?.email ?: return@setPositiveButton
                val kho = KhoDuLieu(this)
                Thread {
                    // Kiem mat khau cu bang chinh duong dang nhap: neu chi
                    // doi ma khong hoi, ai cam may dang mo cung doi duoc.
                    val dung = kho.dangNhap(email, cu) != null
                    val xong = dung && kho.doiMatKhau(email, moi)
                    runOnUiThread {
                        bao(getString(if (xong) R.string.cd_da_doi_mk else R.string.cd_mk_cu_sai))
                        if (xong) Rung.xong(window.decorView)
                    }
                }.start()
            }
            .hien()
    }

    private fun hoiMaMoi() {
        AlertDialog.Builder(this)
            .setTitle(getString(R.string.cd_ma_moi))
            .setMessage(getString(R.string.cd_ma_moi_hoi))
            .setNegativeButton(R.string.huy, null)
            .setPositiveButton(getString(R.string.cd_ma_moi_lam)) { _, _ ->
                val ma = TaiKhoan.taoMaKhoiPhuc(this)
                AlertDialog.Builder(this)
                    .setTitle(getString(R.string.ma_tieu_de))
                    .setMessage(getString(R.string.qmk_ma_moi_noi_dung, ma))
                    .setCancelable(false)
                    .setPositiveButton(getString(R.string.ma_da_luu), null)
                    .hien()
            }
            .hien()
    }

    private fun hoiDangXuat() {
        AlertDialog.Builder(this)
            .setTitle(getString(R.string.cd_dang_xuat))
            .setMessage(getString(R.string.cd_dang_xuat_hoi))
            .setNegativeButton(R.string.huy, null)
            .setPositiveButton(getString(R.string.cd_dang_xuat)) { _, _ ->
                TaiKhoan.dangXuat(this)
                startActivity(Intent(this, DangNhapActivity::class.java)
                    .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TASK or Intent.FLAG_ACTIVITY_NEW_TASK))
                finish()
            }
            .hien()
    }

    private fun hoiXoaTaiKhoan() {
        AlertDialog.Builder(this)
            .setTitle(getString(R.string.cd_xoa_tai_khoan))
            .setMessage(getString(R.string.cd_xoa_1))
            .setNegativeButton(R.string.huy, null)
            .setPositiveButton(getString(R.string.qmk_xoa_tiep)) { _, _ ->
                // Lan hai bat GO DUNG CHU. Mot thao tac khong hoan tac duoc
                // thi hai lan bam nut van la hai lan bam nut - go chu buoc
                // nguoi dung dung lai va doc.
                val o = EditText(this).apply {
                    hint = getString(R.string.cd_xoa_go_chu)
                    inputType = InputType.TYPE_CLASS_TEXT
                    setTextColor(mau(R.color.chu)); setHintTextColor(mau(R.color.chu_phu))
                }
                AlertDialog.Builder(this)
                    .setTitle(getString(R.string.qmk_xoa_chac))
                    .setMessage(getString(R.string.cd_xoa_2, getString(R.string.cd_xoa_tu_khoa)))
                    .setView(LinearLayout(this).apply {
                        setPadding(dp(24), dp(8), dp(24), 0); addView(o)
                    })
                    .setNegativeButton(R.string.huy, null)
                    .setPositiveButton(getString(R.string.qmk_xoa_lam)) { _, _ ->
                        if (o.text.toString().trim().equals(
                                getString(R.string.cd_xoa_tu_khoa), ignoreCase = true)) {
                            TaiKhoan.xoaHet(this)
                            startActivity(Intent(this, KhoiDongActivity::class.java)
                                .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TASK
                                    or Intent.FLAG_ACTIVITY_NEW_TASK))
                            finish()
                        } else bao(getString(R.string.cd_xoa_sai_chu))
                    }
                    .hien()
            }
            .hien()
    }

    // ---------------------------------------------------------------
    // NHOM 2 - BAO MAT & DU LIEU
    // ---------------------------------------------------------------

    private fun nhomBaoMat(cot: LinearLayout) {
        cot.addView(tenNhom(getString(R.string.cd_nhom_bao_mat)), lp(26))
        val the = the()

        // Dong trang thai ma hoa: khong bam duoc, chi bao su that.
        val chac = MaHoa.nguyenVen(this)
        the.addView(LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(dp(16), dp(15), dp(16), dp(15))
            addView(ImageView(this@CaiDatActivity).apply {
                setImageResource(R.drawable.ic_khoa)
                setColorFilter(mau(if (chac) R.color.xanh_xong else R.color.cam))
                importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
            }, LinearLayout.LayoutParams(dp(20), dp(20)).apply {
                topMargin = dp(2); marginEnd = dp(12)
            })
            addView(TextView(this@CaiDatActivity).apply {
                text = getString(if (chac) R.string.cd_ma_hoa_tot else R.string.cd_ma_hoa_yeu)
                textSize = 13.5f
                setLineSpacing(0f, 1.4f)
                setTextColor(mau(R.color.chu_phu))
            }, LinearLayout.LayoutParams(-1, -2))
        }, LinearLayout.LayoutParams(-1, -2))
        the.addView(vach())

        // MUC 3.4 - "Nhap lich" da chuyen han sang tab Lich.
        //
        // Truoc day no nam o CA HAI cho: mot nut tren thanh tieu de cua
        // tab Lich, va mot dong o day. Hai duong vao cho cung mot viec
        // nghia la nguoi dung phai nho no nam o dau - va dat trong Cai dat
        // con gui sai tin hieu: nhap lich khong phai mot tuy chon he
        // thong, no la mot thao tac lam voi lich, ngay o cho co lich.
        //
        // Cai dat giu lai nhung thu lam MOT LAN roi thoi. Nhap lich la
        // viec lap lai moi hoc ky, moi du an.

        the.addView(dong(getString(R.string.cd_suc_khoe),
            getString(if (SucKhoe.dangBat(this)) R.string.cd_dang_bat
                      else R.string.cd_dang_tat)) {
            startActivity(Intent(this, SucKhoeActivity::class.java))
        })
        the.addView(vach())

        the.addView(dong(getString(R.string.cd_xuat),
            getString(R.string.cd_xuat_phu)) { hoiXuat() })
        the.addView(vach())

        the.addView(dong(getString(R.string.pl_dieu_khoan), null) {
            moPhapLy(PhapLyActivity.DIEU_KHOAN)
        })
        the.addView(vach())
        the.addView(dong(getString(R.string.pl_rieng_tu), null) {
            moPhapLy(PhapLyActivity.RIENG_TU)
        })

        cot.addView(the, lp(10))
    }

    private fun moPhapLy(phan: String) {
        startActivity(Intent(this, PhapLyActivity::class.java)
            .putExtra(PhapLyActivity.PHAN, phan))
    }

    private fun hoiXuat() {
        AlertDialog.Builder(this)
            .setTitle(getString(R.string.cd_xuat))
            .setMessage(getString(R.string.cd_xuat_canh_bao))
            .setNegativeButton(R.string.huy, null)
            .setPositiveButton(getString(R.string.cd_xuat_chon_noi)) { _, _ ->
                // Storage Access Framework: NGUOI DUNG chon noi luu. App
                // khong xin quyen o dia nao, va khong tu ghi vao thu muc
                // dung chung - tep di dau la do ho quyet dinh.
                val it2 = Intent(Intent.ACTION_CREATE_DOCUMENT)
                    .addCategory(Intent.CATEGORY_OPENABLE)
                    .setType(XuatDuLieu.LOAI_MIME)
                    .putExtra(Intent.EXTRA_TITLE, XuatDuLieu.tenTep())
                try {
                    startActivityForResult(it2, MA_TAO_TEP)
                } catch (_: Exception) {
                    bao(getString(R.string.cd_xuat_khong_mo_duoc))
                }
            }
            .hien()
    }

    override fun onActivityResult(ma: Int, ketQua: Int, du: Intent?) {
        super.onActivityResult(ma, ketQua, du)
        if (ma != MA_TAO_TEP || ketQua != RESULT_OK) return
        val noi: Uri = du?.data ?: return
        Thread {
            val duoc = try {
                val chu = XuatDuLieu.goi(this)
                contentResolver.openOutputStream(noi)?.use { it.write(chu.toByteArray()) } != null
            } catch (_: Exception) { false }
            runOnUiThread {
                bao(getString(if (duoc) R.string.cd_xuat_xong else R.string.cd_xuat_hong))
                if (duoc) Rung.xong(window.decorView)
            }
        }.start()
    }

    // ---------------------------------------------------------------
    // NHOM 3 - HE THONG & TRO NANG
    // ---------------------------------------------------------------

    private fun nhomHeThong(cot: LinearLayout) {
        cot.addView(tenNhom(getString(R.string.cd_nhom_he_thong)), lp(26))

        // --- giao dien: sang / toi / theo may ---
        //
        // Dat TREN ngon ngu vi day la thu nguoi ta doi thu nhieu nhat va
        // doi lai ngay neu khong thich; de no o cuoi trang la bat cuon
        // qua ca nhom chi de thu mot lua chon.
        val the0 = the()
        the0.addView(nhanTrong(getString(R.string.cd_theme)))
        the0.addView(hangChip(
            CheDoToi.DANH_SACH.map { getString(it.second) },
            CheDoToi.viTri(this)) { i ->
            CheDoToi.doi(this, CheDoToi.DANH_SACH[i].first)
            // API >= 31: he thong tu ve lai, nhung rieng man hinh nay
            // dang dung bang ma nen phai tu ve de hang chip danh dau lai
            // dung o vua chon.
            if (android.os.Build.VERSION.SDK_INT >= 31) ve()
        })
        the0.addView(TextView(this).apply {
            text = getString(R.string.cd_theme_mo_ta)
            textSize = 13f * s.coChu
            setLineSpacing(0f, 1.45f)
            setTextColor(mau(R.color.chu_phu))
            setPadding(dp(16), 0, dp(16), dp(14))
        })
        cot.addView(the0, lp(10))

        // --- ngon ngu ---
        val the1 = the()
        the1.addView(nhanTrong(getString(R.string.cd_ngon_ngu)))
        the1.addView(hangChip(NgonNgu.DANH_SACH.map { it.second }, viTriNgonNgu()) { i ->
            val ma = NgonNgu.DANH_SACH[i].first
            if (ma != s.ngonNgu) NgonNgu.doi(this, ma)   // tu goi recreate()
        })
        cot.addView(the1, lp(10))

        // --- phong chu ---
        val the2 = the()
        the2.addView(nhanTrong(getString(R.string.cd_phong_chu)))
        the2.addView(hangChip(
            listOf(getString(R.string.cd_chu_lexend), getString(R.string.cd_chu_andika),
                   getString(R.string.cd_chu_inter), getString(R.string.cd_chu_he_thong)),
            viTriChu()) { i ->
            s.kieuChu = listOf(AppSettings.CHU_LEXEND, AppSettings.CHU_ANDIKA,
                               AppSettings.CHU_INTER, AppSettings.CHU_HE_THONG)[i]
            // Theme cua hop thoai he thong doi theo font -> phai recreate.
            recreate()
        })
        the2.addView(TextView(this).apply {
            text = getString(R.string.cd_chu_mau)
            textSize = 14f * s.coChu
            setLineSpacing(0f, 1.45f)
            setTextColor(mau(R.color.chu_phu))
            setPadding(dp(16), 0, dp(16), dp(14))
        })
        cot.addView(the2, lp(10))

        // --- co chu ---
        val the3 = the()
        the3.addView(nhanTrong(getString(R.string.cd_co_chu)))
        the3.addView(thanhTruot(
            soMuc = 6, hienTai = ((s.coChu - CO_MIN) / CO_BUOC).toInt(),
            nhanTrai = getString(R.string.cd_co_nho), nhanPhai = getString(R.string.cd_co_to),
            moTa = { i -> getString(R.string.cd_co_phan_tram,
                ((CO_MIN + i * CO_BUOC) * 100).toInt()) }) { i ->
            s.coChu = CO_MIN + i * CO_BUOC
            // Ve lai NGAY: nguoi dung thay co chu that trong luc con dang
            // cam thanh truot, khong phai doan roi bam Luu.
            ve()
        })
        cot.addView(the3, lp(10))

        // --- muc rung ---
        val the4 = the()
        the4.addView(nhanTrong(getString(R.string.cd_muc_rung)))
        the4.addView(thanhTruot(
            soMuc = 4, hienTai = s.mucRung,
            nhanTrai = getString(R.string.cd_rung_tat), nhanPhai = getString(R.string.cd_rung_manh),
            moTa = { i -> getString(when (i) {
                0 -> R.string.cd_rung_0; 1 -> R.string.cd_rung_1
                2 -> R.string.cd_rung_2; else -> R.string.cd_rung_3 }) }) { i ->
            s.mucRung = i
            // Rung THU ngay muc vua chon - mo ta bang chu khong thay duoc
            // "nhe" khac "vua" bao nhieu.
            goc?.let { Rung.rung(it, i) }
        })
        cot.addView(the4, lp(10))

        // --- nhac viec (muc 3.3) ---
        //
        // Mot nhom rieng, dat TREN "phan hoi & giong doc". Hai muc duoi
        // do tra loi cau "app phan hoi thao tac cua toi the nao"; nhom nay
        // tra loi cau khac han: "khi nao app duoc lam phien toi". Truoc
        // day ca hai tron lam mot, va ket qua la muon tat mot cai thi tat
        // luon ca cai kia.
        val theNhac = the()
        theNhac.addView(nhanTrong(getString(R.string.cd_nhom_nhac)))

        // Gio yen tinh
        theNhac.addView(dongCongTac(getString(R.string.cd_gio_yen),
            getString(R.string.cd_gio_yen_phu), s.gioYenBat) { bat ->
            s.gioYenBat = bat; ve()
        })
        if (s.gioYenBat) {
            theNhac.addView(vach())
            theNhac.addView(dong(getString(R.string.cd_gio_yen_tu),
                Lich.gioPhut(s.gioYenTu)) {
                BoChonGio.hien(this, getString(R.string.cd_gio_yen_tu), s.gioYenTu) { p ->
                    s.gioYenTu = p; ve()
                }
            })
            theNhac.addView(vach())
            theNhac.addView(dong(getString(R.string.cd_gio_yen_den),
                Lich.gioPhut(s.gioYenDen)) {
                BoChonGio.hien(this, getString(R.string.cd_gio_yen_den), s.gioYenDen) { p ->
                    s.gioYenDen = p; ve()
                }
            })
        }

        // Nhac truoc phien
        theNhac.addView(vach())
        theNhac.addView(nhanTrong(getString(R.string.cd_nhac_truoc)))
        theNhac.addView(hangChip(
            NhacCaiDat.TRUOC_PHIEN.map {
                if (it == 0) getString(R.string.cd_nhac_dung_gio) else Lich.moTaPhut(it, this)
            },
            NhacCaiDat.TRUOC_PHIEN.indexOf(s.nhacTruocPhien).coerceAtLeast(0)) { i ->
            s.nhacTruocPhien = NhacCaiDat.TRUOC_PHIEN[i]
        })

        // Nhac lai
        theNhac.addView(vach())
        theNhac.addView(nhanTrong(getString(R.string.cd_nhac_lai)))
        theNhac.addView(hangChip(
            NhacCaiDat.NHAC_LAI.map {
                if (it == 0) getString(R.string.cd_khong_nhac_lai) else Lich.moTaPhut(it, this)
            },
            NhacCaiDat.NHAC_LAI.indexOf(s.nhacLai).coerceAtLeast(0)) { i ->
            s.nhacLai = NhacCaiDat.NHAC_LAI[i]
        })

        // Am khan
        theNhac.addView(vach())
        theNhac.addView(dongCongTac(getString(R.string.cd_am_khan),
            getString(R.string.cd_am_khan_phu), s.amKhanChoViecTre) { bat ->
            s.amKhanChoViecTre = bat
        })
        cot.addView(theNhac, lp(10))

        // --- phan hoi & giong doc ---
        val the5 = the()
        the5.addView(nhanTrong(getString(R.string.cd_phan_hoi)))
        the5.addView(hangChip(
            listOf(getString(R.string.ph_ca_hai_nhan), getString(R.string.ph_chi_tieng_nhan),
                   getString(R.string.ph_chi_rung_nhan)),
            when (s.feedbackMode) {
                AppSettings.MODE_SPEECH_ONLY -> 1
                AppSettings.MODE_HAPTIC_ONLY -> 2
                else -> 0
            }) { i ->
            s.feedbackMode = when (i) {
                1 -> AppSettings.MODE_SPEECH_ONLY
                2 -> AppSettings.MODE_HAPTIC_ONLY
                else -> AppSettings.MODE_BOTH
            }
            ve()
        })
        if (s.useSpeech) {
            the5.addView(vach())
            the5.addView(nhanTrong(getString(R.string.cd_toc_do_doc)))
            the5.addView(thanhTruot(
                soMuc = 14, hienTai = ((s.speechRate - TOC_DO_MIN) * 10).toInt(),
                nhanTrai = getString(R.string.cd_cham), nhanPhai = getString(R.string.cd_nhanh),
                moTa = { i -> getString(R.string.toc_do_doc,
                    String.format(Locale.US, "%.1f", TOC_DO_MIN + i / 10f).replace('.', ',')) }) { i ->
                s.speechRate = TOC_DO_MIN + i / 10f
                speaker?.setRate(s.speechRate)
            })
            the5.addView(vach())
            the5.addView(dong(getString(R.string.cd_thu_giong), null) {
                speaker?.say(getString(R.string.cau_thu_giong), urgent = true)
            })
        }
        cot.addView(the5, lp(10))

        // --- quyen va phien laptop ---
        val the6 = the()
        the6.addView(dong(getString(R.string.cd_kiem_quyen),
            getString(R.string.cd_kiem_quyen_phu)) { moKiemQuyen() })
        the6.addView(vach())
        the6.addView(dong(getString(R.string.cd_phien_laptop),
            getString(R.string.cd_phien_laptop_phu)) { hopLaptop() })
        cot.addView(the6, lp(10))

        cot.addView(TextView(this).apply {
            text = getString(R.string.cd_phien_ban, phienBan())
            textSize = 12f
            gravity = Gravity.CENTER
            setTextColor(mau(R.color.chu_phu))
        }, lp(24))
    }

    private fun hopLaptop() {
        val o = EditText(this).apply {
            setText(s.serverUrl)
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_URI
            setTextColor(mau(R.color.chu)); setHintTextColor(mau(R.color.chu_phu))
        }
        AlertDialog.Builder(this)
            .setTitle(getString(R.string.cd_phien_laptop))
            .setMessage(getString(R.string.cd_phien_laptop_giai_thich))
            .setView(LinearLayout(this).apply {
                setPadding(dp(24), dp(8), dp(24), 0); addView(o)
            })
            .setNegativeButton(R.string.huy, null)
            .setNeutralButton(getString(R.string.cd_mo_phien)) { _, _ ->
                s.serverUrl = o.text.toString()
                startActivity(Intent(this, MainActivity::class.java))
            }
            .setPositiveButton(R.string.luu) { _, _ ->
                s.serverUrl = o.text.toString()
                bao(getString(R.string.da_luu))
            }
            .hien()
    }

    private fun viTriNgonNgu(): Int =
        NgonNgu.DANH_SACH.indexOfFirst { it.first == s.ngonNgu }.coerceAtLeast(0)

    private fun viTriChu(): Int = when (s.kieuChu) {
        AppSettings.CHU_ANDIKA -> 1
        AppSettings.CHU_INTER -> 2
        AppSettings.CHU_HE_THONG -> 3
        else -> 0
    }

    private fun phienBan(): String = try {
        packageManager.getPackageInfo(packageName, 0).versionName ?: "5.0"
    } catch (_: Exception) { "5.0" }

    // ================================================================
    // QUYEN (giu nguyen tu v4)
    // ================================================================

    private fun moKiemQuyen() {
        if (isFinishing) return
        val ds = KiemQuyen.danhSach(this, speaker)
        val thieu = ds.count { !it.daCo && !it.tuyChon && !it.chuaBiet }

        AlertDialog.Builder(this)
            .setCustomTitle(tieuDeHop(getString(R.string.kiem_quyen_tieu_de),
                getString(if (thieu == 0) R.string.kiem_quyen_du
                          else R.string.kiem_quyen_thieu)))
            .setAdapter(ArrayAdapter(this, android.R.layout.simple_list_item_1,
                ds.map { it.dong() })) { _, viTri ->
                val muc = ds[viTri]
                if (muc.daCo) { moKiemQuyen(); return@setAdapter }
                dangKiemQuyen = true
                KiemQuyen.xuLy(this, muc, speaker)
            }
            .setPositiveButton(R.string.xong, null)
            .hien()
    }

    override fun onRequestPermissionsResult(ma: Int, quyen: Array<out String>, ketQua: IntArray) {
        super.onRequestPermissionsResult(ma, quyen, ketQua)
        if (dangKiemQuyen) {
            dangKiemQuyen = false
            moKiemQuyen()
        }
    }

    private fun tieuDeHop(ten: String, ghiChu: String): View =
        LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(24), dp(20), dp(24), dp(4))
            addView(TextView(this@CaiDatActivity).apply {
                text = ten
                textSize = 19f
                typeface = Typeface.DEFAULT_BOLD
                setTextColor(mau(R.color.chu))
            })
            addView(TextView(this@CaiDatActivity).apply {
                text = ghiChu
                textSize = 13.5f
                setTextColor(mau(R.color.chu_phu))
                setPadding(0, dp(6), 0, 0)
            })
        }

    // ================================================================
    // KHUON NHO
    // ================================================================

    /** Ten nhom: chu nho, in hoa, khong nam trong the - no la nhan cua the. */
    private fun tenNhom(ten: String) = TextView(this).apply {
        text = ten
        textSize = 11.5f
        typeface = Typeface.DEFAULT_BOLD
        letterSpacing = 0.07f
        setPadding(dp(6), 0, 0, dp(2))
        setTextColor(mau(R.color.chu_phu))
        if (Build.VERSION.SDK_INT >= 28) isAccessibilityHeading = true
    }

    private fun the() = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        background = GradientDrawable().apply {
            cornerRadius = dp(20).toFloat()
            setColor(mau(R.color.the))
            setStroke(dp(1), mau(R.color.vien))
        }
    }

    private fun vach() = View(this).apply {
        setBackgroundColor(mau(R.color.vien))
        layoutParams = LinearLayout.LayoutParams(-1, Math.max(1, dp(1) / 2)).apply {
            marginStart = dp(16)
        }
    }

    private fun nhanTrong(s2: String) = TextView(this).apply {
        text = s2
        textSize = 11.5f
        typeface = Typeface.DEFAULT_BOLD
        letterSpacing = 0.05f
        setPadding(dp(16), dp(15), dp(16), dp(2))
        setTextColor(mau(R.color.chu_phu))
    }

    /** Mot dong bam duoc: ten, dong phu, va mui ten. */
    private fun dong(ten: String, phu: String?, doCanh: Boolean = false,
                     khi: () -> Unit) = LinearLayout(this).apply {
        orientation = LinearLayout.HORIZONTAL
        gravity = Gravity.CENTER_VERTICAL
        minimumHeight = dp(56)
        setPadding(dp(16), dp(13), dp(16), dp(13))
        isClickable = true
        setOnClickListener { Rung.nhe(it); khi() }
        val cot = LinearLayout(this@CaiDatActivity).apply {
            orientation = LinearLayout.VERTICAL
        }
        cot.addView(TextView(this@CaiDatActivity).apply {
            text = ten
            textSize = 15.5f
            setTextColor(mau(if (doCanh) R.color.do_xoa else R.color.chu))
        })
        if (phu != null) cot.addView(TextView(this@CaiDatActivity).apply {
            text = phu
            textSize = 12.5f
            setLineSpacing(0f, 1.35f)
            setTextColor(mau(R.color.chu_phu))
        }, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(3) })
        addView(cot, LinearLayout.LayoutParams(0, -2, 1f))
        contentDescription = if (phu == null) ten else "$ten, $phu"
    }

    /**
     * Mot dong co cong tac bat/tat ben phai.
     *
     * Dung `Switch` cua he thong chu khong ve tay: cong tac la thu nguoi
     * dung da biet cach doc tu moi app khac, va trinh doc man hinh cung
     * da biet doc no. Mau lay tu `colors.xml` nen ban dem tu dung.
     *
     * Ca dong bam duoc, khong chi rieng cai cong tac - vung cham 56dp
     * thay vi 32dp, va khong phai ngam trung.
     */
    private fun dongCongTac(ten: String, phu: String?, bat: Boolean,
                            doi: (Boolean) -> Unit) = LinearLayout(this).apply {
        orientation = LinearLayout.HORIZONTAL
        gravity = Gravity.CENTER_VERTICAL
        minimumHeight = dp(56)
        setPadding(dp(16), dp(13), dp(16), dp(13))
        val cot = LinearLayout(this@CaiDatActivity).apply {
            orientation = LinearLayout.VERTICAL
        }
        cot.addView(TextView(this@CaiDatActivity).apply {
            text = ten
            textSize = 15.5f
            setTextColor(mau(R.color.chu))
        })
        if (phu != null) cot.addView(TextView(this@CaiDatActivity).apply {
            text = phu
            textSize = 12.5f
            setLineSpacing(0f, 1.35f)
            setTextColor(mau(R.color.chu_phu))
        }, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(3) })
        addView(cot, LinearLayout.LayoutParams(0, -2, 1f))

        val ct = android.widget.Switch(this@CaiDatActivity).apply {
            isChecked = bat
            contentDescription = ten
            setOnCheckedChangeListener { v, moi -> Rung.nhe(v); doi(moi) }
        }
        addView(ct, LinearLayout.LayoutParams(-2, -2).apply { marginStart = dp(10) })
        isClickable = true
        setOnClickListener { ct.isChecked = !ct.isChecked }
        contentDescription = if (phu == null) ten else "$ten, $phu"
    }

    /** Hang chip chon-mot: nhin thay het lua chon, khong phai mo menu. */
    private fun hangChip(ten: List<String>, dangChon: Int, doi: (Int) -> Unit): View {
        val hang = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(dp(12), dp(8), dp(12), dp(14))
        }
        for ((i, t) in ten.withIndex()) {
            val chon = i == dangChon
            hang.addView(TextView(this).apply {
                text = t
                textSize = 13.5f
                gravity = Gravity.CENTER
                minHeight = dp(44)
                includeFontPadding = false
                setPadding(dp(6), dp(11), dp(6), dp(11))
                typeface = if (chon) Typeface.DEFAULT_BOLD else Typeface.DEFAULT
                setTextColor(mau(if (chon) R.color.chu_tren_nhan else R.color.chu))
                background = GradientDrawable().apply {
                    cornerRadius = dp(13).toFloat()
                    setColor(mau(if (chon) R.color.nhan else R.color.the_2))
                }
                setOnClickListener { if (!chon) { Rung.nhe(it); doi(i) } }
                contentDescription = t + ", " +
                    getString(if (chon) R.string.da_chon else R.string.chua_chon)
            }, LinearLayout.LayoutParams(0, -2, 1f).apply { marginStart = if (i == 0) 0 else dp(7) })
        }
        return hang
    }

    /**
     * Thanh truot nac: `soMuc` nac, co dong chu mo ta nac dang chon.
     *
     * Khong dung phan tram tron: moi nac phai la mot lua chon co ten goi,
     * vi "83%" khong noi len dieu gi con "Vua" thi co.
     */
    private fun thanhTruot(soMuc: Int, hienTai: Int, nhanTrai: String, nhanPhai: String,
                           moTa: (Int) -> String, doi: (Int) -> Unit): View {
        val cot = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(16), dp(2), dp(16), dp(14))
        }
        val tv = TextView(this).apply {
            text = moTa(hienTai.coerceIn(0, soMuc - 1))
            textSize = 13.5f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(mau(R.color.chu))
        }
        cot.addView(tv)

        val sb = SeekBar(this).apply {
            max = soMuc - 1
            progress = hienTai.coerceIn(0, soMuc - 1)
            setPadding(0, dp(10), 0, dp(6))
        }
        sb.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(b: SeekBar?, p: Int, tuNguoiDung: Boolean) {
                tv.text = moTa(p)
                if (tuNguoiDung) doi(p)
            }
            override fun onStartTrackingTouch(b: SeekBar?) = Unit
            override fun onStopTrackingTouch(b: SeekBar?) = Unit
        })
        cot.addView(sb, LinearLayout.LayoutParams(-1, -2))

        cot.addView(LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
            addView(TextView(this@CaiDatActivity).apply {
                text = nhanTrai; textSize = 11.5f; setTextColor(mau(R.color.chu_phu))
            }, LinearLayout.LayoutParams(0, -2, 1f))
            addView(TextView(this@CaiDatActivity).apply {
                text = nhanPhai; textSize = 11.5f; gravity = Gravity.END
                setTextColor(mau(R.color.chu_phu))
            }, LinearLayout.LayoutParams(0, -2, 1f))
        }, LinearLayout.LayoutParams(-1, -2))
        return cot
    }

    private fun oMatKhau(goiY: String) = EditText(this).apply {
        hint = goiY
        inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD
        setTextColor(mau(R.color.chu)); setHintTextColor(mau(R.color.chu_phu))
    }

    private fun bao(chu: String) = ThongBao.hien(this, chu)

    private fun lp(tren: Int) = LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(tren) }
    private fun dp(n: Int) = (n * resources.displayMetrics.density).toInt()
    private fun mau(id: Int) = resources.getColor(id, theme)

    private companion object {
        const val MA_TAO_TEP = 8801
        const val TOC_DO_MIN = 0.7f
        /** 0,90 .. 1,15 - sau nac, buoc 0,05. Xem GiaoDien.apCoChu. */
        const val CO_MIN = 0.90f
        const val CO_BUOC = 0.05f

        /** Khoa mang `scrollY` qua `recreate()` khi doi ngon ngu / phong chu. */
        const val KHOA_CUON = "y_cuon"
    }
}
