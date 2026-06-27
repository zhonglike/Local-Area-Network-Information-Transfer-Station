package com.lants.app;

import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.view.KeyEvent;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.webkit.WebViewAssetLoader;

import com.google.android.material.dialog.MaterialAlertDialogBuilder;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;

public class MainActivity extends AppCompatActivity {

    private WebView webView;
    private SharedPreferences prefs;
    private ClipboardManager clipboardManager;
    private String serverUrl = "http://192.168.1.100:9527";
    private ValueCallback<Uri[]> filePathCallback;
    private static final int FILE_CHOOSER_REQUEST = 1001;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        prefs = getSharedPreferences("lanits", MODE_PRIVATE);
        serverUrl = prefs.getString("server_url", serverUrl);

        clipboardManager = (ClipboardManager) getSystemService(CLIPBOARD_SERVICE);

        webView = findViewById(R.id.webview);
        setupWebView();

        handleShareIntent(getIntent());
    }

    private void setupWebView() {
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return false;
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                // Restore clipboard service if needed
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView wv, ValueCallback<Uri[]> cb, FileChooserParams params) {
                filePathCallback = cb;
                Intent intent = params.createIntent();
                intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true);
                startActivityForResult(intent, FILE_CHOOSER_REQUEST);
                return true;
            }
        });

        webView.addJavascriptInterface(new JsBridge(), "LANITS");

        loadServerUrl();
    }

    private void loadServerUrl() {
        String url = prefs.getString("server_url", serverUrl);
        webView.loadUrl(url);
    }

    public void connectToServer(String url) {
        serverUrl = url;
        prefs.edit().putString("server_url", url).apply();
        webView.loadUrl(url);
    }

    // ── Clipboard Monitor ──
    private void startClipboardMonitor() {
        clipboardManager.addPrimaryClipChangedListener(clipListener);
    }

    private final ClipboardManager.OnPrimaryClipChangedListener clipListener = () -> {
        ClipData clip = clipboardManager.getPrimaryClip();
        if (clip != null && clip.getItemCount() > 0) {
            ClipData.Item item = clip.getItemAt(0);
            CharSequence text = item.getText();
            if (text != null) {
                sendClipboardToServer(text.toString());
            }
        }
    };

    private void sendClipboardToServer(final String text) {
        new Thread(() -> {
            try {
                java.net.URL url = new java.net.URL(serverUrl + "/api/clipboard");
                java.net.HttpURLConnection conn = (java.net.HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setDoOutput(true);
                String json = "{\"type\":\"text\",\"content\":" + org.json.JSONObject.quote(text) + ",\"expire_hours\":24}";
                conn.getOutputStream().write(json.getBytes("UTF-8"));
                conn.getResponseCode();
                conn.disconnect();
            } catch (Exception ignored) {}
        }).start();
    }

    // ── Share Receive ──
    private void handleShareIntent(Intent intent) {
        if (intent == null || !Intent.ACTION_SEND.equals(intent.getAction())) return;

        String type = intent.getType();
        if (type == null) return;

        if ("text/plain".equals(type)) {
            String sharedText = intent.getStringExtra(Intent.EXTRA_TEXT);
            if (sharedText != null) {
                webView.evaluateJavascript(
                    "document.getElementById('textInput').value = " + org.json.JSONObject.quote(sharedText) + "; sendText();", null);
            }
        } else if (type.startsWith("image/") || type.startsWith("application/")) {
            Uri uri = intent.getParcelableExtra(Intent.EXTRA_STREAM);
            if (uri != null) uploadFile(uri);
        }
    }

    private void uploadFile(final Uri uri) {
        new Thread(() -> {
            try {
                InputStream is = getContentResolver().openInputStream(uri);
                if (is == null) return;

                String fileName = "shared_file";
                String mimeType = getContentResolver().getType(uri);
                java.io.File tempFile = new java.io.File(getCacheDir(), fileName);
                FileOutputStream fos = new FileOutputStream(tempFile);
                byte[] buf = new byte[8192];
                int len;
                while ((len = is.read(buf)) > 0) fos.write(buf, 0, len);
                fos.close(); is.close();

                java.net.URL url = new java.net.URL(serverUrl + "/api/upload");
                java.net.HttpURLConnection conn = (java.net.HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setDoOutput(true);
                conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=----BOUNDARY");
                java.io.OutputStream os = conn.getOutputStream();
                os.write(("------BOUNDARY\r\nContent-Disposition: form-data; name=\"file\"; filename=\"" + fileName + "\"\r\nContent-Type: " + mimeType + "\r\n\r\n").getBytes());
                java.io.FileInputStream fis = new java.io.FileInputStream(tempFile);
                byte[] buf2 = new byte[8192];
                int len2;
                while ((len2 = fis.read(buf2)) > 0) os.write(buf2, 0, len2);
                fis.close();
                os.write("\r\n------BOUNDARY--\r\n".getBytes());
                os.flush(); os.close();
                conn.getResponseCode();
                conn.disconnect();
                tempFile.delete();
                runOnUiThread(() -> Toast.makeText(this, "File uploaded", Toast.LENGTH_SHORT).show());
            } catch (Exception e) {
                runOnUiThread(() -> Toast.makeText(this, "Upload failed: " + e.getMessage(), Toast.LENGTH_SHORT).show());
            }
        }).start();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == FILE_CHOOSER_REQUEST) {
            if (filePathCallback != null) {
                Uri[] results = null;
                if (resultCode == RESULT_OK) {
                    if (data != null) {
                        String dataString = data.getDataString();
                        if (dataString != null) {
                            results = new Uri[]{Uri.parse(dataString)};
                        } else if (data.getClipData() != null) {
                            int count = data.getClipData().getItemCount();
                            results = new Uri[count];
                            for (int i = 0; i < count; i++)
                                results[i] = data.getClipData().getItemAt(i).getUri();
                        }
                    }
                }
                filePathCallback.onReceiveValue(results);
                filePathCallback = null;
            }
        }
        super.onActivityResult(requestCode, resultCode, data);
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK && webView.canGoBack()) {
            webView.goBack();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    // ── JS Bridge ──
    public class JsBridge {
        @JavascriptInterface
        public void copyToClipboard(String text) {
            ClipData clip = ClipData.newPlainText("LANITS", text);
            clipboardManager.setPrimaryClip(clip);
        }

        @JavascriptInterface
        public String getServerUrl() {
            return serverUrl;
        }

        @JavascriptInterface
        public void showDiscovery() {
            Intent intent = new Intent(MainActivity.this, DiscoveryActivity.class);
            startActivity(intent);
        }

        @JavascriptInterface
        public void toast(String msg) {
            runOnUiThread(() -> Toast.makeText(MainActivity.this, msg, Toast.LENGTH_SHORT).show());
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        startClipboardMonitor();
    }

    @Override
    protected void onPause() {
        super.onPause();
        clipboardManager.removePrimaryClipChangedListener(clipListener);
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        handleShareIntent(intent);
    }
}
