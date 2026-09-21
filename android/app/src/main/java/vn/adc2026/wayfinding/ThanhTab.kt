package vn.adc2026.wayfinding

import android.animation.ValueAnimator
import android.annotation.SuppressLint
import android.app.Activity
import android.content.Intent
import android.view.MotionEvent
import android.view.View
import android.view.ViewGroup
import android.view.animation.DecelerateInterpolator
import android.widget.ImageView
import android.widget.TextView

/**
 * ====================================================================
 * THANH TAB DUOI (v5) - "KINH LONG"
 * ====================================================================
 *
 * Noi day MOT cho cho moi man hinh co tab. Ba thay doi so voi v4:
 *
 *   1. MOT VIEN THUOC DUNG CHUNG cho ca nam tab, TRUOT tu tab cu sang
 *      tab moi - thay vi tat o cho nay, bat o cho kia.
 *   2. KEO NGANG tren thanh tab: vien thuoc bam theo ngon tay, co gian
 *      khi bi keo, va rung moi lan vuot qua mot tab.
 *   3. Nen kinh (xem drawable/nen_kinh.xml).
 *
 * ----- Vien thuoc truot QUA RANH GIOI HAI ACTIVITY -----
 *
 * Moi tab la mot Activity rieng, nen tab cu bien mat truoc khi tab moi
 * ve xong - khong Activity nao "thay" duoc ca hai dau de chay hoat hinh.
 *
 * Cach lam: Activity di TRUYEN LAI chi so tab cu qua Intent (`TU_TAB`).
 * Activity den dat vien thuoc o cho tab CU roi truot sang cho cua minh.
 * Vi hai Activity chuyen canh khong co hieu ung (FLAG_ACTIVITY_NO_ANIMATION)
 * va thanh tab hai ben giong het nhau, mat nguoi doc ca hai khung hinh do
 * la MOT thanh tab lien tuc co vien thuoc dang truot.
 *
 * ----- Keo ngang: vi sao them mot cach lam nua -----
 *
 * Cham de doi tab van la cach chinh. Keo them vao vi hai ly do:
 *
 *   · Ngon cai o tay dang cam may quet ngang de hon la nhac len cham
 *     dung o mot o rong 72 dp.
 *   · Keo cho phep DOI Y: thay vien thuoc dang di toi tab minh khong dinh
 *     toi thi keo nguoc lai, tha ra, khong co gi xay ra. Cham thi khong
 *     rut lai duoc - da vao man hinh khac roi.
 *
 * Rung theo tung nac (`Rung.rung(v, 1)` moi lan qua mot tab, `Rung.xong`
 * khi chot) bien thanh tab thanh thu dem duoc bang ngon tay ma khong can
 * nhin - huu ich khi dang di bo, va khi mat con dang o cho khac.
 */
object ThanhTab {

    const val VIEC = 0
    const val LICH = 1
    const val FOCUS = 2
    const val NHAT_KY = 3
    const val MEETY = 4

    /** Chi so tab vua roi, gui sang Activity ke tiep de vien thuoc truot tiep. */
    const val TU_TAB = "tu_tab"

    private data class Tab(val khoi: Int, val pill: Int, val icon: Int, val nhan: Int, val lop: Class<*>)

    private val TAB = listOf(
        Tab(R.id.tab_viec, R.id.tab_viec_pill, R.id.tab_viec_icon, R.id.tab_viec_nhan, ViecCanLamActivity::class.java),
        Tab(R.id.tab_lich, R.id.tab_lich_pill, R.id.tab_lich_icon, R.id.tab_lich_nhan, LichActivity::class.java),
        Tab(R.id.tab_focus, R.id.tab_focus_pill, R.id.tab_focus_icon, R.id.tab_focus_nhan, FocusActivity::class.java),
        Tab(R.id.tab_nhat_ky, R.id.tab_nhat_ky_pill, R.id.tab_nhat_ky_icon, R.id.tab_nhat_ky_nhan, NhatKyActivity::class.java),
        Tab(R.id.tab_meety, R.id.tab_meety_pill, R.id.tab_meety_icon, R.id.tab_meety_nhan, MeetyActivity::class.java),
    )

