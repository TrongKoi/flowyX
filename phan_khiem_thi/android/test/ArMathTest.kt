package vn.adc2026.wayfinding

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.hypot
import kotlin.math.sin

/**
 * Ban doi chieu cua `adc_wayfinding/tests/test_arcore.py`.
 *
 * Hai file phai chay CUNG MOT bo ca kiem thu. Ben Python la ban tham
 * chieu va da duoc kiem chung dau-cuoi voi run_bridge.py qua
 * tools/android_sim.py; ben nay chung minh ban dich Kotlin cho ra dung
 * ket qua do.
 *
 * Sai quy uoc truc la he thong chi NGUOC duong ma van tu tin - dung
 * loai loi ma toan bo thiet ke dang phong.
 *
 * Chay: ./gradlew :app:testDebugUnitTest
 */
class ArMathTest {

    private val identity = floatArrayOf(0f, 0f, 0f, 1f)
    private val angles = listOf(0.0, 30.0, 45.0, 90.0, 135.0, 180.0, -45.0, -90.0, -135.0)

    // --------------------------------------------------------------
    // Tien ich - CHI dung cho kiem thu, nang tu the 2D len 6 bac tu do.
    // Tren may that ARCore cho san quaternion.
    // Ban goc: tools/android_sim.py
    // --------------------------------------------------------------

    private fun quatAxisY(deg: Double): FloatArray {
        val h = Math.toRadians(deg) / 2.0
        return floatArrayOf(0f, sin(h).toFloat(), 0f, cos(h).toFloat())
    }

    private fun quatAxisX(deg: Double): FloatArray {
        val h = Math.toRadians(deg) / 2.0
        return floatArrayOf(sin(h).toFloat(), 0f, 0f, cos(h).toFloat())
    }

    private fun quatMul(a: FloatArray, b: FloatArray): FloatArray {
        val ax = a[0].toDouble(); val ay = a[1].toDouble()
        val az = a[2].toDouble(); val aw = a[3].toDouble()
        val bx = b[0].toDouble(); val by = b[1].toDouble()
        val bz = b[2].toDouble(); val bw = b[3].toDouble()
        return floatArrayOf(
            (aw * bx + ax * bw + ay * bz - az * by).toFloat(),
            (aw * by - ax * bz + ay * bw + az * bx).toFloat(),
            (aw * bz + ax * by - ay * bx + az * bw).toFloat(),
            (aw * bw - ax * bx - ay * by - az * bz).toFloat(),
        )
    }

    /** Camera 2D -> quaternion. Quay quanh truc y goc (-theta - 90). */
    private fun cameraQuat(theta: Double) = quatAxisY(-theta - 90.0)

    /**
     * Bien/ma dan TUONG -> quaternion.
     *
     * Anh dung thang tren tuong, nen phai lat 90 do quanh truc x truoc
     * de phap tuyen +Y cua anh nam ngang, roi moi quay quanh truc y.
     */
    private fun signQuat(theta: Double) = quatMul(quatAxisY(-theta - 90.0), quatAxisX(-90.0))

    private fun assertAngle(expected: Double, actual: Double, tol: Double = 1e-4) {
        assertTrue(
            "mong doi $expected, nhan $actual",
            abs(ArMath.normAngle(expected - actual)) < tol,
        )
    }

    // --------------------------------------------------------------
    // Quaternion
    // --------------------------------------------------------------

    @Test
    fun quaternionDonViKhongDoiVector() {
        val out = ArMath.rotate(identity, floatArrayOf(1f, 2f, 3f))
        assertEquals(1.0, out[0], 1e-9)
        assertEquals(2.0, out[1], 1e-9)
        assertEquals(3.0, out[2], 1e-9)
    }

    @Test
    fun quayQuanhTrucY90Do() {
        // Quay +90 do quanh truc y: truc +x di ve huong -z
        val out = ArMath.rotate(quatAxisY(90.0), floatArrayOf(1f, 0f, 0f))
        assertEquals(0.0, out[0], 1e-6)
        assertEquals(0.0, out[1], 1e-6)
        assertEquals(-1.0, out[2], 1e-6)
    }

