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
        versionCode = 5
        versionName = "0.5"
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
