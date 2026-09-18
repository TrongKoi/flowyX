import SwiftUI

/// GO ROI DE BAT DAU (v4) - cho luc te liet truoc nhiem vu.
/// NAM cau hoi hien CUNG LUC, cau nao cung tuy chon, nut "Bắt đầu hẹn giờ"
/// luon bam duoc. Mac dinh 10 phut - "chỉ 10 phút" de noi "co" hon 25.
struct ManHinhGoRoi: View {
    /// (ten viec, buoc dau, ly do, so phut) - o trong = nil.
    let xong: (String?, String?, String?, Int) -> Void

    @Environment(\.dismiss) private var dong
    @EnvironmentObject var focus: FocusModel

    @State private var viec = ""
    @State private var buoc = ""
    @State private var lyDo = ""
    @State private var canTro: Set<Int> = []
    @State private var phut = 10

    private let cacCanTro = ["Không biết bắt đầu từ đâu", "Việc có vẻ quá lớn", "Sợ làm chưa tốt",
                             "Thấy chán", "Đang mệt", "Nhiều thứ quá"]
    private let goiY = ["Chỉ cần bước nhỏ ở câu 2. Làm xong bước đó rồi dừng cũng được.",
                        "Hôm nay chỉ cần một mẩu thôi. Phần còn lại vẫn đợi ở đó.",
                        "Bản nháp được phép xấu. Sửa sau dễ hơn viết từ trang trắng.",
                        "Hẹn giờ ngắn giúp việc chán có điểm kết thúc nhìn thấy được.",
                        "Thử 5 phút. Nếu vẫn mệt, nghỉ là lựa chọn hợp lý.",
                        "Chọn một việc thôi. Những việc khác đã nằm trong Kế hoạch."]

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 0) {
                    Text("Không cần trả lời hết. Câu nào khó thì bỏ trống — bấm Bắt đầu lúc nào cũng được.")
                        .chu(14).foregroundColor(Mau.chuPhu).padding(.bottom, 4)

                    cauHoi("Việc gì đang chờ bạn?")
                    oNhap("Ví dụ: viết báo cáo", $viec)

                    cauHoi("Bước nhỏ nhất, làm được trong 2 phút?")
                    oNhap("Ví dụ: mở tệp và đọc lại tiêu đề", $buoc)

                    cauHoi("Điều gì đang làm bạn khựng lại?")
                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 8) {
                        ForEach(cacCanTro.indices, id: \.self) { i in
                            ChipChon(nhan: cacCanTro[i], chon: canTro.contains(i), gian: true) {
                                if canTro.contains(i) { canTro.remove(i) } else { canTro.insert(i) }
                            }
                        }
                    }
                    .padding(.top, 8)
                    if let cuoi = canTro.sorted().last {
                        Text(goiY[cuoi]).chu(13).foregroundColor(Mau.chu)
                            .padding(12).frame(maxWidth: .infinity, alignment: .leading)
                            .background(RoundedRectangle(cornerRadius: 14).fill(Mau.nhanNhat))
                            .padding(.top, 10)
                    }

                    cauHoi("Làm xong thì bạn được gì?")
                    oNhap("Ví dụ: tối nay được nghỉ thoải mái", $lyDo)

                    cauHoi("Thử trong bao lâu?")
                    HStack(spacing: 8) {
                        ForEach([5, 10, 15, 25], id: \.self) { p in
                            ChipChon(nhan: "\(p) phút", chon: phut == p, gian: true) { phut = p }
                        }
                    }
                    .padding(.top, 8)

                    Button("Bắt đầu hẹn giờ") { batDau() }
                        .buttonStyle(NutChinhStyle()).chu(18, dam: true).padding(.top, 24)
                }
                .padding(16)
            }
            .background(Mau.nen.ignoresSafeArea())
            .navigationTitle("Gỡ rối để bắt đầu")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Quay lại") { dong() }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Bỏ qua") { batDau() }
                }
            }
        }
        .onAppear { viec = focus.ten ?? ""; buoc = focus.buocDau ?? ""; lyDo = focus.lyDo ?? "" }
    }

    private func batDau() {
        Rung.xong()
        xong(rong(viec), rong(buoc), rong(lyDo), phut)
        dong()
    }

    private func rong(_ s: String) -> String? {
        let t = s.trimmingCharacters(in: .whitespacesAndNewlines)
        return t.isEmpty ? nil : t
    }

    private func cauHoi(_ c: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(c).chu(16, dam: true).foregroundColor(Mau.chu)
            Text("Tuỳ chọn").chu(12).foregroundColor(Mau.chuPhu)
                .accessibilityHidden(true)
        }
        .padding(.top, 22)
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func oNhap(_ goiY: String, _ chu: Binding<String>) -> some View {
        TextField(goiY, text: chu, axis: .vertical)
            .chu(16).foregroundColor(Mau.chu)
            .padding(.horizontal, 14).padding(.vertical, 12)
            .frame(minHeight: 52)
            .background(RoundedRectangle(cornerRadius: 14).fill(Mau.the))
            .overlay(RoundedRectangle(cornerRadius: 14).stroke(Mau.vien, lineWidth: 1))
            .padding(.top, 8)
    }
}
