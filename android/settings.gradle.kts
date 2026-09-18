pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "Flowy"
include(":app")

// Module giao dien nam NGOAI thu muc android/, ngang hang voi no.
// Gradle cho phep dieu nay bang cach chi ro projectDir.
include(":frontend")
project(":frontend").projectDir = file("../frontend")
