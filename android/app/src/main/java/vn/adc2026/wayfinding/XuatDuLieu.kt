package vn.adc2026.wayfinding

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * ====================================================================
 * XUAT DU LIEU RA TEP
 * ====================================================================
 *
 * GDPR Dieu 20 (quyen mang du lieu di) va Nghi dinh 13/2023/ND-CP deu
 * doi hoi du lieu phai lay ra duoc o "dinh dang co cau truc, thong dung,
 * doc duoc bang may". Chinh sach quyen rieng tu cua Flowy hua dieu do,
 * nen no phai co that.
 *
 * ----- Vi sao JSON chu khong phai PDF hay CSV -----
 *
 * PDF doc duoc bang mat nhung khong doc duoc bang may - no khong thoa
 * dieu 20. CSV thi phang, ma du lieu o day co cau truc long nhau (ke
 * hoach co danh sach lan nhac, bien ban co danh sach viec). JSON giu
 * duoc cau truc, mo bang bat ky trinh soan thao nao, va nhap lai duoc.
 *
 * ----- CANH BAO: tep xuat ra la BAN RO -----
 *
 * Nhat ky trong may duoc ma hoa AES-256. Khi xuat ra, no thanh chu
 * thuong - vi khoa nam trong Keystore cua may nay va khong di theo tep
 * duoc; mot tep khong ai giai duoc thi xuat ra lam gi.
 *
 * Nguoi dung PHAI duoc bao dieu nay TRUOC khi bam xuat, va `canhBao()`
 * o duoi la cau chu do. Ho chon noi luu qua Storage Access Framework
 * (ACTION_CREATE_DOCUMENT), nen tep khong bao gio nam o thu muc dung
 * chung ma app tu chon.
 */
object XuatDuLieu {

    const val LOAI_MIME = "application/json"

    /** "flowy-2026-09-18.json" */
    fun tenTep(): String =
        "flowy-" + SimpleDateFormat("yyyy-MM-dd", Locale.US).format(Date()) + ".json"

    /**
     * Gom toan bo du lieu nguoi dung thanh mot chuoi JSON.
     *
     * KHONG bao gom: mat khau (chi co ban bam, xuat ra la tiep tay cho
     * viec do vet ngoai may), ma khoi phuc, va khoa ma hoa.
     */
    fun goi(ctx: Context): String {
        val goc = JSONObject()
        goc.put("ung_dung", "Flowy")
        goc.put("phien_ban_xuat", 1)
        goc.put("luc_xuat", System.currentTimeMillis())
        goc.put("ghi_chu", ctx.getString(R.string.xuat_ghi_chu_trong_tep))

        TaiKhoan.dangDangNhap(ctx)?.let {
            goc.put("tai_khoan", JSONObject()
                .put("ho_ten", it.hoTen)
                .put("email", it.email))
        }

        goc.put("ke_hoach", keHoach(ctx))
        goc.put("nhat_ky", nhatKy(ctx))
        goc.put("bien_ban", bienBan(ctx))
        goc.put("tien_do", tienDo(ctx))

        // indent 2: tep con mo duoc bang mat nguoi, khong chi bang may.
        return goc.toString(2)
    }

    private fun keHoach(ctx: Context): JSONArray {
        val ra = JSONArray()
        for (k in SoLich.doc(ctx).danhSach) {
            ra.put(JSONObject()
                .put("ten", k.ten)
                .put("emoji", k.emoji)
                .put("ngay", ngayChu(k.ngay))
                .put("bat_dau", Lich.gioPhut(k.batDau))
                .put("thoi_luong_phut", k.thoiLuong)
                .put("lap_lai", k.lapLai.name)
                .put("uu_tien", k.uuTien.name)
                .put("ghim", k.ghim)
                .put("o_dau", k.oDau ?: JSONObject.NULL))
        }
        return ra
    }

    private fun nhatKy(ctx: Context): JSONArray {
        val ra = JSONArray()
        for (m in SoNhatKy.doc(ctx).muc) {
            ra.put(JSONObject()
                .put("luc", m.luc)
                .put("ngay", SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.US).format(Date(m.luc)))
                .put("tieu_de", m.tieuDe)
                .put("noi_dung", m.noiDung)
                .put("the_nao", m.theNao ?: JSONObject.NULL))
        }
        return ra
    }

    private fun bienBan(ctx: Context): JSONArray {
        val ra = JSONArray()
        for (b in SoBienBan.doc(ctx).danhSach) {
            ra.put(JSONObject()
                .put("ten", b.ten)
                .put("luc", b.luc)
                .put("da_chot", b.daChot)
                .put("viec", JSONArray(b.viec))
                .put("nguon", b.nguon))
        }
        return ra
    }

    private fun tienDo(ctx: Context): JSONObject {
        val s = SoTienDo.doc(ctx)
        val theoNgay = JSONObject()
        for ((ngay, so) in s.bangTheoNgay()) theoNgay.put(ngay, so)
        return JSONObject()
            .put("tong_so_viec", s.tongSoViec())
            .put("chuoi_hien_tai", s.chuoi())
            .put("theo_ngay", theoNgay)
    }

    /** So ngay tuyet doi -> "2026-09-18" de nguoi doc hieu duoc. */
    private fun ngayChu(soNgay: Long): String {
        val (nam, thang, ngay) = Lich.ngayThang(soNgay)
        return String.format(Locale.US, "%04d-%02d-%02d", nam, thang, ngay)
    }
}
