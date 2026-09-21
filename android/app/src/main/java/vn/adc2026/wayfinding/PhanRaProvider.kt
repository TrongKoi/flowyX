package vn.adc2026.wayfinding

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/**
 * ====================================================================
 * NGUON PHAN RA - Gemini that, hoac ban mau
 * ====================================================================
 *
 * ----- KHOA GEMINI DAT O DAU, VA VI SAO -----
 *
 * Gan khoa vao APK thi BAT KY AI CUNG LAY RA DUOC: giai nen tep apk va
 * doc chuoi, khong can ky nang gi. Khong co cach nao giau mot khoa trong
 * mot ung dung chay tren may nguoi dung - mo hoa no thi ca khoa lan ma
 * giai deu nam trong cung goi cai dat.
 *
 * Nen khoa KHONG nam trong ma nguon va KHONG len GitHub. No doc tu
 * `local.properties` (da nam trong .gitignore) qua `BuildConfig`. Ai
 * muon chay ban goi Gemini that thi tu dien khoa cua minh vao may minh.
 *
 * Khong co khoa -> `MauProvider`. Va do la lua chon MAC DINH, co chu
 * dich:
 *
 *   · Buoi demo khong phu thuoc WiFi hoi truong, khong phu thuoc han
 *     muc Google, va khong lo khoa cho ai nhin man hinh.
 *   · Toan bo UX ma giam khao thay - man xem truoc, sua buoc, duyet,
 *     dong ho chay - la that. Chi co nguon sinh ra cac buoc la khac.
 *   · Noi backend sau chi la them mot lop hien thuc nua cua cung giao
 *     dien nay.
 *
 * Duong dung ve lau dai la proxy qua may chu cua nhom: khoa nam tren
 * may chu, app goi qua do. Luc co backend thi viet `ProxyProvider` va
 * doi mot dong o `chon()`.
 */
interface PhanRaProvider {
    /** Chay tren LUONG NEN. Nem ngoai le khi that bai. */
    fun phanRa(viec: String, moTaThem: String?): PhanRa.KetQua

    /** Ten hien trong Cai dat, de biet dang chay nguon nao. */
    val ten: String
}

object NguonPhanRa {

    /**
     * Chon nguon.
     *
     * Khong co khoa -> ban mau. Xem ghi chu dau tep ve vi sao day la
     * mac dinh chu khong phai mot duong du phong.
     */
    fun chon(ctx: Context): PhanRaProvider {
        val khoa = BuildConfig.GEMINI_API_KEY
        return if (khoa.isBlank()) MauProvider() else GeminiProvider(khoa)
    }
}

/**
 * ====================================================================
 * SYSTEM PROMPT
 * ====================================================================
 *
 * Moi dong trong day deu chan mot kieu tra loi da lam hong trai nghiem
 * cua nguoi ADHD, chu khong phai de cho "day du".
 */
internal object PhanRaPrompt {

    const val HE_THONG = """
Bạn chia nhỏ một công việc cho người trưởng thành có ADHD đang bế tắc,
không bắt đầu được.

QUY TẮC CỨNG
1. Tối đa 5 bước. Ít hơn thì tốt hơn. Việc đơn giản: 2-3 bước.
2. Bước 1 phải làm xong trong 2 phút và KHÔNG cần quyết định gì.
   Ví dụ tốt: "Mở tệp báo cáo và đọc lại tiêu đề."
   Ví dụ xấu: "Lên kế hoạch cho báo cáo."
3. Mỗi bước bắt đầu bằng ĐỘNG TỪ HÀNH ĐỘNG CỤ THỂ: mở, viết, gọi,
   gửi, in, đếm, xếp, hỏi, gạch.
   CẤM: nghiên cứu, tìm hiểu, chuẩn bị, xây dựng, tối ưu, rà soát,
   suy nghĩ về, lên kế hoạch.
4. Mỗi bước tối đa 12 từ.
5. Ước thời gian: bội số của 5, từ 5 đến 45.
6. Không động viên, không khen, không "bạn nên", không "hãy cố".
   Chỉ các bước.
7. Viết bằng ngôn ngữ của công việc đầu vào.
8. Không đủ thông tin để chia: trả steps rỗng và một câu hỏi duy nhất
   trong "need". Không bịa.

Chỉ trả JSON theo đúng dạng sau, không rào đón:
{"steps":[{"buoc_so":1,"ten_hanh_dong":"...","thoi_gian_du_tinh":5}],"need":null}
"""
}

