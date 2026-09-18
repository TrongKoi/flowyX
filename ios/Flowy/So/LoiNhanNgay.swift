import Foundation

/// LOI NHAN THEO NGAY - CUNG danh sach va CUNG cong thuc voi Android
/// `LoiNhanNgay.kt`: chi so = (ngay * 7 + 3) mod 31. Hai may cung ngay hien
/// cung mot cau; hai ngay lien nhau khong bao gio trung.
enum LoiNhanNgay {
    static let cau = [
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
    ]

    static func cua(soNgay: Int) -> String {
        let n = cau.count
        return cau[((soNgay * 7 + 3) % n + n) % n]
    }
}
