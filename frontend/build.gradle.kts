plugins {
    id("com.android.library")
    id("org.jetbrains.kotlin.android")
}

// Module GIAO DIEN, tach rieng khoi `app`.
//
// Ly do tach: `app` lo phan CAM BIEN (ARCore, Depth API, khi ap ke, micro)
// va vong lap gui goi tin. Module nay lo phan NGUOI DUNG NHIN THAY. Tron
// hai thu do vao mot cho lam ca hai kho sua: doi mau mot cai nut khong nen
// nam cung file voi vong lap camera.
//
// Day la thu vien Android (`com.android.library`), khong phai ung dung -
// no khong co Activity khoi dong rieng, chi cung cap View cho `app` dung.
android {
    namespace = "vn.adc2026.frontend"
    compileSdk = 34

    defaultConfig {
        minSdk = 24
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    // KHONG them androidx/Compose o day - xem docs/UIUX_QUYET_DINH.md.
    // Giao dien ve bang Canvas thuan de tranh keo theo hang chuc
    // dependency co the hong luc build gap truoc ngay thi.
}
