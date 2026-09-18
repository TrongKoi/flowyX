package vn.adc2026.wayfinding

import android.content.Context

/**
 * GOP LOI NHAC VAO KE HOACH (v4) - chay mot lan cho moi may.
 *
 * Nhom bo tinh nang "Loi nhac" rieng: hai noi cung tra loi cau "khi nao
 * can nho viec gi" la hai noi phai nho mo ra. Moi loi nhac cu thanh mot
 * ke hoach 15 phut, lap hang ngay (hoac mot lan), nhac dung gio, uu tien
 * Vua - roi so loi nhac duoc xoa va chuong cu duoc huy.
 *
 * Khong mat du lieu: chuyen xong moi xoa; loi giua chung thi lan sau chay lai.
 */
object ChuyenLoiNhac {

    private const val PREFS = "flowy_v4"
    private const val KHOA = "da_gop_loi_nhac"

    fun chayMotLan(ctx: Context) {
        val p = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        if (p.getBoolean(KHOA, false)) return
        try {
            val cu = SoNhac.doc(ctx)
            if (cu.danhSach.isNotEmpty()) {
                val lich = SoLich.doc(ctx)
                val homNay = SoLich.homNay()
                for (ln in cu.danhSach) {
                    lich.danhSach.add(KeHoach(
                        id = SoLich.moiId(),
                        ten = ln.ten,
                        emoji = "🔔",
                        ngay = homNay,
                        batDau = ln.gio.toInt().coerceIn(0, 1439),
                        thoiLuong = 15,
                        lapLai = if (ln.lapLaiHangNgay) LapLai.HANG_NGAY else LapLai.KHONG,
                        nhacTruoc = listOf(0),
                    ))
                }
                lich.luu(ctx)
                LichBao.datLai(ctx, lich)
                cu.danhSach.clear()
                cu.luu(ctx)
                BaoGio.datLai(ctx, cu)          // huy chuong cu
            }
            p.edit().putBoolean(KHOA, true).apply()
        } catch (_: Exception) {
            // Loi giua chung: de lan sau thu lai, khong lam sap app.
        }
    }
}