    @Test
    fun quaternionGiuDoDaiVector() {
        val q = quatMul(quatAxisY(37.0), quatAxisX(-52.0))
        val v = floatArrayOf(0.3f, -0.8f, 0.5f)
        val out = ArMath.rotate(q, v)
        val before = hypot(hypot(0.3, -0.8), 0.5)
        val after = hypot(hypot(out[0], out[1]), out[2])
        assertEquals(before, after, 1e-6)
    }

    // --------------------------------------------------------------
    // Quy uoc truc - phan de sai nhat
    // --------------------------------------------------------------

    @Test
    fun cameraKhongQuayNhinVeHuongTruZ() {
        // ARCore: camera nhin theo huong tru z cua chinh no. Chieu xuong
        // mat phang (x, z) thi vector (0, 0, -1) co goc atan2(-1, 0) = -90
        assertAngle(-90.0, ArMath.headingDeg(identity, ArMath.CAMERA_FORWARD_AXIS))
    }

    @Test
    fun phapTuyenAnhKhongQuayLaThangDung() {
        // Truc +y cua AugmentedImage la phap tuyen. Chua quay thi no
        // thang dung, hinh chieu xuong mat phang di lai bang 0 - goc luc
        // do vo nghia va phai bi loai.
        assertEquals(
            0.0,
            ArMath.horizontalStrength(identity, ArMath.IMAGE_NORMAL_AXIS),
            1e-6,
        )
    }

    @Test
    fun phapTuyenAnhDanTuongNamNgang() {
        for (th in angles) {
            assertEquals(
                "theta=$th",
                1.0,
                ArMath.horizontalStrength(signQuat(th), ArMath.IMAGE_NORMAL_AXIS),
                1e-6,
            )
        }
    }

    @Test
    fun vongTronTuTheCamera() {
        for (th in angles) {
            val t = floatArrayOf(3f, 1.35f, -2f)
            val got = ArMath.cameraPose2d(t, cameraQuat(th))
            assertEquals(3.0, got.x, 1e-6)
            assertEquals(-2.0, got.y, 1e-6)
            assertAngle(th, got.theta)
        }
    }

    @Test
    fun vongTronTuTheBienTuong() {
        for (th in angles) {
            val t = floatArrayOf(-1.5f, 1.5f, 4f)
            val got = ArMath.imagePose2d(t, signQuat(th))
            assertEquals(-1.5, got.x, 1e-6)
            assertEquals(4.0, got.y, 1e-6)
            assertAngle(th, got.theta)
        }
    }

    @Test
    fun banDoXLayTuArcoreXVaBanDoYLayTuArcoreZ() {
        // Chot quy uoc chieu truc - cho de dich sai nhat tu Python
        val got = ArMath.cameraPose2d(floatArrayOf(7f, 1.35f, -3f), identity)
        assertEquals(7.0, got.x, 1e-9)
        assertEquals(-3.0, got.y, 1e-9)
    }

    // --------------------------------------------------------------
    // Moc neo so voi camera
    // --------------------------------------------------------------

    @Test
    fun mocThangTruocMatCamera() {
        val cam = Pose2D(0.0, 0.0, 0.0)
        val anchor = Pose2D(2.0, 0.0, 180.0)      // ma quay mat lai phia camera
        val rel = ArMath.camFromAnchor(cam, anchor)
        assertEquals(2.0, rel.x, 1e-9)
        assertEquals(0.0, rel.y, 1e-9)
        assertAngle(180.0, rel.theta)
    }

    @Test
    fun mocBenTraiCamera() {
        // Quay nguoi 90 do thi moc truoc do o phia truoc chuyen sang ben phai
        val cam = Pose2D(0.0, 0.0, 90.0)
        val anchor = Pose2D(2.0, 0.0, 180.0)
        val rel = ArMath.camFromAnchor(cam, anchor)
        assertEquals(0.0, rel.x, 1e-9)
        assertEquals(-2.0, rel.y, 1e-9)
    }

