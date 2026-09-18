package vn.adc2026.wayfinding

import android.annotation.TargetApi
import android.content.Context
import android.health.connect.HealthConnectManager
import android.health.connect.ReadRecordsRequestUsingFilters
import android.health.connect.ReadRecordsResponse
import android.health.connect.TimeInstantRangeFilter
import android.health.connect.datatypes.SleepSessionRecord
import android.health.connect.datatypes.StepsRecord
import android.os.OutcomeReceiver
import java.time.Instant
import java.util.Calendar
import java.util.Date
import java.util.concurrent.Executors

/**
 * ====================================================================
 * NGUON: HEALTH CONNECT (Android 14+)
 * ====================================================================
 *
 * Tu Android 14 (API 34), Health Connect nam TRONG he dieu hanh:
 * `android.health.connect.*` la API nen tang, khong phai thu vien ngoai.
 * Nho vay Flowy doc duoc du lieu suc khoe ma khong keo them mot dong
 * AndroidX nao vao ban dung - dieu quan trong voi du an nay vi toan bo
 * app duoc dung khong qua Gradle (xem tools/build_khong_gradle.sh).
 *
 * ----- Vi sao tach han ra mot tep -----
 *
 * Moi tham chieu trong day deu la lop chi ton tai tu API 34, va
 * `java.time.Instant` chi co tu API 26. minSdk cua Flowy la 24. Gom
 * chung vao mot lop RIENG nghia la may Android 7 khong bao gio NAP lop
 * nay - `SucKhoe.coNguon()` kiem tra SDK_INT truoc khi cham toi no, nen
 * trinh nap lop khong bao gio phai giai cac tham chieu ben trong.
 *
 * Neu viet thang vao `SucKhoe` thi may cu se sap ngay khi nap lop do,
 * ke ca khi khong ai bam vao tinh nang suc khoe.
 *
 * ----- Vi sao doc theo tung ngay -----
 *
 * Health Connect tra ve BAN GHI THO: moi lan dong ho deo ghi mot doan
 * ngu, moi lan dien thoai dem buoc. Flowy khong can chung. Ham duoi doc
 * tung ngay mot roi CONG LAI ngay tai cho, va chi con so tong di vao
 * co so du lieu. Ban ghi tho khong bao gio duoc luu lai.
 */
@TargetApi(34)
object SucKhoeHC {

    /** Luong chay vong doc (mot ngay mot vong, tuan tu). */
    private val may = Executors.newSingleThreadExecutor()

    /**
     * Luong RIENG cho ket qua tra ve.
     *
     * Bat buoc phai khac `may`: `docThoi` chan tren `may` de cho ket qua,
     * nen neu Health Connect goi lai cung tren `may` thi loi goi lai do se
     * xep hang SAU cai dang cho - khoa cheo, treo dung 8 giay roi tra ve
     * rong. Loi nay khong hien ra trong thu nghiem nhanh vi no van "chay",
     * chi la khong bao gio co du lieu.
     */
    private val traLoi = Executors.newCachedThreadPool()

    fun coTrenMay(ctx: Context): Boolean = try {
        ctx.getSystemService(HealthConnectManager::class.java) != null
    } catch (_: Throwable) {
        false
    }

