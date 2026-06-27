package com.lants.app;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;
import android.os.IBinder;
import android.util.Log;

import androidx.core.app.NotificationCompat;

import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

public class ClipboardSyncService extends Service {

    private static final String CHANNEL_ID = "lanits_clipboard";
    private static final int NOTIF_ID = 1001;
    private ClipboardManager clipboardManager;
    private SharedPreferences prefs;
    private String lastContent = "";

    private final ClipboardManager.OnPrimaryClipChangedListener listener = () -> {
        ClipData clip = clipboardManager.getPrimaryClip();
        if (clip == null || clip.getItemCount() == 0) return;

        CharSequence text = clip.getItemAt(0).getText();
        if (text == null || text.toString().equals(lastContent)) return;

        lastContent = text.toString();
        sendToServer(lastContent);
    };

    private void sendToServer(final String text) {
        final String serverUrl = prefs.getString("server_url", "http://192.168.1.100:9527");
        new Thread(() -> {
            try {
                URL url = new URL(serverUrl + "/api/clipboard");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setDoOutput(true);
                String json = "{\"type\":\"text\",\"content\":" +
                    org.json.JSONObject.quote(text) + ",\"expire_hours\":24}";
                OutputStream os = conn.getOutputStream();
                os.write(json.getBytes("UTF-8"));
                os.flush(); os.close();
                conn.getResponseCode();
                conn.disconnect();
            } catch (Exception ignored) {}
        }).start();
    }

    @Override
    public void onCreate() {
        super.onCreate();
        prefs = getSharedPreferences("lanits", MODE_PRIVATE);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID, "LANITS Clipboard Sync",
                NotificationManager.IMPORTANCE_LOW);
            ((NotificationManager) getSystemService(NOTIFICATION_SERVICE))
                .createNotificationChannel(channel);
        }

        Notification notification = new NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("LANITS")
            .setContentText("Clipboard sync active")
            .setSmallIcon(android.R.drawable.ic_menu_share)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build();

        startForeground(NOTIF_ID, notification);

        clipboardManager = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        clipboardManager.addPrimaryClipChangedListener(listener);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        if (clipboardManager != null) {
            clipboardManager.removePrimaryClipChangedListener(listener);
        }
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
