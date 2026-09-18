import AVFoundation
import Speech

/// Nghe MOT cau tieng Viet. Ban Swift cua `VoiceInput.kt`.
///
/// Uu tien nhan dang TREN MAY khi iOS ho tro. Khong tu bat lai khi khong
/// nghe duoc: im lang la mot cau tra loi hop le.
final class VoiceInput {

    private let recognizer = SFSpeechRecognizer(locale: Locale(identifier: "vi-VN"))
    private let engine = AVAudioEngine()
    private var request: SFSpeechAudioBufferRecognitionRequest?
    private var task: SFSpeechRecognitionTask?
    private var hetGio: DispatchWorkItem?
    private var daTraLoi = false

    var available: Bool { recognizer?.isAvailable ?? false }

    static func xinQuyen(_ xong: @escaping (Bool) -> Void) {
        SFSpeechRecognizer.requestAuthorization { st in
            guard st == .authorized else {
                DispatchQueue.main.async { xong(false) }
                return
            }
            AVAudioSession.sharedInstance().requestRecordPermission { ok in
                DispatchQueue.main.async { xong(ok) }
            }
        }
    }

    static var coQuyen: Bool {
        SFSpeechRecognizer.authorizationStatus() == .authorized &&
            AVAudioSession.sharedInstance().recordPermission == .granted
    }

    /// `xong` duoc goi TREN LUONG CHINH voi cau nghe duoc, hoac nil.
    func listenOnce(_ xong: @escaping (String?) -> Void) {
        guard task == nil else { return }
        guard let recognizer, recognizer.isAvailable else { xong(nil); return }
        daTraLoi = false

        func traLoi(_ s: String?) {
            DispatchQueue.main.async {
                guard !self.daTraLoi else { return }
                self.daTraLoi = true
                self.dung()
                xong(s?.trimmingCharacters(in: .whitespacesAndNewlines).nilNeuRong)
            }
        }

        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.playAndRecord, mode: .measurement, options: [.duckOthers, .defaultToSpeaker])
            try session.setActive(true, options: .notifyOthersOnDeactivation)

            let req = SFSpeechAudioBufferRecognitionRequest()
            req.shouldReportPartialResults = true
            if recognizer.supportsOnDeviceRecognition { req.requiresOnDeviceRecognition = true }
            request = req

            let input = engine.inputNode
            let format = input.outputFormat(forBus: 0)
            input.removeTap(onBus: 0)
            input.installTap(onBus: 0, bufferSize: 1024, format: format) { buf, _ in
                req.append(buf)
            }
            engine.prepare()
            try engine.start()

            var cuoi: String?
            task = recognizer.recognitionTask(with: req) { kq, loi in
                if let kq {
                    cuoi = kq.bestTranscription.formattedString
                    if kq.isFinal { traLoi(cuoi) }
                }
                if loi != nil { traLoi(cuoi) }
            }

            // Toi da 8 giay, roi lay cau tot nhat da nghe duoc.
            let h = DispatchWorkItem { traLoi(cuoi) }
            hetGio = h
            DispatchQueue.main.asyncAfter(deadline: .now() + 8, execute: h)
        } catch {
            traLoi(nil)
        }
    }

    func cancel() {
        daTraLoi = true
        dung()
    }

    private func dung() {
        hetGio?.cancel(); hetGio = nil
        if engine.isRunning { engine.stop() }
        engine.inputNode.removeTap(onBus: 0)
        request?.endAudio(); request = nil
        task?.cancel(); task = nil
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
    }
}

private extension String {
    var nilNeuRong: String? { isEmpty ? nil : self }
}