    @Test
    fun khopVoiBanThamChieuPython() {
        // Gia tri lay tu tests/test_arcore.py, ca test_khop_voi_phone_sim
        val cam = Pose2D(4.0, 1.0, 35.0)
        val anchor = Pose2D(6.5, 2.2, -120.0)
        val rel = ArMath.camFromAnchor(cam, anchor)

        // inv(T_cam) @ T_anchor tinh tay
        val th = Math.toRadians(35.0)
        val dx = 6.5 - 4.0
        val dy = 2.2 - 1.0
        assertEquals(cos(th) * dx + sin(th) * dy, rel.x, 1e-9)
        assertEquals(-sin(th) * dx + cos(th) * dy, rel.y, 1e-9)
        assertAngle(-155.0, rel.theta)
    }

    // --------------------------------------------------------------
    // Loc moc neo khong dang tin
    // --------------------------------------------------------------

    @Test
    fun loaiMocQuaXa() {
        val entry = ArMath.markerEntry(
            "11",
            floatArrayOf(0f, 1.35f, 0f), cameraQuat(0.0),
            floatArrayOf(9f, 1.5f, 0f), signQuat(180.0),
            maxDistance = 6.0,
        )
        assertNull(entry)
    }

    @Test
    fun loaiMocQuaGan() {
        // Duoi 15cm thi uoc luong goc rat nhieu, va thuc te khong xay ra
        val entry = ArMath.markerEntry(
            "11",
            floatArrayOf(0f, 1.35f, 0f), cameraQuat(0.0),
            floatArrayOf(0.05f, 1.5f, 0f), signQuat(180.0),
        )
        assertNull(entry)
    }

    @Test
    fun loaiAnhNamNgangTrenSan() {
        // Anh nam ngua tren san thi phap tuyen thang dung, goc trong mat
        // phang di lai vo nghia. Phai loai, khong duoc doan bua.
        val entry = ArMath.markerEntry(
            "11",
            floatArrayOf(0f, 1.35f, 0f), cameraQuat(0.0),
            floatArrayOf(2f, 0f, 0f), identity,
        )
        assertNull(entry)
    }

    @Test
    fun chatLuongGiamTheoKhoangCach() {
        val camT = floatArrayOf(0f, 1.35f, 0f)
        val camQ = cameraQuat(0.0)
        val gan = ArMath.markerEntry(
            "11", camT, camQ, floatArrayOf(1f, 1.5f, 0f), signQuat(180.0)
        )
        val xa = ArMath.markerEntry(
            "11", camT, camQ, floatArrayOf(4f, 1.5f, 0f), signQuat(180.0)
        )
        assertNotNull(gan)
        assertNotNull(xa)
        assertTrue(gan!!.quality > xa!!.quality)
    }

    @Test
    fun mocHopLeDuTruongBridgeCan() {
        val entry = ArMath.markerEntry(
            "12",
            floatArrayOf(0f, 1.35f, 0f), cameraQuat(0.0),
            floatArrayOf(2f, 1.5f, 0f), signQuat(180.0),
        )
        assertNotNull(entry)
        assertEquals("12", entry!!.id)
        assertEquals(2.0, entry.distance, 1e-3)
    }

    // --------------------------------------------------------------
    // Chuan hoa goc
    // --------------------------------------------------------------

    @Test
    fun chuanHoaGocVeKhoangMoRong() {
        assertEquals(0.0, ArMath.normAngle(360.0), 1e-9)
        assertEquals(-90.0, ArMath.normAngle(270.0), 1e-9)
        assertEquals(180.0, ArMath.normAngle(180.0), 1e-9)
        assertEquals(180.0, ArMath.normAngle(-180.0), 1e-9)
        assertEquals(1.0, ArMath.normAngle(361.0), 1e-9)
    }
}
