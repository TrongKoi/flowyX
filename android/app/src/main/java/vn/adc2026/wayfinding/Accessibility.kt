package vn.adc2026.wayfinding

import android.accessibilityservice.AccessibilityServiceInfo
import android.content.Context
import android.view.View
import android.view.accessibility.AccessibilityManager

/**
 * Phoi hop giua TalkBack va giong noi cua chinh app.
 *
 * ------------------------------------------------------------------
 * Van de: HAI GIONG NOI CUNG LUC
 * ------------------------------------------------------------------
 *
 * Nguoi dung khiem thi gan nhu luon bat TalkBack. Ma app nay cung tu
 * doc thanh tieng. Neu ca hai cung noi thi chong len nhau va khong
 * nghe ra gi ca - loi rat de mac vi may lap trinh vien thu nghiem
 * thuong TAT TalkBack di cho de lam viec.
 *
 * Cach chia viec:
 *
 *   Noi dung MAN HINH (trang thai, loi, huong dan dat may)
 *       -> de TalkBack doc, qua vung song va announceForAccessibility
 *       -> app KHONG dung TTS rieng, tranh doc hai lan
 *
 *   Chi dan DIEU HUONG (re trai, canh bao cau thang)
 *       -> app tu doc bang TTS rieng
 *       -> vi day la thong tin theo thoi gian thuc, khong duoc xep
 *          hang cho TalkBack doc xong phan giao dien nguoi dung dang
 *          vuot tay tren man hinh
 *
 * Va trong luc dieu huong thi TAT vung song di: `detail` doi lien tuc
 * moi khi thay moc neo moi, de nguyen thi TalkBack lai lai lien mieng
 * de len tren giong chi dan.
 */
class Accessibility(context: Context) {

    private val manager =
        context.getSystemService(Context.ACCESSIBILITY_SERVICE) as? AccessibilityManager

    /**
     * Co dich vu tro nang nao dang DOC THANH TIENG khong.
     *
     * Kiem tra rieng loai phan hoi bang giong noi chu khong chi hoi
     * isEnabled: may co the dang bat dich vu tro nang khac (phong to,
     * dieu khien bang cong tac) ma khong doc gi ca - luc do app van
     * phai tu doc.
     */
    val spokenFeedbackOn: Boolean
        get() {
            val m = manager ?: return false
            if (!m.isEnabled) return false
            return m.getEnabledAccessibilityServiceList(
                AccessibilityServiceInfo.FEEDBACK_SPOKEN
            ).isNotEmpty()
        }

    /**
     * Doc mot cau thuoc ve GIAO DIEN.
     *
     * TalkBack dang bat thi nho no doc, de chi co mot giong. Khong thi
     * app tu doc bang TTS cua minh.
     */
    @Suppress("DEPRECATION")
    fun announce(view: View, text: String, speaker: Speaker?, useSpeech: Boolean) {
        if (text.isBlank()) return
        if (spokenFeedbackOn) {
            // announceForAccessibility bi danh dau deprecated tu API 36
            // vi Google khuyen dung VUNG SONG thay the. Cho hau het
            // truong hop thi dung - va app nay da dung vung song cho o
            // trang thai.
            //
            // Nhung vung song chi kich hoat khi NOI DUNG DOI. Rieng
            // truong hop "doc lai dung cau vua roi" thi noi dung khong
            // doi, nen vung song im lang. Chua co API thay the cho viec
            // nay, nen van phai dung ham cu.
            view.announceForAccessibility(text)
        } else if (useSpeech) {
            speaker?.say(text, urgent = false)
        }
    }

    /**
     * Bat/tat vung song cua mot o.
     *
     * Dung khi chuyen giua luc dat may (nen cho TalkBack doc thay doi)
     * va luc dang di duong (khong nen, vi noi dung doi lien tuc).
     */
    fun setLiveRegion(view: View, on: Boolean) {
        view.accessibilityLiveRegion =
            if (on) View.ACCESSIBILITY_LIVE_REGION_POLITE
            else View.ACCESSIBILITY_LIVE_REGION_NONE
    }
}