    /**
     * Doc `soNgay` ngay gan nhat (khong tinh hom nay - hom nay chua het,
     * so lieu con dang chay).
     *
     * `xong` duoc goi mot lan, o luong nen, voi `null` khi that bai.
     */
    fun doc(ctx: Context, soNgay: Int, xong: (List<SucKhoe.Ngay>?) -> Unit) {
        val hcm = try {
            ctx.getSystemService(HealthConnectManager::class.java)
        } catch (_: Throwable) { null }
        if (hcm == null) { xong(null); return }

        val canNgu = SucKhoe.docNgu(ctx)
        val canBuoc = SucKhoe.docBuoc(ctx)
        if (!canNgu && !canBuoc) { xong(emptyList()); return }

        may.execute {
            val ra = ArrayList<SucKhoe.Ngay>(soNgay)
            try {
                for (lui in 1..soNgay) {
                    val dau = nuaDem(-lui)
                    val cuoi = nuaDem(-lui + 1)
                    val ngay = SucKhoe.dinhDangNgay(Date(dau.toEpochMilli()))
                    val ngu = if (canNgu) tongNgu(hcm, dau, cuoi) else null
                    val buoc = if (canBuoc) tongBuoc(hcm, dau, cuoi) else null
                    if (ngu != null || buoc != null) ra.add(SucKhoe.Ngay(ngay, ngu, buoc))
                }
                xong(ra)
            } catch (_: Throwable) {
                // Quyen bi rut giua chung, hoac Health Connect dang cap nhat.
                // Khong co gi de cuu - bao that bai, man hinh se noi voi
                // nguoi dung thay vi im lang hien so cu.
                xong(null)
            }
        }
    }

    /** Tong so PHUT ngu cua cac doan ngu chong len khoang [dau, cuoi). */
    private fun tongNgu(hcm: HealthConnectManager, dau: Instant, cuoi: Instant): Int? {
        val ds = docThoi(hcm, SleepSessionRecord::class.java, dau, cuoi) ?: return null
        var giay = 0L
        for (r in ds) {
            // Cat phan nam ngoai khoang: mot giac ngu vat qua nua dem
            // thuoc ve ca hai ngay, va chi phan trong ngay moi duoc tinh.
            val b = maxOf(r.startTime, dau)
            val k = minOf(r.endTime, cuoi)
            if (k.isAfter(b)) giay += k.epochSecond - b.epochSecond
        }
        return (giay / 60).toInt()
    }

    private fun tongBuoc(hcm: HealthConnectManager, dau: Instant, cuoi: Instant): Int? {
        val ds = docThoi(hcm, StepsRecord::class.java, dau, cuoi) ?: return null
        var tong = 0L
        for (r in ds) tong += r.count
        return tong.toInt()
    }

    /**
     * Goi `readRecords` bat dong bo roi CHO ket qua - ham nay da chay o
     * luong nen cua `may`, nen chan o day khong lam dung giao dien.
     */
    private fun <T : android.health.connect.datatypes.Record> docThoi(
        hcm: HealthConnectManager, lop: Class<T>, dau: Instant, cuoi: Instant): List<T>? {
        val yeuCau = ReadRecordsRequestUsingFilters.Builder(lop)
            .setTimeRangeFilter(TimeInstantRangeFilter.Builder()
                .setStartTime(dau).setEndTime(cuoi).build())
            .build()

        val khoa = java.util.concurrent.CountDownLatch(1)
        var ketQua: List<T>? = null
        hcm.readRecords(yeuCau, traLoi, object :
            OutcomeReceiver<ReadRecordsResponse<T>, android.health.connect.HealthConnectException> {
            override fun onResult(r: ReadRecordsResponse<T>) {
                ketQua = r.records; khoa.countDown()
            }
            override fun onError(e: android.health.connect.HealthConnectException) {
                ketQua = null; khoa.countDown()
            }
        })
        // 8 giay: doc cuc bo, khong qua mang. Qua lau nghia la co su co.
        khoa.await(8, java.util.concurrent.TimeUnit.SECONDS)
        return ketQua
    }

    /** Nua dem cua ngay hom nay + `lech` ngay, theo mui gio may. */
    private fun nuaDem(lech: Int): Instant = Calendar.getInstance().apply {
        add(Calendar.DAY_OF_YEAR, lech)
        set(Calendar.HOUR_OF_DAY, 0); set(Calendar.MINUTE, 0)
        set(Calendar.SECOND, 0); set(Calendar.MILLISECOND, 0)
    }.time.toInstant()
}
