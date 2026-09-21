package vn.adc2026.wayfinding

/**
 * LOI NHAN THAN THIEN - doi moi ngay, KHONG doi trong ngay.
 *
 * Vi sao theo NGAY chu khong ngau nhien moi lan mo: cau doi moi lan mo app
 * bien the loi nhan thanh thu de "keo xuong xem cau moi" - mot vong lap
 * phan tam nho. Mot cau cho ca ngay la mot diem tua co dinh.
 *
 * Vi sao khong bao gio trung hom qua: chi so = (ngay * 7 + 3) mod 31. Vi 31
 * nguyen to va 7 khong chia het cho 31, hai ngay lien nhau luon lech nhau 7
 * vi tri, va sau 31 ngay moi cau deu da xuat hien dung mot lan.
 *
 * Quy tac viet (FLOWY_THIET_KE muc 4.4, va rieng cho nguoi ADHD):
 *   - khong "ban nen", "ban phai" - khong giao them viec
 *   - khong so sanh voi nguoi khac, khong "co len!"
 *   - cong nhan cong suc, khong chi ket qua
 *   - ngay nghi va ngay te la binh thuong, khong phai that bai
 *   - ngan: doc duoc trong mot lan liec
 */
object LoiNhanNgay {

    val CAU: List<Int> = listOf(
        R.string.motd_small_beginning,
        R.string.motd_no_perfection,
        R.string.motd_moving_standing,
        R.string.motd_brain_not_lazy,
        R.string.motd_forget_then_return,
        R.string.motd_rest_day,
        R.string.motd_slower_than_planned,
        R.string.motd_the_first_minutes,
        R.string.motd_partial_done,
        R.string.motd_app_initiate,
        R.string.motd_focus_then_leave,
        R.string.motd_partial_progress,
        R.string.motd_rest_is_work,
        R.string.motd_yesterday_is_yesterday,
        R.string.motd_divide_and_conquer,
        R.string.motd_ready_to_begin,
        R.string.motd_return_to_work,
        R.string.motd_time_blindness,
        R.string.motd_divide_down,
        R.string.motd_peace_in_chaos,
        R.string.motd_personal_work_style,
        R.string.motd_smallest_step,
        R.string.motd_stop_to_breathe,
        R.string.motd_do_things_twice,
        R.string.motd_today_easy,
        R.string.motd_rearrange_surroundings,
        R.string.motd_change_of_plans,
        R.string.motd_focus_over_force,
        R.string.motd_task_procrastination,
        R.string.motd_endured_harder,
        R.string.motd_persistence_over_speed,
    )

    /** Cau cua mot ngay. `soNgay` = so ngay tu 1970 theo gio dia phuong. */
    fun cua(soNgay: Long): Int =
        CAU[Math.floorMod(soNgay * 7 + 3, CAU.size.toLong()).toInt()]
}
