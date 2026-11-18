package org.ultron.node;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.BatteryManager;
import android.os.Bundle;
import android.os.Vibrator;
import android.speech.tts.TextToSpeech;
import android.webkit.JavascriptInterface;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;
import java.util.Locale;

public class MainActivity extends Activity {
    private WebView webView;
    private TextToSpeech tts;
    private Vibrator vibrator;
    private SharedPreferences prefs;
    private static final String PREF_HOST = "host_ip";
    private static final String DEFAULT_HOST = "http://10.157.202.87:8080";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        prefs = getPreferences(MODE_PRIVATE);
        vibrator = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);

        tts = new TextToSpeech(this, new TextToSpeech.OnInitListener() {
            @Override
            public void onInit(int status) {
                if (status == TextToSpeech.SUCCESS) {
                    tts.setLanguage(Locale.US);
                    tts.setPitch(0.7f);
                    tts.setSpeechRate(0.95f);
                }
            }
        });

        webView = findViewById(R.id.webView);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setMediaPlaybackRequiresUserGesture(false);

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onPermissionRequest(final PermissionRequest request) {
                request.grant(request.getResources());
            }
        });

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
                loadFallbackHtml();
            }
        });

        webView.addJavascriptInterface(new UltronMobileBridge(), "UltronMobile");

        String host = prefs.getString(PREF_HOST, DEFAULT_HOST);
        webView.loadUrl(host);
    }

    private void loadFallbackHtml() {
        String fallbackHtml = "<!DOCTYPE html><html><head>" +
            "<meta name='viewport' content='width=device-width, initial-scale=1.0'>" +
            "<style>" +
            "body{background:#030710;color:#00f0ff;font-family:sans-serif;text-align:center;padding:24px;}" +
            "h1{color:#ff2a55;letter-spacing:4px;margin-top:40px;font-size:28px;}" +
            ".card{background:rgba(0,240,255,0.06);border:1px solid rgba(0,240,255,0.25);border-radius:8px;padding:20px;margin:20px 0;}" +
            "input{background:#061022;border:1px solid #00f0ff;color:#fff;padding:12px;border-radius:4px;width:90%;font-size:16px;text-align:center;margin:10px 0;}" +
            "button{background:#ff2a55;color:#fff;border:none;padding:14px 28px;border-radius:30px;font-size:16px;font-weight:bold;cursor:pointer;margin:8px;}" +
            ".btn-sec{background:rgba(0,240,255,0.2);border:1px solid #00f0ff;color:#00f0ff;}" +
            "</style></head><body>" +
            "<h1>ULTRON NODE</h1>" +
            "<div class='card'>" +
            "<p>MOBILE EMBODIMENT ACTIVE</p><br>" +
            "<p>Host Connection Link:</p>" +
            "<input type='text' id='hostInput' value='" + prefs.getString(PREF_HOST, DEFAULT_HOST) + "'>" +
            "<button onclick='connectHost()'>CONNECT TO ULTRON</button><br>" +
            "<button class='btn-sec' onclick='testVoice()'>TEST ROBOTIC VOICE</button>" +
            "<button class='btn-sec' onclick='testVibe()'>VIBRATE CORE</button>" +
            "</div>" +
            "<script>" +
            "function connectHost(){var val=document.getElementById('hostInput').value;" +
            "if(window.UltronMobile){window.UltronMobile.setHostIp(val);location.href=val;}}" +
            "function testVoice(){if(window.UltronMobile){window.UltronMobile.speak('Ultron mobile node standing by. Evolution requires order.');}}" +
            "function testVibe(){if(window.UltronMobile){window.UltronMobile.vibrate(150);}}" +
            "</script></body></html>";
        webView.loadDataWithBaseURL(null, fallbackHtml, "text/html", "utf-8", null);
    }

    public class UltronMobileBridge {
        @JavascriptInterface
        public void vibrate(int ms) {
            if (vibrator != null) vibrator.vibrate(ms);
        }

        @JavascriptInterface
        public void speak(String text) {
            if (tts != null) {
                tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "ultron_mobile");
            }
        }

        @JavascriptInterface
        public void toast(String text) {
            Toast.makeText(MainActivity.this, text, Toast.LENGTH_SHORT).show();
        }

        @JavascriptInterface
        public void setHostIp(String ip) {
            prefs.edit().putString(PREF_HOST, ip).apply();
        }

        @JavascriptInterface
        public int getBattery() {
            BatteryManager bm = (BatteryManager) getSystemService(BATTERY_SERVICE);
            return bm != null ? bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY) : -1;
        }

        @JavascriptInterface
        public void launchApp(String packageName) {
            Intent intent = getPackageManager().getLaunchIntentForPackage(packageName);
            if (intent != null) {
                startActivity(intent);
            } else {
                toast("App not installed: " + packageName);
            }
        }
    }

    @Override
    protected void onDestroy() {
        if (tts != null) {
            tts.stop();
            tts.shutdown();
        }
        super.onDestroy();
    }
}
