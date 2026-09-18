import SwiftUI

/// THANH TAB DUOI (v4) - ba tin hieu cho tab dang chon: pill nen vang nhat,
/// icon + chu navy, va NHAN CHU chi hien o tab dang chon. Khop Android
/// `khoi_tab_duoi.xml`. Khong dung TabView he thong vi no chi doi mau icon.
struct ThanhTabDuoi: View {
    @Binding var tab: TabV4

    var body: some View {
        HStack(spacing: 0) {
            ForEach(TabV4.allCases) { t in
                let chon = t == tab
                Button {
                    if !chon { Rung.nhe(); tab = t }
                } label: {
                    VStack(spacing: 2) {
                        Image(systemName: t.icon)
                            .font(.system(size: 19, weight: .medium))
                            .frame(width: 64, height: 32)
                            .background(
                                RoundedRectangle(cornerRadius: 16, style: .continuous)
                                    .fill(chon ? Mau.tabPill : .clear)
                                    .scaleEffect(x: chon ? 1 : 0.6)
                                    .animation(.easeOut(duration: 0.18), value: chon))
                            .foregroundColor(chon ? Mau.tabChon : Mau.chuPhu)
                        Text(t.nhan).chu(11, dam: true).foregroundColor(Mau.tabChon)
                            .opacity(chon ? 1 : 0)
                    }
                    .frame(maxWidth: .infinity)
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityLabel(t.nhan + (chon ? ", đang chọn" : ""))
                .accessibilityAddTraits(chon ? [.isButton, .isSelected] : .isButton)
            }
        }
        .padding(.top, 6)
        .frame(height: 64)
        .background(Mau.the.ignoresSafeArea(edges: .bottom))
        .overlay(Rectangle().fill(Mau.vien).frame(height: 1), alignment: .top)
    }
}

enum TabV4: String, CaseIterable, Identifiable {
    case keHoach, lich, focus, nhatKy, bienBan
    var id: String { rawValue }
    var nhan: String {
        switch self {
        case .keHoach: return "Kế hoạch"
        case .lich: return "Lịch"
        case .focus: return "Tập trung"
        case .nhatKy: return "Nhật ký"
        case .bienBan: return "Biên bản"
        }
    }
    var icon: String {
        switch self {
        case .keHoach: return "checklist"
        case .lich: return "calendar"
        case .focus: return "timer"
        case .nhatKy: return "book.closed"
        case .bienBan: return "doc.text"
        }
    }
}

/// THANH TIEU DE CUA TAB: logo | [nut hanh dong] | CAI DAT (co dinh moi tab).
struct ThanhTieuDeTab<HanhDong: View>: View {
    @Binding var moCaiDat: Bool
    @ViewBuilder var hanhDong: HanhDong

    var body: some View {
        HStack(spacing: 4) {
            LogoFlowy()
            Spacer(minLength: 0)
            hanhDong
            Button { Rung.nhe(); moCaiDat = true } label: {
                Image(systemName: "gearshape")
                    .font(.system(size: 20, weight: .regular))
                    .frame(width: 44, height: 44)
                    .foregroundColor(Mau.chu)
            }
            .accessibilityLabel("Cài đặt")
        }
        .padding(.horizontal, 12)
        .frame(height: 56)
    }
}

struct LogoFlowy: View {
    var body: some View {
        HStack(spacing: 6) {
            VStack(spacing: 2) {
                HStack(spacing: 2) { cham(Mau.chu); cham(Mau.chu) }
                HStack(spacing: 2) { cham(Mau.nhan); cham(Mau.cam) }
            }
            HStack(spacing: 0) {
                Text("flowy").chu(19, dam: true).foregroundColor(Mau.chu)
                Text("X").chu(19, dam: true).foregroundColor(Mau.cam)
            }
        }
        .accessibilityElement()
        .accessibilityLabel("FlowyX")
    }
    private func cham(_ m: Color) -> some View { Circle().fill(m).frame(width: 6, height: 6) }
}

/// HANG CAI DAT dung chung - khuon sua loi lech can gióng cua Android:
/// icon 20 | nhan (gian) | gia tri can phai, cao toi thieu 56.
struct HangCaiDat: View {
    let icon: String
    let nhan: String
    var giaTri: String?
    var cham: (() -> Void)?

