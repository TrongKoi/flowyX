package vn.adc2026.wayfinding

import kotlin.math.abs
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.hypot
import kotlin.math.min
import kotlin.math.sin

/**
 * Ban dich nguyen van cua `adc_wayfinding/wayfinding/arcore.py`.
 *
 * File goc la ban tham chieu va DA DUOC KIEM CHUNG dau-cuoi voi
 * run_bridge.py (xem tools/android_sim.py). Sua o mot ben thi PHAI sua
 * ben con lai - tests/test_arcore.py ben Python va ArMathTest.kt ben nay
 * chay cung mot bo ca kiem thu.
 *
 * ------------------------------------------------------------------
 * QUY UOC TRUC - cho nay sai la ca he thong chi nguoc duong
 * ------------------------------------------------------------------
 *
 * ARCore dung he toa do TAY PHAI, truc y HUONG LEN. Mat phang di lai
 * la x-z. He ban do cua du an la 2D:
 *
 *      ban do X      <-  ARCore x
 *      ban do Y      <-  ARCore z
 *      ban do theta  <-  goc trong mat phang (x, z), NGUOC chieu kim
 *                        dong ho, 0 do la huong duong truc x
 *
 * Phep chieu nay bo truc y nen he 2D thu duoc la he TAY TRAI so voi
 * ARCore. Khong sao - mien la ap dung DUNG MOT phep chieu cho ca camera
 * lan moc neo, va tools/phone_sim.py (ban mo phong da dung de kiem thu
 * ca he thong) cung dung dung quy uoc nay.
 */
object ArMath {

    /**
     * Truc phap tuyen cua AugmentedImage trong he toa do cua chinh no.
     *
     * CANH BAO: phai KIEM CHUNG TREN MAY THAT. Neu goc doc ra lech dung
     * 180 do so voi thuc te, doi thanh floatArrayOf(0f, -1f, 0f) roi
     * chay lai ArMathTest.
     */
    val IMAGE_NORMAL_AXIS = floatArrayOf(0f, 1f, 0f)

    /** Camera ARCore nhin theo huong tru Z cua chinh no. */
    val CAMERA_FORWARD_AXIS = floatArrayOf(0f, 0f, -1f)

    /** Chuan hoa goc ve khoang (-180, 180]. */
    fun normAngle(deg: Double): Double {
        val a = (deg + 180.0).mod(360.0) - 180.0
        return if (a == -180.0) 180.0 else a
    }

    /**
     * Quay vector v bang quaternion (x, y, z, w).
     *
     * Thu tu thanh phan dung nhu ARCore Pose.getRotationQuaternion()
     * tra ve: [x, y, z, w].
     */
    fun rotate(q: FloatArray, v: FloatArray): DoubleArray {
        val qx = q[0].toDouble(); val qy = q[1].toDouble()
        val qz = q[2].toDouble(); val qw = q[3].toDouble()
        val vx = v[0].toDouble(); val vy = v[1].toDouble(); val vz = v[2].toDouble()

        // t = 2 * (q_vec x v)
        val tx = 2.0 * (qy * vz - qz * vy)
        val ty = 2.0 * (qz * vx - qx * vz)
        val tz = 2.0 * (qx * vy - qy * vx)

        // v' = v + w*t + (q_vec x t)
        return doubleArrayOf(
            vx + qw * tx + (qy * tz - qz * ty),
            vy + qw * ty + (qz * tx - qx * tz),
            vz + qw * tz + (qx * ty - qy * tx),
        )
    }

    /** Goc cua mot truc sau khi chieu xuong mat phang (x, z). */
    fun headingDeg(q: FloatArray, axis: FloatArray): Double {
        val d = rotate(q, axis)
        return normAngle(Math.toDegrees(atan2(d[2], d[0])))
    }

    /**
     * Do dai hinh chieu cua truc len mat phang di lai, 0..1.
     *
     * Gan 1 nghia la truc nam ngang va goc rat dang tin. Gan 0 nghia la
     * truc thang dung va goc gan nhu vo nghia - vi du anh bi nhan tren
     * san hoac tran thay vi tren tuong.
     */
    fun horizontalStrength(q: FloatArray, axis: FloatArray): Double {
        val d = rotate(q, axis)
        return min(1.0, hypot(d[0], d[2]))
    }

    /** Tu the camera trong he ban do 2D. */
    fun cameraPose2d(t: FloatArray, q: FloatArray): Pose2D =
        Pose2D(t[0].toDouble(), t[2].toDouble(), headingDeg(q, CAMERA_FORWARD_AXIS))

    /** Tu the moc neo trong he ban do 2D. theta la huong mat ma quay ra. */
    fun imagePose2d(t: FloatArray, q: FloatArray): Pose2D =
        Pose2D(t[0].toDouble(), t[2].toDouble(), headingDeg(q, IMAGE_NORMAL_AXIS))

    /**
     * Tu the moc neo SO VOI camera - dung dinh dang bridge mong doi.
     *
     *     camFromAnchor = inv(T_world_cam) @ T_world_anchor
     */
    fun camFromAnchor(cam: Pose2D, anchor: Pose2D): Pose2D {
        val th = Math.toRadians(cam.theta)
        val c = cos(th); val s = sin(th)
        val dx = anchor.x - cam.x
        val dy = anchor.y - cam.y
        return Pose2D(
            x = c * dx + s * dy,
            y = -s * dx + c * dy,
            theta = normAngle(anchor.theta - cam.theta),
        )
    }

    /**
     * Mot phan tu cua mang `markers`, hoac null neu khong dang tin.
     *
     * Loc bo ba truong hop, cung tinh than voi bo loc cua
     * lop nhan dien ben Python:
     *   - phap tuyen gan nhu thang dung: goc vo nghia
     *   - moc qua xa: sai so goc lon, vuot nguong do o thi nghiem Muc 3.2
     *   - moc qua gan: duoi 15cm thi uoc luong rat nhieu
     */
    fun markerEntry(
        markerId: String,
        camT: FloatArray,
        camQ: FloatArray,
        imgT: FloatArray,
        imgQ: FloatArray,
        maxDistance: Double = 6.0,
        minHorizontal: Double = 0.35,
    ): MarkerEntry? {
        val strength = horizontalStrength(imgQ, IMAGE_NORMAL_AXIS)
        if (strength < minHorizontal) return null

        val cam = cameraPose2d(camT, camQ)
        val anchor = imagePose2d(imgT, imgQ)
        val rel = camFromAnchor(cam, anchor)

        val distance = hypot(anchor.x - cam.x, anchor.y - cam.y)
        if (distance > maxDistance || distance < 0.15) return null

        val quality = maxOf(0.0, 1.0 - distance / maxDistance) * strength
        return MarkerEntry(
            id = markerId,
            x = round3(rel.x),
            y = round3(rel.y),
            theta = round1(rel.theta),
            distance = round3(distance),
            quality = round3(quality),
        )
    }

    private fun round1(v: Double) = Math.round(v * 10.0) / 10.0
    private fun round3(v: Double) = Math.round(v * 1000.0) / 1000.0
}

/** Mot tu the trong mat phang. theta tinh bang do. */
data class Pose2D(val x: Double, val y: Double, val theta: Double)

/** Mot moc neo dien thoai nhin thay, o dinh dang goi tin cua bridge. */
data class MarkerEntry(
    val id: String,
    val x: Double,
    val y: Double,
    val theta: Double,
    val distance: Double,
    val quality: Double,
)
