package vn.adc2026.wayfinding

import android.content.Context

/**
 * ====================================================================
 * MAU DONG HO TAP TRUNG - nguoi dung tu chon
 * ====================================================================
 *
 * ----- Vi sao cho chon, khi ca app con lai thi khong -----
 *
 * FlowyX co mot bang mau co dinh, va do la co y: moi mau trong app deu
 * mang MOT nghia (cam = sap het gio, do = xoa, tim = bam duoc), nen cho
 * doi mau tu do se pha chinh he thong do.
 *
 * Dong ho Tap trung la ngoai le, va co ba ly do that:
 *
 *   1. No la thu nguoi dung NHIN LAU NHAT. Mot phien 50 phut la 50 phut
 *      nhin vao dung mot vong tron. Mau nao de chiu thi rat khac nhau
 *      giua tung nguoi.
 *   2. Voi nguoi nhay cam giac quan - rat thuong gap o nhom
 *      neurodivergent - cam va vang bao hoa cao co the gay kho chiu thuc
 *      su, khong phai chuyen tham my.
 *   3. Do la mot quyen kiem soat NHO ma khong lam hong gi. Doi mau vong
 *      khong lam doi nghia cua mau nao khac trong app.
 *
 * ----- Vi sao KHONG phai bang chon mau tu do -----
 *
 * Mot banh xe mau cho phep chon bat cu ma hex nao se de nguoi dung tu
 * dat mot mau chim vao nen, hoac mot mau ma chu o giua khong con doc
 * duoc. Voi mot man hinh ma ca muc dich la "lieec mot cai la biet", do
 * la hong chuc nang chu khong phai xau.
 *
 * Nen o day la NAM bo mau lam san, moi bo da do tuong phan o CA hai che
 * do sang/toi, va moi bo van giu du ba chang (con nhieu / sap den / di
 * ngay) de tin hieu thoi gian khong mat.
 *
 * Bo "Theo he thong" la mac dinh va dung dung bang mau FlowyX goc.
 */
object MauDongHo {

    /**
     * Mot bo mau dong ho.
     *
     * @param ten     id chuoi de hien trong Cai dat
     * @param conNhieu mau luc con nhieu thoi gian - phai DIU, khong giuc
     * @param sapDen   mau chang giua
     * @param diNgay   mau luc sap het - phai la mau manh nhat trong bo
     */
    data class Bo(
        val ma: String,
        val ten: Int,
        val conNhieu: Int,
        val sapDen: Int,
        val diNgay: Int,
    )

    const val THEO_HE_THONG = ""

    /**
     * Nam bo. Con so lay tu bang mau FlowyX va tu cac ho mau da kiem
     * tuong phan; khong bo nao dung mau bao hoa toi da.
     *
     * Bo "diu" co y dat ngay sau bo mac dinh: ai vao day vi thay mau
     * hien tai choi mat thi thay ngay thu minh dang tim, khong phai doc
     * het nam lua chon.
     */
    val BO: List<Bo> = listOf(
        Bo(THEO_HE_THONG, R.string.dh_mau_mac_dinh,
            R.color.dh_con_nhieu, R.color.dh_sap_den, R.color.dh_di_ngay),
        Bo("diu", R.string.dh_mau_diu,
            R.color.dhm_diu_1, R.color.dhm_diu_2, R.color.dhm_diu_3),
        Bo("bien", R.string.dh_mau_bien,
            R.color.dhm_bien_1, R.color.dhm_bien_2, R.color.dhm_bien_3),
        Bo("rung", R.string.dh_mau_rung,
            R.color.dhm_rung_1, R.color.dhm_rung_2, R.color.dhm_rung_3),
        Bo("hoang_hon", R.string.dh_mau_hoang_hon,
            R.color.dhm_hh_1, R.color.dhm_hh_2, R.color.dhm_hh_3),
    )

    fun dangDung(ctx: Context): Bo {
        val ma = AppSettings(ctx).mauDongHo
        return BO.firstOrNull { it.ma == ma } ?: BO[0]
    }

    fun viTri(ctx: Context): Int {
        val ma = AppSettings(ctx).mauDongHo
        return BO.indexOfFirst { it.ma == ma }.coerceAtLeast(0)
    }
}
