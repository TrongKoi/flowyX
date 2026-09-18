import SwiftUI

// MARK: - Thanh phan dung chung

/// Nhan nho phia tren moi khoi. Chu thuong, khong viet hoa toan bo.
struct NhanKhoi: View {
    let chu: String
    var body: some View {
        Text(chu).chu(14, theo: .footnote).foregroundColor(Mau.chuPhu)
    }
}

/// Chip mot lan cham. Dang chon: nen nhan nhat + vien nhan.
struct Chip: View {
    let nhan: String
    let chon: Bool
    var co: CGFloat = 15
    let bam: () -> Void

    var body: some View {
        Button(action: bam) {
            Text(nhan)
                .chu(co, dam: chon)
                .foregroundColor(Mau.chu)
                .padding(.horizontal, 14)
                .frame(minWidth: 52, minHeight: 44)
                .background(Capsule().fill(chon ? Mau.nhanNhat : Mau.the))
                .overlay(Capsule().stroke(chon ? Mau.nhan : Mau.vien, lineWidth: chon ? 2 : 1))
        }
        .buttonStyle(.plain)
        .accessibilityAddTraits(chon ? .isSelected : [])
    }
}

/// Vong thoi gian thu nho dan. Ban Swift cua `TimerTronView.kt`.
///
/// Vanh day thay vi dia dac de so o giua doc duoc tren ca nen sang lan
/// toi. Khong co gio hen: vanh rong + dau gach, KHONG an di.
struct VongThoiGian: View {
    let conLai: Double?
    let tong: Double?

    private var tyLe: Double {
        guard let c = conLai, let t = tong, t > 0 else { return 0 }
        return min(max(c / t, 0), 1)
    }
    private var mau: Color {
        tyLe > 0.5 ? Mau.dhConNhieu : (tyLe > 0.15 ? Mau.dhSapDen : Mau.dhDiNgay)
    }
    private var phut: Int? { conLai.map { Int(($0 / 60).rounded(.up)) } }

    var body: some View {
        GeometryReader { geo in
            let d = min(geo.size.width, geo.size.height)
            ZStack {
                Circle().stroke(Mau.dhRanh, lineWidth: d * 0.12)
                if phut != nil {
                    Circle()
                        .trim(from: 0, to: tyLe)
                        .stroke(mau, style: StrokeStyle(lineWidth: d * 0.12, lineCap: .round))
                        .rotationEffect(.degrees(-90))
                        // Cap nhat moi giay la du; khong hoat hinh muot lien tuc.
                        .animation(nil, value: tyLe)
                }
                VStack(spacing: 0) {
                    Text(phut.map { "\($0)" } ?? "—")
                        .font(.system(size: d * 0.22, weight: .semibold, design: .rounded))
                        .foregroundColor(Mau.chu)
                        .minimumScaleFactor(0.5)
                    if phut != nil {
                        Text("phút").font(.system(size: d * 0.09)).foregroundColor(Mau.chuPhu)
                    }
                }
            }
            .frame(width: d, height: d)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(phut.map { "Còn \($0) phút" } ?? "Chưa có giờ hẹn")
    }
}

/// Khoi mau cho mot buoc hoac mot ke hoach.
struct KhoiMau<NoiDung: View>: View {
    let chiSoMau: Int
    var vienNhan = false
    var mo = false
    let noiDung: NoiDung

    init(chiSoMau: Int, vienNhan: Bool = false, mo: Bool = false,
         @ViewBuilder noiDung: () -> NoiDung) {
        self.chiSoMau = chiSoMau
        self.vienNhan = vienNhan
        self.mo = mo
        self.noiDung = noiDung()
    }

    var body: some View {
        noiDung
            .padding(.horizontal, 14).padding(.vertical, 12)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: 16, style: .continuous)
                .fill(Mau.buoc[((chiSoMau % 5) + 5) % 5]))
            .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous)
                .stroke(vienNhan ? Mau.nhan : Color.clear, lineWidth: 2))
            .opacity(mo ? 0.55 : 1)
    }
}