    @SuppressLint("ClickableViewAccessibility")
    fun noi(a: Activity, dangChon: Int) {
        val vienThuoc = a.findViewById<View>(R.id.tab_vien_thuoc)

        TAB.forEachIndexed { i, t ->
            val khoi = a.findViewById<View>(t.khoi) ?: return@forEachIndexed
            val chon = i == dangChon
            a.findViewById<ImageView>(t.icon)?.setColorFilter(
                a.resources.getColor(if (chon) R.color.tab_chon else R.color.chu_phu, a.theme))
            a.findViewById<TextView>(t.nhan)?.visibility = if (chon) View.VISIBLE else View.INVISIBLE
            // Pill rieng cua tung tab gio chi con la KHUNG DO VI TRI cho
            // vien thuoc dung chung - khong con nen rieng nua.
            a.findViewById<View>(t.pill)?.background = null
            khoi.isSelected = chon
            khoi.contentDescription = a.getString(
                if (chon) R.string.tab_dang_chon else R.string.tab_chua_chon,
                a.findViewById<TextView>(t.nhan)?.text ?: "")
            khoi.setOnClickListener { if (!chon) { Rung.nhe(it); mo(a, i) } }

            // Cham giu -> vien thuoc phinh nhe. Chi cho tab DANG CHON:
            // vien thuoc nam o day, phinh no khi nguoi dung dang giu mot
            // tab khac se la mot chuyen dong o sai cho.
            if (chon && vienThuoc != null) {
                khoi.setOnTouchListener { v, e ->
                    when (e.actionMasked) {
                        MotionEvent.ACTION_DOWN -> nhanGiu(vienThuoc, true)
                        MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL ->
                            nhanGiu(vienThuoc, false)
                    }
                    // KHONG nuot su kien: `onClick` va bo keo ngang o
                    // `batKeo` van phai chay binh thuong.
                    false
                }
            }
        }

        if (vienThuoc == null) return
        val tuTab = a.intent.getIntExtra(TU_TAB, -1)
        datCho(a, vienThuoc, dangChon, tuTab)
        batKeo(a, vienThuoc, dangChon)
    }

    /**
     * Dat vien thuoc vao dung cho tab dang chon.
     *
     * Phai doi bo cuc xong moi biet toa do - truoc `onGlobalLayout` thi moi
     * view deu rong 0. `post` khong du: o lan mo dau tien, view chua qua
     * vong do nao.
     */
    private fun datCho(a: Activity, vienThuoc: View, den: Int, tu: Int) {
        val moc = a.findViewById<View>(TAB[den].pill) ?: return
        moc.viewTreeObserver.addOnGlobalLayoutListener(
            object : android.view.ViewTreeObserver.OnGlobalLayoutListener {
                override fun onGlobalLayout() {
                    moc.viewTreeObserver.removeOnGlobalLayoutListener(this)
                    val x = xCuaTab(a, den) ?: return
                    vienThuoc.translationY = 0f
                    if (tu < 0 || tu == den || tu !in TAB.indices) {
                        vienThuoc.translationX = x
                        noNhe(vienThuoc)
                    } else {
                        // Bat dau o cho tab CU roi truot toi - xem ghi chu
                        // dau file ve viec truot qua ranh gioi Activity.
                        vienThuoc.translationX = xCuaTab(a, tu) ?: x
                        truotKinhLong(vienThuoc, x, Math.abs(den - tu))
                    }
                }
            })
    }

    private fun xCuaTab(a: Activity, i: Int): Float? {
        val pill = a.findViewById<View>(TAB[i].pill) ?: return null
        val khoi = a.findViewById<View>(TAB[i].khoi) ?: return null
        if (khoi.width == 0) return null
        return (khoi.x + pill.x)
    }

