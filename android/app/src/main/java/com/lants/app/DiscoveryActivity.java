package com.lants.app;

import android.content.Context;
import android.net.nsd.NsdManager;
import android.net.nsd.NsdServiceInfo;
import android.os.Bundle;
import android.os.Handler;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.ListView;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

import java.util.ArrayList;
import java.util.List;

public class DiscoveryActivity extends AppCompatActivity {

    private NsdManager nsdManager;
    private NsdManager.DiscoveryListener discoveryListener;
    private final List<ServerInfo> serverList = new ArrayList<>();
    private ArrayAdapter<ServerInfo> adapter;
    private TextView statusText;
    private boolean discovering = false;

    static class ServerInfo {
        String name;
        String host;
        int port;

        ServerInfo(String name, String host, int port) {
            this.name = name;
            this.host = host;
            this.port = port;
        }

        @Override
        public String toString() {
            return name + "\nhttp://" + host + ":" + port;
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_discovery);

        statusText = findViewById(R.id.discovery_status);
        ListView listView = findViewById(R.id.discovery_list);
        Button refreshBtn = findViewById(R.id.discovery_refresh);

        adapter = new ArrayAdapter<ServerInfo>(this, android.R.layout.simple_list_item_1, serverList) {
            @Override
            public View getView(int position, View convertView, ViewGroup parent) {
                TextView tv = (TextView) super.getView(position, convertView, parent);
                tv.setTextSize(14);
                return tv;
            }
        };
        listView.setAdapter(adapter);

        listView.setOnItemClickListener((parent, view, position, id) -> {
            ServerInfo server = serverList.get(position);
            String url = "http://" + server.host + ":" + server.port;
            ((MainActivity) getParent()).connectToServer(url);
            finish();
        });

        refreshBtn.setOnClickListener(v -> startDiscovery());
        nsdManager = (NsdManager) getSystemService(Context.NSD_SERVICE);
        startDiscovery();
    }

    private void startDiscovery() {
        if (discovering) return;
        discovering = true;
        serverList.clear();
        adapter.notifyDataSetChanged();
        statusText.setText("Scanning network for LANITS servers...");

        discoveryListener = new NsdManager.DiscoveryListener() {
            @Override
            public void onStartDiscoveryFailed(String serviceType, int errorCode) {
                discovering = false;
                runOnUiThread(() -> statusText.setText("Discovery failed (code " + errorCode + ")"));
            }

            @Override
            public void onStopDiscoveryFailed(String serviceType, int errorCode) {
                discovering = false;
            }

            @Override
            public void onDiscoveryStarted(String serviceType) {
                statusText.setText("Scanning...");
            }

            @Override
            public void onDiscoveryStopped(String serviceType) {
                discovering = false;
            }

            @Override
            public void onServiceFound(NsdServiceInfo serviceInfo) {
                nsdManager.resolveService(serviceInfo, new NsdManager.ResolveListener() {
                    @Override
                    public void onResolveFailed(NsdServiceInfo info, int err) {}

                    @Override
                    public void onServiceResolved(NsdServiceInfo info) {
                        String host = info.getHost().getHostAddress();
                        int port = info.getPort();
                        String name = info.getServiceName().replace("._lants._tcp.local.", "");
                        runOnUiThread(() -> {
                            ServerInfo si = new ServerInfo(name, host, port);
                            if (!serverList.contains(si)) {
                                serverList.add(si);
                                adapter.notifyDataSetChanged();
                            }
                            statusText.setText("Found " + serverList.size() + " server(s)");
                        });
                    }
                });
            }

            @Override
            public void onServiceLost(NsdServiceInfo serviceInfo) {
                runOnUiThread(() -> {
                    serverList.removeIf(s -> s.host.equals(serviceInfo.getHost().getHostAddress()));
                    adapter.notifyDataSetChanged();
                    statusText.setText("Found " + serverList.size() + " server(s)");
                });
            }
        };

        nsdManager.discoverServices("_lants._tcp", NsdManager.PROTOCOL_DNS_SD, discoveryListener);

        // Timeout after 8 seconds
        new Handler(getMainLooper()).postDelayed(() -> {
            if (discovering) {
                nsdManager.stopServiceDiscovery(discoveryListener);
                discovering = false;
                if (serverList.isEmpty()) {
                    statusText.setText("No servers found. Make sure LANITS is running on your PC.");
                }
            }
        }, 8000);
    }

    @Override
    protected void onDestroy() {
        if (discovering && discoveryListener != null) {
            try {
                nsdManager.stopServiceDiscovery(discoveryListener);
            } catch (Exception ignored) {}
        }
        super.onDestroy();
    }
}
