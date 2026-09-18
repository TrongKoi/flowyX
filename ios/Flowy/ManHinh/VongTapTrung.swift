import SwiftUI

/// DONG HO TAP TRUNG - mat tuyet doi 60 phut, kieu Time Timer.
/// Khop `frontend/.../VongTapTrungView.kt` cua Android: 15 phut LUC NAO cung
/// la mot phan tu mat, nen mat hoc duoc "15 phut trong to co nay". Tu 60 den
/// 120 phut: mat day + gio thu hai la vong ngoai.
///
/// Dat gio = XOAY quanh mat (moi vong 60 phut, toi da 2 vong), rung "tich"
/// moi moc 5 phut. Chi xoay duoc khi chua chay.
struct VongTapTrung: View {
    let conLaiPhut: Double
    let nhanChinh: String
    let nhanPhu: String
    /// 0...1 phan con lai so voi tong - chi de chon MAU gap.
    let tyLe: Double
    let choKeo: Bool
    let doiPhut: (Int) -> Void

    @State private var gocTruoc: Double?
    @State private var phutKeo: Double = 25
    @State private var mocTruoc = 5

    private var mau: Color {
        tyLe > 0.5 ? Mau.dhConNhieu : (tyLe > 0.15 ? Mau.dhSapDen : Mau.dhDiNgay)
    }

    var body: some View {
        GeometryReader { g in
            let d = min(g.size.width, g.size.height)
            let tam = CGPoint(x: g.size.width / 2, y: d / 2)
            let rNgoai = d / 2 - d * 0.03
            let dayVong = d * 0.035
            let r = rNgoai - dayVong * 1.8
            ZStack {
                Canvas { ctx, _ in
                    ctx.fill(Path(ellipseIn: CGRect(x: tam.x - r, y: tam.y - r, width: r * 2, height: r * 2)),
                             with: .color(Mau.the))
                    // 60 vach phut, moc 5 phut dai hon
                    for i in 0..<60 {
                        let goc = Double(i) * 6 - 90
                        let dai = i % 5 == 0 ? r * 0.10 : r * 0.04
                        var p = Path()
                        p.move(to: diem(tam, r - d * 0.02, goc))
                        p.addLine(to: diem(tam, r - d * 0.02 - dai, goc))
                        ctx.stroke(p, with: .color(Mau.chuPhu.opacity(i % 5 == 0 ? 0.9 : 0.35)),
                                   style: StrokeStyle(lineWidth: i % 5 == 0 ? d * 0.008 : d * 0.004, lineCap: .round))
                    }
                    // Quat con lai - gio dau tren mat
                    let gioDau = min(conLaiPhut, 60)
                    if gioDau > 0 {
                        let rq = r * 0.86
                        var p = Path()
                        p.move(to: tam)
                        p.addArc(center: tam, radius: rq, startAngle: .degrees(-90),
                                 endAngle: .degrees(-90 + 360 * gioDau / 60), clockwise: false)
                        p.closeSubpath()
                        ctx.fill(p, with: .color(mau.opacity(0.92)))
                    }
                    // Gio thu hai: vong ngoai
                    let gioHai = max(0, conLaiPhut - 60)
                    if gioHai > 0 {
                        let rv = rNgoai - dayVong / 2
                        ctx.stroke(Path(ellipseIn: CGRect(x: tam.x - rv, y: tam.y - rv, width: rv * 2, height: rv * 2)),
                                   with: .color(Mau.dhRanh), lineWidth: dayVong)
                        var p = Path()
                        p.addArc(center: tam, radius: rv, startAngle: .degrees(-90),
                                 endAngle: .degrees(-90 + 360 * gioHai / 60), clockwise: false)
                        ctx.stroke(p, with: .color(mau), style: StrokeStyle(lineWidth: dayVong, lineCap: .round))
                    }
                    // Nut giua de chu doc duoc tren moi mau quat
                    let rt = r * 0.42
                    ctx.fill(Path(ellipseIn: CGRect(x: tam.x - rt, y: tam.y - rt, width: rt * 2, height: rt * 2)),
                             with: .color(Mau.the))
                }
                ForEach([0, 15, 30, 45], id: \.self) { so in
                    let goc = Double(so) * 6 - 90
                    Text("\(so)").chu(d * 0.045).foregroundColor(Mau.chuPhu)
                        .position(diem(tam, r * 0.74, goc))
                }
                VStack(spacing: 2) {
                    Text(nhanChinh).chu(d * (nhanChinh.count > 5 ? 0.095 : 0.115), dam: true, theo: .title)
                        .foregroundColor(Mau.chu).monospacedDigit()
                    Text(nhanPhu).chu(d * 0.042).foregroundColor(Mau.chuPhu)
                }
                .position(tam)
            }
            .contentShape(Rectangle())
            // `including:` thay cho gesture tuy chon - keo tat khi dang chay.
            .gesture(keo(tam: tam), including: choKeo ? .all : .subviews)
        }
        .aspectRatio(1, contentMode: .fit)
        .onAppear { phutKeo = max(1, conLaiPhut); mocTruoc = Int(phutKeo) / 5 }
        .onChange(of: conLaiPhut) { moi in
            // Chip nhanh doi so phut tu ben ngoai: dong bo de lan xoay sau
            // bat dau tu dung vi tri, khong nhay.
            if choKeo, abs(moi - phutKeo) > 0.9 { phutKeo = max(1, moi); mocTruoc = Int(phutKeo) / 5 }
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(nhanChinh + ". " + nhanPhu)
        .accessibilityValue("\(Int(conLaiPhut.rounded())) phút")
        .accessibilityAdjustableAction { huong in
            guard choKeo else { return }
            phutKeo = min(120, max(1, (phutKeo.rounded() + (huong == .increment ? 5 : -5))))
            doiPhut(Int(phutKeo))
        }
    }

    private func keo(tam: CGPoint) -> some Gesture {
        DragGesture(minimumDistance: 0)
            .onChanged { v in
                let g = gocCua(v.location, tam)
                if let truoc = gocTruoc {
                    var delta = g - truoc
                    if delta > 180 { delta -= 360 }
                    if delta < -180 { delta += 360 }
                    phutKeo = min(120, max(1, phutKeo + delta / 6))
                } else {
                    // Cham xuong = NHAY toi goc do trong vong hien tai.
                    let vong: Double = phutKeo > 60 ? 60 : 0
                    phutKeo = min(120, max(1, vong + g / 6))
                }
                gocTruoc = g
                let moc = Int(phutKeo) / 5
                if moc != mocTruoc { mocTruoc = moc; Rung.tich() }
                doiPhut(Int(phutKeo.rounded()))
            }
            .onEnded { _ in gocTruoc = nil }
    }

    /// 0 do o dinh, tang theo chieu kim dong ho.
    private func gocCua(_ p: CGPoint, _ tam: CGPoint) -> Double {
        let a = atan2(p.y - tam.y, p.x - tam.x) * 180 / .pi + 90
        return (a + 360).truncatingRemainder(dividingBy: 360)
    }

    private func diem(_ tam: CGPoint, _ r: CGFloat, _ gocDo: Double) -> CGPoint {
        let rad = gocDo * .pi / 180
        return CGPoint(x: tam.x + r * cos(rad), y: tam.y + r * sin(rad))
    }
}
