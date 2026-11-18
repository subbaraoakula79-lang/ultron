import os
import sys
import subprocess
import shutil
import zipfile
from pathlib import Path

# Paths
SDK_DIR = Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk"
BUILD_TOOLS = SDK_DIR / "build-tools" / "36.0.0"
PLATFORM_JAR = SDK_DIR / "platforms" / "android-36" / "android.jar"

AAPT2 = BUILD_TOOLS / "aapt2.exe"
D8 = BUILD_TOOLS / "d8.bat"
ZIPALIGN = BUILD_TOOLS / "zipalign.exe"
APKSIGNER = BUILD_TOOLS / "apksigner.bat"

JDK_BIN = Path(r"C:\Program Files\Java\jdk-26.0.2.1\bin")
KEYTOOL = JDK_BIN / "keytool.exe"
JAVAC = Path(r"C:\Program Files\Common Files\Oracle\Java\javapath\javac.exe")

PROJECT_DIR = Path("mobile_app").resolve()
BUILD_DIR = PROJECT_DIR / "build"
KEYSTORE = BUILD_DIR / "debug.keystore"

def run_cmd(cmd, desc):
    print(f"[BUILD] {desc}...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[!] Error in {desc}:")
        print(res.stderr or res.stdout)
        sys.exit(1)
    return res

def build_apk():
    print("=" * 60)
    print("      BUILDING ULTRON MOBILE NODE (ANDROID APK)")
    print("=" * 60)

    # 1. Clean & create build dir
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True)
    classes_dir = BUILD_DIR / "classes"
    classes_dir.mkdir()

    # 2. Compile resources
    res_zip = BUILD_DIR / "res.zip"
    run_cmd([
        str(AAPT2), "compile",
        "--dir", str(PROJECT_DIR / "res"),
        "-o", str(res_zip)
    ], "Compiling Android resources")

    # 3. Link resources and generate R.java
    unaligned_apk = BUILD_DIR / "unaligned.apk"
    run_cmd([
        str(AAPT2), "link",
        "-o", str(unaligned_apk),
        "-I", str(PLATFORM_JAR),
        "--manifest", str(PROJECT_DIR / "AndroidManifest.xml"),
        "--java", str(PROJECT_DIR / "src"),
        "--auto-add-overlay",
        str(res_zip)
    ], "Linking package and generating R.java")

    # 4. Compile Java sources
    java_files = list((PROJECT_DIR / "src" / "org" / "ultron" / "node").glob("*.java"))
    run_cmd([
        str(JAVAC),
        "-source", "17",
        "-target", "17",
        "-cp", str(PLATFORM_JAR),
        "-d", str(classes_dir),
        *[str(f) for f in java_files]
    ], "Compiling Java sources to bytecode")

    # 5. Dex with d8
    class_files = list(classes_dir.rglob("*.class"))
    run_cmd([
        str(D8),
        *[str(f) for f in class_files],
        "--lib", str(PLATFORM_JAR),
        "--output", str(BUILD_DIR)
    ], "Translating bytecode to classes.dex")

    # 6. Add classes.dex into unaligned.apk
    dex_file = BUILD_DIR / "classes.dex"
    print("[BUILD] Packaging classes.dex into APK container...")
    with zipfile.ZipFile(unaligned_apk, "a") as apk:
        apk.write(dex_file, "classes.dex")

    # 7. Zipalign APK
    aligned_apk = BUILD_DIR / "aligned.apk"
    run_cmd([
        str(ZIPALIGN),
        "-f", "-p", "4",
        str(unaligned_apk),
        str(aligned_apk)
    ], "Aligning APK 4-byte boundaries")

    # 8. Create debug keystore if missing
    if not KEYSTORE.exists():
        run_cmd([
            str(KEYTOOL), "-genkeypair",
            "-keystore", str(KEYSTORE),
            "-storepass", "android",
            "-alias", "androiddebugkey",
            "-keypass", "android",
            "-keyalg", "RSA",
            "-keysize", "2048",
            "-validity", "10000",
            "-dname", "CN=UltronDebug,O=Ultron,C=US"
        ], "Generating debug keystore")

    # 9. Sign APK with apksigner
    final_apk = Path("ultron_mobile.apk").resolve()
    run_cmd([
        str(APKSIGNER), "sign",
        "--ks", str(KEYSTORE),
        "--ks-pass", "pass:android",
        "--ks-key-alias", "androiddebugkey",
        "--key-pass", "pass:android",
        "--out", str(final_apk),
        str(aligned_apk)
    ], "Signing APK with apksigner")

    # Copy to hud directory for instant web download
    hud_apk = Path("ultron") / "hud" / "ultron_mobile.apk"
    shutil.copy2(final_apk, hud_apk)

    apk_size_kb = round(final_apk.stat().st_size / 1024, 2)
    print("\n" + "=" * 60)
    print(f" SUCCESS: Ultron Mobile APK Generated!")
    print(f" Output Location: {final_apk} ({apk_size_kb} KB)")
    print(f" Hosted at: http://10.157.202.87:8080/ultron_mobile.apk")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    build_apk()
