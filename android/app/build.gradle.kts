plugins {
    id("com.android.application")
}

android {
    namespace = "com.lants.app"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.lants.app"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"))
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_1_8
        targetCompatibility = JavaVersion.VERSION_1_8
    }
}

dependencies {
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("androidx.webkit:webkit:1.9.0")
    implementation("com.google.android.material:material:1.11.0")
    implementation("com.google.zxing:core:3.5.2")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
}