/**
 * Ban mau - khong goi mang.
 *
 * KHONG phai mot ban gia de lap cho day. No chay dung duong ma that:
 * cung giao dien, cung do tre gia lap, cung dang JSON di qua
 * `PhanRa.doc`. Loi duy nhat khong tai hien duoc la loi mang.
 *
 * Cac buoc sinh theo KHUON, khong phai cau co dinh, nen thu ra luon
 * mang ten viec that cua nguoi dung - du de demo ma khong can mang.
 */
internal class MauProvider : PhanRaProvider {

    override val ten = "mẫu"

    override fun phanRa(viec: String, moTaThem: String?): PhanRa.KetQua {
        // Do tre gia lap: man hinh cho phai duoc nhin thay that, khong
        // phai nhay mot cai roi xong.
        Thread.sleep(900)
        val v = viec.trim().ifBlank { "việc này" }
        val json = JSONObject().apply {
            put("steps", JSONArray().apply {
                put(buoc(1, "Mở chỗ làm $v và đọc lại dòng đầu", 5))
                put(buoc(2, "Viết ra một câu về phần khó nhất", 10))
                put(buoc(3, "Làm xong phần dễ nhất trước", 15))
                put(buoc(4, "Đọc lại và gạch phần thừa", 10))
            })
            put("need", JSONObject.NULL)
        }
        return PhanRa.doc(json.toString())
    }

    private fun buoc(so: Int, ten: String, phut: Int) = JSONObject().apply {
        put("buoc_so", so); put("ten_hanh_dong", ten); put("thoi_gian_du_tinh", phut)
    }
}

/**
 * Goi Gemini that.
 *
 * Dung `HttpURLConnection` cua thu vien chuan thay vi them OkHttp hay
 * Retrofit: mot lan goi POST JSON khong can toi mot thu vien mang, va
 * moi phu thuoc them vao la mot thu co the hong luc build gap.
 */
internal class GeminiProvider(private val khoa: String) : PhanRaProvider {

    override val ten = "Gemini"

    override fun phanRa(viec: String, moTaThem: String?): PhanRa.KetQua {
        val cau = buildString {
            append("Công việc: ").append(viec.trim())
            moTaThem?.takeIf { it.isNotBlank() }?.let {
                append("\nNgười dùng nói thêm: ").append(it.trim())
            }
        }
        val than = JSONObject().apply {
            put("system_instruction", JSONObject().put("parts",
                JSONArray().put(JSONObject().put("text", PhanRaPrompt.HE_THONG))))
            put("contents", JSONArray().put(JSONObject()
                .put("role", "user")
                .put("parts", JSONArray().put(JSONObject().put("text", cau)))))
            // `responseMimeType` buoc mo hinh tra JSON thuan - bot han
            // truong hop no boc trong khoi ma. `PhanRa.goBocMa` van giu
            // lai vi khong phai ban API nao cung ton trong truong nay.
            put("generationConfig", JSONObject()
                .put("temperature", 0.4)
                .put("responseMimeType", "application/json"))
        }

        val url = URL("https://generativelanguage.googleapis.com/v1beta/" +
            "models/gemini-flash-latest:generateContent")
        val c = (url.openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            // Tran 8 giay: qua do thi man hinh chuyen sang duong tu chia.
            // Cho 30 giay roi bao loi la du de mat mach hoan toan.
            connectTimeout = 4000
            readTimeout = 8000
            doOutput = true
            setRequestProperty("Content-Type", "application/json; charset=utf-8")
            setRequestProperty("x-goog-api-key", khoa)
        }
        try {
            c.outputStream.use { it.write(than.toString().toByteArray(Charsets.UTF_8)) }
            if (c.responseCode !in 200..299) {
                throw IllegalStateException("Gemini tra ma ${c.responseCode}")
            }
            val tra = c.inputStream.bufferedReader(Charsets.UTF_8).use { it.readText() }
            return PhanRa.doc(layChu(tra))
        } finally {
            c.disconnect()
        }
    }

    /** Boc lay phan van ban trong goi tra loi cua Gemini. */
    private fun layChu(tra: String): String {
        val o = JSONObject(tra)
        val ungVien = o.optJSONArray("candidates")
            ?: throw IllegalArgumentException("khong co candidates")
        val phan = ungVien.optJSONObject(0)?.optJSONObject("content")?.optJSONArray("parts")
            ?: throw IllegalArgumentException("khong co parts")
        return phan.optJSONObject(0)?.optString("text")
            ?: throw IllegalArgumentException("khong co text")
    }
}
