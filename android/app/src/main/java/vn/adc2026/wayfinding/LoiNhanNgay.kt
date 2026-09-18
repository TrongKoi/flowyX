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

    val CAU = listOf(
        "Bắt đầu nhỏ vẫn là bắt đầu.",
        "Hôm nay không cần hoàn hảo. Chỉ cần có mặt.",
        "Một bước năm phút vẫn đưa bạn đi xa hơn đứng yên.",
        "Não bạn không lười. Nó chỉ cần một điểm vào dễ hơn.",
        "Quên mất rồi quay lại cũng là một kỹ năng.",
        "Ngày nghỉ không làm đứt gì cả.",
        "Bạn được phép làm chậm hơn kế hoạch.",
        "Việc khó nhất thường là hai phút đầu.",
        "Xong một phần vẫn là xong một phần.",
        "Bạn đã mở app. Đó đã là một lựa chọn tốt.",
        "Tập trung đến rồi đi. Bạn chỉ cần mời nó quay lại.",
        "Không cần làm hết. Chọn một việc thôi.",
        "Nghỉ cũng là một phần của làm việc.",
        "Hôm qua là hôm qua. Hôm nay bắt đầu từ đây.",
        "Chia nhỏ không phải là làm ít. Là làm được.",
        "Bạn không cần cảm thấy sẵn sàng mới bắt đầu.",
        "Mỗi lần quay lại việc đang dở là một lần thắng.",
        "Thời gian trôi khó cảm nhận. Vòng đồng hồ sẽ nhớ hộ bạn.",
        "Viết ra được là đã nhẹ đi một nửa.",
        "Một ngày rối vẫn có thể có một giờ yên.",
        "Bạn đang học cách làm việc theo kiểu của mình.",
        "Hỏi \"bước nhỏ nhất là gì?\" luôn có câu trả lời.",
        "Dừng lại để thở không làm mất tiến độ.",
        "Làm cùng một việc hai lần vẫn là tiến bộ.",
        "Không sao nếu hôm nay chỉ làm được việc dễ.",
        "Bạn không phải sửa mình. Chỉ cần sắp lại xung quanh.",
        "Một kế hoạch đổi giữa chừng vẫn là một kế hoạch.",
        "Mười phút tập trung thật quý hơn một giờ ép mình.",
        "Việc bạn né lâu nhất thường nhỏ hơn bạn nghĩ.",
        "Bạn đã đi qua nhiều ngày khó hơn hôm nay.",
        "Chậm mà quay lại vẫn hơn nhanh mà bỏ cuộc.",
    )

    /** Cau cua mot ngay. `soNgay` = so ngay tu 1970 theo gio dia phuong. */
    fun cua(soNgay: Long): String =
        CAU[Math.floorMod(soNgay * 7 + 3, CAU.size.toLong()).toInt()]
}