    /**
     * ================================================================
     * TRUOT KIEU "KINH LONG" (muc 1.3)
     * ================================================================
     *
     * Ban truoc truot bang mot `translationX` deu voi
     * `DecelerateInterpolator`. Dung ky thuat, nhung nhin ra la mot HINH
     * KHOI DI CHUYEN - mot vien thuoc cung truot tu cho nay sang cho kia.
     *
     * Chat long thi khac: no BI KEO CANG ra theo huong di, roi DON lai
     * khi dung. Day la thu mat nguoi nhan ra ngay ma khong goi ten duoc,
     * va cung la thu iOS lam voi tab bar cua no.
     *
     * Ba phan chay cung luc:
     *
     *   · `translationX` toi cho moi, giam toc.
     *   · `scaleX` phinh len giua duong roi ve 1 - vien thuoc dai ra
     *     trong luc bay, ngan lai khi ha canh.
     *   · `scaleY` mong di mot chut cung luc - giu cho the tich trong
     *     nhu khong doi, dung cach chat long bi keo.
     *
     * Bien do TY LE VOI QUANG DUONG: nhay mot tab thi gan nhu khong gian
     * ra, nhay bon tab thi gian ro. Mot bien do co dinh se lam cu nhay
     * ngan trong giat cuc.
     *
     * Toan bo van trong 300 ms va khong co nhap nhay - xem nguyen tac
     * chuyen dong o `GIAO_DIEN_V5.md`.
     */
    private fun truotKinhLong(v: View, den: Float, soTab: Int) {
        val muc = (soTab.coerceIn(1, 4)) / 4f          // 0,25 .. 1
        val gian = 1f + 0.26f * muc
        val det = 1f - 0.10f * muc

        v.animate().cancel()
        v.animate().translationX(den)
            .setDuration(300)
            .setInterpolator(DecelerateInterpolator(1.7f))
            .start()

        // Phinh roi don: mot ValueAnimator chay 0 -> 1 -> 0 bang
        // `sin(pi * t)`, nen dinh roi dung vao GIUA duong bay.
        ValueAnimator.ofFloat(0f, 1f).apply {
            duration = 300
            interpolator = DecelerateInterpolator(1.2f)
            addUpdateListener {
                val t = it.animatedValue as Float
                val cung = Math.sin(Math.PI * t).toFloat()
                v.scaleX = 1f + (gian - 1f) * cung
                v.scaleY = 1f + (det - 1f) * cung
            }
            addListener(object : android.animation.AnimatorListenerAdapter() {
                override fun onAnimationEnd(a: android.animation.Animator) {
                    v.scaleX = 1f; v.scaleY = 1f
                }
            })
            start()
        }
    }

    /**
     * ----- CHAM GIU: VIEN THUOC PHINH NHE (muc 1.3) -----
     *
     * Dat ngon tay len mot tab va giu: vien thuoc phinh ra mot chut va o
     * yen do cho toi khi nha tay. Hai viec cung luc:
     *
     *   · Bao rang cham DA DUOC NHAN - tren mot thanh tab khong co hieu
     *     ung nhan (`ripple` bi tat de man hinh yen tinh), truoc day
     *     khong co gi phan hoi cho toi khi man hinh moi hien ra.
     *   · Cho mot khoanh de DOI Y: keo ngon tay ra ngoai truoc khi nha
     *     thi khong co gi xay ra.
     *
     * Bien do 6% - du de thay bang duoi mat, khong du de doc ra la mot
     * chuyen dong.
     */
    private fun nhanGiu(v: View, giu: Boolean) {
        v.animate().cancel()
        v.animate()
            .scaleX(if (giu) 1.06f else 1f)
            .scaleY(if (giu) 1.06f else 1f)
            .setDuration(if (giu) 120 else 160)
            .setInterpolator(DecelerateInterpolator(1.3f))
            .start()
    }

    /** Vien thuoc "no" nhe khi trang vua hien - chuyen dong mo dau cua v4. */
    private fun noNhe(v: View) {
        v.scaleX = 0.72f
        ValueAnimator.ofFloat(0.72f, 1f).apply {
            duration = 180
            interpolator = DecelerateInterpolator()
            addUpdateListener { v.scaleX = it.animatedValue as Float }
            start()
        }
    }

