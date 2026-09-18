import AVFoundation
import UIKit

/// Giong noi tieng Viet, rung, va am ngan. Ban Swift cua `Speaker.kt`.
final class Speaker {

    private let tts = AVSpeechSynthesizer()
    private var giong: AVSpeechSynthesisVoice?
    var tocDo: Double = 1.2

    init() {
        giong = AVSpeechSynthesisVoice(language: "vi-VN")
    }

    /// May co giong tieng Viet khong. iOS thuong co san ban "compact".
    static var coGiongViet: Bool {
        AVSpeechSynthesisVoice.speechVoices().contains { $0.language.hasPrefix("vi") }
    }

    func say(_ cau: String, urgent: Bool) {
        let t = cau.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !t.isEmpty else { return }
        if urgent, tts.isSpeaking { tts.stopSpeaking(at: .immediate) }
        let session = AVAudioSession.sharedInstance()
        // Nguoi dung co the dang nghe nhac: ha nho nhac, khong cat han.
        try? session.setCategory(.playback, mode: .spokenAudio, options: [.duckOthers])
        try? session.setActive(true, options: [])
        let u = AVSpeechUtterance(string: t)
        u.voice = giong
        let r = Float(tocDo) * AVSpeechUtteranceDefaultSpeechRate
        u.rate = min(max(r, AVSpeechUtteranceMinimumSpeechRate), AVSpeechUtteranceMaximumSpeechRate)
        tts.speak(u)
    }

    func stop() { tts.stopSpeaking(at: .immediate) }

    /// Ma rung - khop HAPTIC_PATTERNS ben speech.py (dem so nhip).
    func vibrate(_ ma: String?) {
        guard let ma else { return }
        let nhip: [(TimeInterval, UIImpactFeedbackGenerator.FeedbackStyle)]
        switch ma {
        case "one_pulse": nhip = [(0, .medium)]
        case "two_pulse": nhip = [(0, .medium), (0.2, .medium)]
        case "three_pulse": nhip = [(0, .medium), (0.16, .medium), (0.32, .medium)]
        case "long_buzz", "double_repeat": nhip = [(0, .heavy), (0.3, .heavy)]
        case "xong_chang": nhip = [(0, .light), (0.1, .light)]
        default: return
        }
        for (tre, kieu) in nhip {
            DispatchQueue.main.asyncAfter(deadline: .now() + tre) {
                UIImpactFeedbackGenerator(style: kieu).impactOccurred()
            }
        }
    }

    /// Am ngan, khong phai giong noi.
    func playAm(_ ten: String?) {
        switch ten {
        case "tach": AudioServicesPlaySystemSound(1104)          // tieng go phim nhe
        case "hoan_thanh": AudioServicesPlaySystemSound(1025)
        default: break
        }
    }
}
