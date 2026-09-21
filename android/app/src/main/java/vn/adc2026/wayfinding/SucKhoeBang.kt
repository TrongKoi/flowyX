package vn.adc2026.wayfinding

/**
 * ====================================================================
 * GHEP SO SUC KHOE VOI SO VIEC XONG (muc 7.2)
 * ====================================================================
 *
 * Phan tinh toan cua bang suc khoe, tach khoi phan ve de test duoc tren
 * JVM. Khong import gi cua Android.
 *
 * ----- Cau hoi ma bang nay tra loi -----
 *
 * Khong phai "toi ngu bao nhieu" - dong ho nao cung noi duoc dieu do.
 * Ma la: **nhung hom toi ngu du, toi co lam duoc nhieu hon khong?**
 *
 * Voi nguoi ADHD, cau tra loi cho rieng ho thuong manh hon nhieu so voi
 * con so trung binh trong sach: nhieu nguoi song ca doi voi loi trach
 * "chi la luoi thoi", va nhin thay chinh du lieu cua minh noi rang mot
 * dem ngu nam tieng keo ca ngay hom sau xuong la mot dieu khac han.
 *
 * ----- Vi sao khong goi day la "tuong quan" -----
 *
 * Bay ngay du lieu khong du de tinh mot he so tuong quan co y nghia
 * thong ke, va goi no la "tuong quan" se cho mot con so trong nhu khoa
 * hoc trong khi no khong phai.
 *
 * Nen o day chi lam mot viec rat han che va noi dung ten no: chia cac
 * ngay lam hai nhom - ngu NHIEU hon muc giua va ngu IT hon muc giua -
 * roi so so viec xong trung binh cua hai nhom. Va chi noi ra khi:
 *
 *   · co it nhat bon ngay co CA hai so, va
 *   · hai nhom lech nhau du ro (tu 25% tro len).
 *
 * Khong du thi tra ve `null`, va man hinh khong hien cau nao. Mot cau
 * nhan xet sai ve chinh minh thi te hon la khong co cau nao - va day la
 * mot app ma nguoi dung se doc no vao luc de ton thuong.
 *
 * ----- Va tuyet doi khong ket luan nhan qua -----
 *
 * Cau chu duoc viet la "những hôm ngủ nhiều hơn, bạn xong nhiều việc
 * hơn" - mot quan sat. Khong phai "hãy ngủ nhiều hơn để làm được nhiều
 * hơn", vi do la loi khuyen y te, va Flowy khong phai thiet bi y te
 * (xem `FLOWY_THIET_KE.md` muc 4).
 */
object SucKhoeBang {

    /** Toi thieu bao nhieu ngay co du hai so thi moi dam nhan xet. */
    const val TOI_THIEU_NGAY = 4

    /** Hai nhom phai lech it nhat bao nhieu thi moi coi la dang noi. */
    const val NGUONG_LECH = 0.25

    /** Mot ngay, da ghep hai nguon. */
    data class Ngay(
        val ngay: String,
        val nguPhut: Int?,
        val buocChan: Int?,
        val nhipTimNghi: Int?,
        val soViecXong: Int,
    )

    enum class LienHe { NGU_NHIEU_XONG_NHIEU, NGU_NHIEU_XONG_IT_HON, KHONG_RO }

    /**
     * Ghep danh sach ngay suc khoe voi so viec xong tung ngay.
     *
     * `soViec` la mot ham tra cuu theo chuoi ngay "yyyy-MM-dd" - dung
     * chinh dinh dang ma `SucKhoe.dinhDangNgay` sinh ra, nen hai ben
     * khop nhau ma khong can chuyen doi gi.
     */
    fun ghep(sucKhoe: List<SucKhoe.Ngay>, soViec: (String) -> Int): List<Ngay> =
        sucKhoe.map { Ngay(it.ngay, it.nguPhut, it.buocChan, it.nhipTimNghi, soViec(it.ngay)) }

    /**
     * Nhin vao nhung ngay co CA so ngu lan so viec, xem hai nhom co lech
     * ro khong.
     *
     * Chia theo TRUNG VI chu khong phai trung binh: bay ngay la mot day
     * rat ngan, va chi mot dem thuc trang den ba gio sang du de keo trung
     * binh lech han - luc do gan nhu moi ngay con lai deu roi vao nhom
     * "ngu nhieu", va phep so mat nghia.
     */
    fun lienHeNguVaViec(ds: List<Ngay>): LienHe {
        val du = ds.filter { it.nguPhut != null }
        if (du.size < TOI_THIEU_NGAY) return LienHe.KHONG_RO

        val giua = trungVi(du.mapNotNull { it.nguPhut })
        val nhieu = du.filter { (it.nguPhut ?: 0) > giua }
        val it2 = du.filter { (it.nguPhut ?: 0) <= giua }
        if (nhieu.isEmpty() || it2.isEmpty()) return LienHe.KHONG_RO

        val tbNhieu = nhieu.map { it.soViecXong }.average()
        val tbIt = it2.map { it.soViecXong }.average()
        // Ca hai nhom deu khong xong viec nao -> khong co gi de so sanh,
        // va cang khong nen noi gi. Day la tuan ma nguoi dung dang chat
        // vat nhat.
        if (tbNhieu == 0.0 && tbIt == 0.0) return LienHe.KHONG_RO

        val moc = maxOf(tbNhieu, tbIt)
        val lech = (tbNhieu - tbIt) / moc
        return when {
            lech >= NGUONG_LECH -> LienHe.NGU_NHIEU_XONG_NHIEU
            lech <= -NGUONG_LECH -> LienHe.NGU_NHIEU_XONG_IT_HON
            else -> LienHe.KHONG_RO
        }
    }

    /** Trung binh cac gia tri khong null, lam tron. `null` neu khong co so nao. */
    fun trungBinh(gt: List<Int?>): Int? {
        val co = gt.filterNotNull()
        return if (co.isEmpty()) null else Math.round(co.average()).toInt()
    }

    fun trungVi(gt: List<Int>): Int {
        if (gt.isEmpty()) return 0
        val s = gt.sorted()
        return if (s.size % 2 == 1) s[s.size / 2]
               else (s[s.size / 2 - 1] + s[s.size / 2]) / 2
    }
}