    /**
     * Keo ngang tren thanh tab.
     *
     * Chi bat dau theo ngon tay khi da di ngang qua `NGUONG` - duoi nguong
     * do thi cham van la cham, va `onClick` cua tung o van chay binh thuong.
     */
    private fun batKeo(a: Activity, vienThuoc: View, dangChon: Int) {
        val hang = a.findViewById<ViewGroup>(R.id.tab_hang) ?: return
        val nguong = 12f * a.resources.displayMetrics.density

        var dangKeo = false
        var xDau = 0f
        var tabCuoi = dangChon

        hang.setOnTouchListener { v, e ->
            when (e.actionMasked) {
                MotionEvent.ACTION_DOWN -> {
                    xDau = e.x
                    dangKeo = false
                    tabCuoi = dangChon
                    false   // chua nuot: de cham thuong van chay
                }

                MotionEvent.ACTION_MOVE -> {
                    if (!dangKeo && Math.abs(e.x - xDau) > nguong) {
                        dangKeo = true
                        // Tu day tro di cha khong duoc cuop su kien nua.
                        v.parent?.requestDisallowInterceptTouchEvent(true)
                        vienThuoc.animate().cancel()
                    }
                    if (dangKeo) {
                        val i = tabTaiX(a, e.x)
                        val x = xCuaTab(a, i)
                        if (x != null) {
                            // Vien thuoc bam theo ngon tay nhung KHONG di qua
                            // giua hai tab: no nhay tung nac. Cam giac "nam
                            // dinh" nay cho biet minh dang o dau ma khong
                            // phai nhin - mot dai truot muot se khong.
                            vienThuoc.translationX = x
                            if (i != tabCuoi) {
                                tabCuoi = i
                                keoCang(vienThuoc)
                                Rung.rung(v, 1)   // moi lan qua mot tab: mot nac
                            }
                        }
                    }
                    dangKeo
                }

                MotionEvent.ACTION_UP -> {
                    if (!dangKeo) return@setOnTouchListener false
                    dangKeo = false
                    vienThuoc.animate().scaleX(1f).scaleY(1f).setDuration(140).start()
                    if (tabCuoi != dangChon) {
                        Rung.rung(v, 2)   // chot: nac manh hon nac di qua
                        mo(a, tabCuoi)
                    } else {
                        // Keo di roi keo ve cho cu: khong lam gi, va noi ro
                        // bang mot nac nhe la "da ve cho cu".
                        Rung.rung(v, 1)
                        xCuaTab(a, dangChon)?.let { vienThuoc.translationX = it }
                    }
                    true
                }

                MotionEvent.ACTION_CANCEL -> {
                    dangKeo = false
                    vienThuoc.animate().scaleX(1f).scaleY(1f).setDuration(140).start()
                    xCuaTab(a, dangChon)?.let { vienThuoc.translationX = it }
                    true
                }

                else -> false
            }
        }
    }

    /** Keo dai vien thuoc ra mot chut roi tha ve - cam giac "long", co dan. */
    private fun keoCang(v: View) {
        v.animate().cancel()
        v.scaleX = 1.18f
        v.scaleY = 0.9f
        v.animate().scaleX(1f).scaleY(1f).setDuration(190)
            .setInterpolator(DecelerateInterpolator(1.4f)).start()
    }

    /** Tab nam duoi toa do x (tinh trong `tab_hang`). */
    private fun tabTaiX(a: Activity, x: Float): Int {
        for (i in TAB.indices) {
            val khoi = a.findViewById<View>(TAB[i].khoi) ?: continue
            if (x >= khoi.x && x < khoi.x + khoi.width) return i
        }
        return if (x < 0) 0 else TAB.size - 1
    }

    /** Mo tab thu `i`, mang theo chi so tab hien tai de vien thuoc truot tiep. */
    fun mo(a: Activity, i: Int) {
        val tu = TAB.indexOfFirst { it.lop == a.javaClass }
        mo(a, TAB[i].lop) { it.putExtra(TU_TAB, tu) }
    }

    /**
     * `REORDER_TO_FRONT`: cham qua lai nam tab muoi lan khong de lai muoi
     * Activity - bam Back mot lan la ra khoi app.
     */
    fun mo(a: Activity, lop: Class<*>, them: (Intent) -> Unit = {}) {
        a.startActivity(Intent(a, lop).apply {
            flags = Intent.FLAG_ACTIVITY_REORDER_TO_FRONT or Intent.FLAG_ACTIVITY_NO_ANIMATION
            them(this)
        })
        @Suppress("DEPRECATION")
        a.overridePendingTransition(0, 0)
    }
}

/**
 * Noi thanh tieu de: icon Cai dat o moi tab, mui ten quay lai o man hinh con.
 */
object ThanhTieuDe {

    /** Tab: icon Cai dat goc phai. */
    fun noiCaiDat(a: Activity) {
        a.findViewById<View>(R.id.nut_cai_dat_icon)?.setOnClickListener {
            Rung.nhe(it)
            a.startActivity(Intent(a, CaiDatActivity::class.java))
        }
    }

    /** Man hinh con: mui ten + tieu de. `khiQuayLai` mac dinh la dong man hinh. */
    fun noiCon(a: Activity, tieuDe: String, khiQuayLai: () -> Unit = { a.finish() }) {
        a.findViewById<TextView>(R.id.tv_tieu_de_con)?.text = tieuDe
        a.findViewById<View>(R.id.nut_quay_lai_icon)?.setOnClickListener { khiQuayLai() }
    }

    fun nutPhai(a: Activity, chu: String, khiCham: () -> Unit) {
        a.findViewById<TextView>(R.id.nut_phai_con)?.apply {
            text = chu
            visibility = View.VISIBLE
            setOnClickListener { Rung.nhe(it); khiCham() }
        }
    }
}
