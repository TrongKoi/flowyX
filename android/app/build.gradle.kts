import java.io.FileInputStream
import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "vn.adc2026.wayfinding"
    compileSdk = 34

    defaultConfig {
        // Khac voi OpticGuard de hai app cai song song duoc tren cung mot
        // may. `namespace` giu nguyen: doi no se phai sua duong dan goi
        // cua toan bo ma Kotlin.
        applicationId = "vn.boussolex.flowy"
        // API 24 la muc cu nhat con dang ho tro. Flowy khong doi phan
        // cung gi dac biet - khong ARCore, khong camera.
        minSdk = 24
        targetSdk = 34
        versionCode = 6
        versionName = "0.5.1"

        // ================================================================
        // KHOA GEMINI - KHONG BAO GIO NAM TRONG MA NGUON
        // ================================================================
        //
        // Gan khoa vao APK thi bat ky ai cung lay ra duoc: giai nen tep
        // apk va doc chuoi, khong can ky nang gi. Ma hoa cung vo nghia -
        // ca khoa lan ma giai deu nam trong cung goi cai dat.
        //
        // Nen khoa doc tu `local.properties`, tep da nam trong
        // .gitignore va khong bao gio len GitHub. Ai muon chay ban goi
        // Gemini that thi them mot dong vao may minh:
        //
        //     GEMINI_API_KEY=...
        //
        // Khong co khoa -> rong -> app dung `MauProvider`. Do la mac
        // dinh CO CHU DICH, khong phai duong du phong: buoi demo khong
        // phu thuoc WiFi hoi truong, khong phu thuoc han muc Google, va
        // khong lo khoa cho ai nhin man hinh. Xem `PhanRaProvider.kt`.
        //
        // Duong dung ve lau dai la proxy qua may chu cua nhom.
        val tepCucBo = rootProject.file("local.properties")
        val props = Properties()
        if (tepCucBo.exists()) FileInputStream(tepCucBo).use { props.load(it) }
        val khoaGemini = props.getProperty("GEMINI_API_KEY", "")
        buildConfigField("String", "GEMINI_API_KEY", "\"$khoaGemini\"")
    }

    buildFeatures {
        buildConfig = true
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }

    testOptions {
        unitTests.isReturnDefaultValues = true
    }
}

dependencies {
    implementation(project(":frontend"))

    // KHONG co phu thuoc ngoai nao trong ban chay.
    //
    // App chi can Activity, TextToSpeech, Vibrator, AlarmManager va
    // HttpURLConnection - deu co san trong android.jar tu API 24.
    //
    // Ban dieu huong tung keo theo ARCore va ML Kit. Flowy khong nhin ra
    // ngoai nen khong can ca hai, va bo chung di lam APK nho han, build
    // nhanh han, va bot hai cho co the hong luc build gap.

    testImplementation("junit:junit:4.13.2")

    // ----------------------------------------------------------------
    // VI SAO CAN org.json THAT CHO UNIT TEST
    // ----------------------------------------------------------------
    //
    // `org.json` trong android.jar chi la ban RONG. Voi
    // `unitTests.isReturnDefaultValues = true` o tren, no khong nem loi
    // nua - no lang le tra ve null va 0.
    //
    // Do la truong hop te nhat: `SoNhatKyTest` se XANH trong khi
    // `SoNhatKy` khong doc duoc gi ca.
    //
    // Ban that nay chi nam tren duong chay cua test, khong vao APK.
    testImplementation("org.json:json:20231013")
}
