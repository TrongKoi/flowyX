package vn.adc2026.wayfinding

import android.content.Context

/**
 * ====================================================================
 * CAI DAT NHAC VIEC (muc 3.3)
 * ====================================================================
 *
 * ----- Vi sao thay hai cong tac cu -----
 *
 * Truoc day Cai dat chi co hai muc lien quan toi nhac viec: mot thanh
 * truot muc rung, va mot hang chip "doc len / rung / ca hai". Ca hai deu
 * la cong tac TOAN CUC: bat thi bat cho moi thu, tat thi tat cho moi thu.
 *
 * Voi nguoi ADHD, do la lua chon giua hai cai deu sai. De nguyen thi buoi
 * toi cung bi danh thuc vi mot viec khong gap; tat di thi mat luon ca
 * nhung loi nhac that su can. Va vi tat la mot cham, con bat lai thi phai
 * nho quay vao Cai dat, nen ket cuc gan nhu luon la: tat, roi quen bat.
 *
 * Nen bon truc duoi day deu la cach noi "KHI NAO thi duoc lam phien", chu
 * khong phai "co duoc lam phien khong":
 *
 *   1. GIO YEN TINH      - khung gio khong phat am thanh va khong doc
 *                          len. Van rung, van hien tren man hinh khoa:
 *                          loi nhac khong mat, no chi im.
 *   2. NHAC TRUOC PHIEN   - bao truoc bao nhieu phut de kip chuyen viec.
 *                          Day la phan chong "mu thoi gian" o dang nho
 *                          nhat: thu nguoi ta thieu khong phai loi nhac
 *                          dung gio, ma la khoang dem TRUOC gio do.
 *   3. NHAC LAI           - viec toi gio ma chua dong toi thi nhac lai
 *                          sau bao lau. Khong nhac lai thi mot lan bo lo
 *                          la mat han.
 *   4. AM BAO KHAN        - nhung viec nao duoc phep keu to hon.
 *
 * ----- Vi sao "gio yen tinh" khong tat rung -----
 *
 * Rung khong danh thuc nguoi khac trong phong, va no van doc duoc khi may
 * de trong tui. Thu can chan la TIENG va GIONG DOC. Tat ca ba thi gio yen
 * tinh thanh "tat thong bao", va khi do nguoi dung se khong dam bat no.
 *
 * ----- Phan logic o day la thuan -----
 *
 * `trongGioYen()` chi nhan so phut va tra ve true/false, nen test duoc
 * tren JVM. Phan doc/ghi nam o `AppSettings`.
 */
object NhacCaiDat {

    /** Cac muc chon cho "nhac truoc phien", tinh bang phut. */
    val TRUOC_PHIEN = listOf(0, 5, 10, 15, 30)

    /** Cac muc chon cho "nhac lai", tinh bang phut. 0 = khong nhac lai. */
    val NHAC_LAI = listOf(0, 5, 10, 20)

    /**
     * Thoi diem `phut` (tinh tu 00:00) co nam trong gio yen tinh khong.
     *
     * Khung gio duoc phep VAT QUA NUA DEM - va do la truong hop thuong
     * gap nhat, vi gio yen tinh dien hinh la 22:00 den 07:00. Luc do
     * `tu > den`, va phep so sanh phai doi chieu:
     *
     *     tu <= den   ->  tu <= phut < den          (vd 13:00-14:00)
     *     tu >  den   ->  phut >= tu HOAC phut < den (vd 22:00-07:00)
     *
     * Ban dau viet nham thanh mot phep so sanh duy nhat thi khung qua nua
     * dem luon tra ve false - tuc la gio yen tinh khong bao gio co hieu
     * luc, dung o khung gio ma nguoi dung can no nhat.
     */
    fun trongGioYen(phut: Int, tu: Int, den: Int): Boolean {
        if (tu == den) return false          // khong dat khung nao
        return if (tu < den) phut in tu until den
               else phut >= tu || phut < den
    }

    /** Bay gio co dang trong gio yen tinh khong. */
    fun dangYen(ctx: Context): Boolean {
        val s = AppSettings(ctx)
        if (!s.gioYenBat) return false
        val c = java.util.Calendar.getInstance()
        val phut = c.get(java.util.Calendar.HOUR_OF_DAY) * 60 + c.get(java.util.Calendar.MINUTE)
        return trongGioYen(phut, s.gioYenTu, s.gioYenDen)
    }
}