    var body: some View {
        let noiDung = HStack(spacing: 12) {
            Image(systemName: icon).font(.system(size: 17))
                .frame(width: 20, height: 20).foregroundColor(Mau.chuPhu)
            Text(nhan).chu(15, dam: giaTri == nil).foregroundColor(Mau.chu)
            Spacer(minLength: 8)
            if let giaTri {
                Text(giaTri).chu(15, dam: true).foregroundColor(Mau.chuLienKet)
                    .multilineTextAlignment(.trailing)
            }
        }
        .frame(minHeight: 56)
        .contentShape(Rectangle())

        if let cham {
            Button { Rung.nhe(); cham() } label: { noiDung }
                .buttonStyle(.plain)
                .accessibilityLabel(giaTri == nil ? nhan : "\(nhan): \(giaTri!)")
        } else {
            noiDung
        }
    }
}

/// Chip chon - dung o uu tien, lap lai, nhac, thoi luong.
struct ChipChon: View {
    let nhan: String
    var chon = false
    var cham: Color?
    var gian = false
    let bam: () -> Void

    var body: some View {
        Button { Rung.nhe(); bam() } label: {
            HStack(spacing: 6) {
                if let cham { Circle().fill(cham).frame(width: 10, height: 10) }
                Text(nhan).chu(14, dam: chon).foregroundColor(Mau.chu)
            }
            .padding(.horizontal, 14)
            .frame(maxWidth: gian ? .infinity : nil, minHeight: 44)
            .background(RoundedRectangle(cornerRadius: 14, style: .continuous)
                .fill(chon ? Mau.nhanNhat : Mau.nen))
            .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous)
                .stroke(chon ? Mau.nhanVien : Mau.vien, lineWidth: chon ? 2 : 1))
        }
        .buttonStyle(.plain)
        .accessibilityLabel(nhan + (chon ? ", đang chọn" : ""))
    }
}

/// O tron danh dau xong - MOT cham, khong nhan giu.
struct OTron: View {
    let xong: Bool
    let bam: () -> Void
    var body: some View {
        Button { Rung.xong(); bam() } label: {
            ZStack {
                Circle().fill(xong ? Mau.cam : .clear)
                    .overlay(Circle().stroke(xong ? .clear : Mau.chuPhu, lineWidth: 2))
                    .frame(width: 24, height: 24)
                if xong {
                    Image(systemName: "checkmark").font(.system(size: 13, weight: .bold))
                        .foregroundColor(Mau.the)
                }
            }
            .frame(width: 44, height: 44)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityLabel(xong ? "Bỏ đánh dấu xong" : "Đánh dấu xong")
    }
}

/// THANH HOAN TAC / THONG BAO - phu len day man hinh, tren thanh tab.
struct ThanhHoanTac: View {
    @EnvironmentObject var ht: HoanTacModel
    var body: some View {
        if let b = ht.bao {
            HStack(spacing: 12) {
                Text(b.chu).chu(14).foregroundColor(Mau.nen)
                Spacer(minLength: 0)
                if let ht2 = b.hoanTac {
                    Button("Hoàn tác") { Rung.nhe(); ht.bao = nil; ht2() }
                        .chu(14, dam: true).foregroundColor(Mau.nhan)
                        .frame(minWidth: 88, minHeight: 44)
                }
            }
            .padding(.leading, 18).padding(.trailing, 6)
            .padding(.vertical, b.hoanTac == nil ? 12 : 0)
            .background(RoundedRectangle(cornerRadius: 14, style: .continuous).fill(Mau.chu))
            .padding(.horizontal, 12)
            .transition(.move(edge: .bottom).combined(with: .opacity))
            .accessibilityElement(children: .contain)
            .accessibilityAddTraits(.isSummaryElement)
        }
    }
}

/// Khoi trong - LUON giu cho, khong bien mat.
struct KhoiTrong: View {
    let chu: String
    var body: some View {
        Text(chu).chu(15).foregroundColor(Mau.chuPhu)
            .multilineTextAlignment(.center)
            .frame(maxWidth: .infinity, minHeight: 88)
            .the()
    }
}

extension View {
    /// Hang trong List nhung trong nhu the tren nen: bo nen, bo vach ngan,
    /// le 16. Vuot (`swipeActions`) CHI chay trong List - day la ly do cac
    /// man hinh co vuot dung List thay vi ScrollView.
    func hangTron(tren: CGFloat = 6, duoi: CGFloat = 6) -> some View {
        self.listRowBackground(Color.clear)
            .listRowSeparator(.hidden)
            .listRowInsets(EdgeInsets(top: tren, leading: 16, bottom: duoi, trailing: 16))
    }
}

/// List phang, nen FlowyX, khong vach ngan.
struct DanhSachPhang<NoiDung: View>: View {
    @ViewBuilder var noiDung: NoiDung
    var body: some View {
        List { noiDung }
            .listStyle(.plain)
            .scrollContentBackground(.hidden)
            .background(Mau.nen)
            .environment(\.defaultMinListRowHeight, 0)
    }
}
