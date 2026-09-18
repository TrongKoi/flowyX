#!/usr/bin/env bash
# =====================================================================
#  BUILD APK KHONG CAN GRADLE - duong du phong.
#
#  Duong chinh van la:  cd android && ./gradlew assembleDebug
#  Dung script nay khi Gradle/Android Studio hong truoc gio thi, hoac tren
#  may chi co Ubuntu + mang han che (khong vao duoc dl.google.com).
#
#  Can (Ubuntu 24.04):
#     sudo apt install aapt dalvik-exchange zipalign apksigner openjdk-17-jdk-headless
#     kotlinc 2.x          (https://github.com/JetBrains/kotlin/releases)
#     android.jar API 34   (co resources.arsc ben trong)
#
#  Chay:
#     ANDROID_JAR=/duong/android.jar KOTLINC=/duong/kotlinc/bin/kotlinc \
#       android/tools/build_khong_gradle.sh
#
#  Ra: android/build-thu-cong/flowyx-debug.apk (ky bang khoa debug tu tao)
#
#  Khac ban Gradle o hai cho, noi thang:
#    - aapt (v1) thay aapt2, dx thay d8. Bytecode Kotlin dich o JVM 1.8 va
#      lambda thanh lop (-Xlambdas=class) de dx doc duoc.
#    - Khong co R8/minify. APK lon hon ban release mot chut.
# =====================================================================
set -euo pipefail

GOC="$(cd "$(dirname "$0")/../.." && pwd)"
APP="$GOC/android/app/src/main"
FRONT="$GOC/frontend/src/main/java"
RA="$GOC/android/build-thu-cong"
ANDROID_JAR="${ANDROID_JAR:?dat ANDROID_JAR}"
KOTLINC="${KOTLINC:-kotlinc}"
GOI="vn.adc2026.wayfinding"
APP_ID="vn.boussolex.flowy"
MIN_SDK=24; TARGET_SDK=34; VCODE=1; VNAME="0.5"

rm -rf "$RA"; mkdir -p "$RA"/{gen,classes,dex}

echo "1/6  Tai nguyen (aapt)"
# Manifest nguon khong co package= (Gradle lay tu namespace) -> them vao ban tam.
sed "s|<manifest xmlns:android=\"http://schemas.android.com/apk/res/android\">|<manifest xmlns:android=\"http://schemas.android.com/apk/res/android\" package=\"$GOI\" android:versionCode=\"$VCODE\" android:versionName=\"$VNAME\">|" \
    "$APP/AndroidManifest.xml" > "$RA/AndroidManifest.xml"
aapt package -f -m \
    -M "$RA/AndroidManifest.xml" -S "$APP/res" -A "$APP/assets" \
    -I "$ANDROID_JAR" -J "$RA/gen" \
    --min-sdk-version $MIN_SDK --target-sdk-version $TARGET_SDK \
    --rename-manifest-package "$APP_ID" \
    --no-version-vectors \
    -F "$RA/tai-nguyen.apk"

echo "2/6  R.java"
javac -nowarn -encoding UTF-8 --release 8 -cp "$ANDROID_JAR" -d "$RA/classes" \
    $(find "$RA/gen" -name '*.java')

echo "3/6  Kotlin"
JAVA_OPTS="${JAVA_OPTS:--Xmx2g}" "$KOTLINC" -nowarn -jvm-target 1.8 -Xlambdas=class -Xsam-conversions=class \
    -cp "$ANDROID_JAR:$RA/classes" -d "$RA/classes" \
    "$APP"/java/vn/adc2026/wayfinding/*.kt "$FRONT"/vn/adc2026/frontend/*.kt

echo "4/6  Thu gon Kotlin stdlib (ProGuard, chi shrink)"
# kotlin-stdlib con vai ham dung invokedynamic (vd compareBy(vararg)). Gradle
# dung D8 tu "desugar"; dx thi khong. ProGuard bo cac ham app KHONG goi toi
# -> dx khong con gap chung. Khong doi ten, khong toi uu: stack trace van doc duoc.
STDLIB="$(dirname "$(readlink -f "$KOTLINC")")/../lib/kotlin-stdlib.jar"
( cd "$RA/classes" && jar cf "$RA/app.jar" . )
cat > "$RA/proguard.pro" <<PRO
-injars $RA/app.jar
-injars $STDLIB(!META-INF/**,!**module-info.class)
-outjars $RA/gon.jar
-libraryjars $ANDROID_JAR
-dontobfuscate
-dontoptimize
-dontpreverify
-dontwarn **
-ignorewarnings
-keep class vn.adc2026.** { *; }
PRO
proguard @"$RA/proguard.pro" > "$RA/proguard.log" 2>&1 || { tail -20 "$RA/proguard.log"; exit 1; }

echo "5/6  DEX"
dalvik-exchange --dex --min-sdk-version=$MIN_SDK --output="$RA/dex/classes.dex" "$RA/gon.jar"

echo "6/6  Dong goi, can le, ky"
cp "$RA/tai-nguyen.apk" "$RA/chua-ky.apk"
( cd "$RA/dex" && zip -q "$RA/chua-ky.apk" classes.dex )
zipalign -f -p 4 "$RA/chua-ky.apk" "$RA/can-le.apk"
KHOA="$RA/debug.keystore"
keytool -genkeypair -keystore "$KHOA" -storepass android -keypass android \
    -alias flowyx -keyalg RSA -keysize 2048 -validity 3650 \
    -dname "CN=FlowyX Debug,O=ADC 2026,C=VN" >/dev/null 2>&1
apksigner sign --ks "$KHOA" --ks-pass pass:android --key-pass pass:android \
    --min-sdk-version $MIN_SDK --out "$RA/flowyx-debug.apk" "$RA/can-le.apk"
apksigner verify "$RA/flowyx-debug.apk"
echo "XONG: $RA/flowyx-debug.apk ($(du -h "$RA/flowyx-debug.apk" | cut -f1))"
