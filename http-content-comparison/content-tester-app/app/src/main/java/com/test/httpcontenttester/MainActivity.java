package com.test.httpcontenttester;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;
import android.webkit.WebSettings;
import android.webkit.WebView;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

import java.net.URI;
import java.net.URL;

public class MainActivity extends AppCompatActivity {

    String websiteString = "<!DOCTYPE html>\n" +
            "<html>\n" +
            "<head>\n" +
            "  <title>loadData Page</title>\n" +
            "  <script src=\"http://mixed-content.test/static/script.js\"></script>\n" +
            "  <link rel=\"stylesheet\" href=\"http://mixed-content.test/static/style.css\">\n" +
            "  <!-- base url-->\n" +
            "   <base href=\"http://mixed-content.test/\">\n" +
            "</head>\n" +
            "<body>\n" +
            "  <h1>Served over loadData</h1>\n" +
            "\n" +
            "  <h1>Secure origin</h1>\n" +
            "  <p>This page is served over loadData.</p>\n" +
            "  <script>\n" +
            "    // check if secure context\n" +
            "    if (window.isSecureContext) {\n" +
            "      document.write(\"<p>This is a secure context.</p>\");\n" +
            "    } else {\n" +
            "      document.write(\"<p>This is NOT a secure context.</p>\");\n" +
            "    }\n" +
            "    // write the origin here\n" +
            "    document.write(\"<p>Origin: \" + window.location.origin + \"</p>\");\n" +
            "  </script>\n" +
            "\n" +
            "  <h1>Upgradable Content</h1>\n" +
            "\n" +
            "  <h2>Image src</h2>\n" +
            "  <img src=\"/static/image.png\" alt=\"HTTPS image\">\n" +
            "  <p>If you see HTTP, it is served over HTTP</p>\n" +
            "\n" +
            "  <!-- CSS Images -->\n" +
            "\n" +
            "  <h2>Video src</h2>\n" +
            "  <video src=\"/static/video.mp4\" controls>\n" +
            "    Your browser does not support the video tag.\n" +
            "  </video>\n" +
            "  <p>If you see the earth, it is served over HTTP</p>\n" +
            "  \n" +
            "  <h2>Audio src</h2>\n" +
            "  <audio src=\"/static/audio.mp3\" controls>\n" +
            "    Your browser does not support the audio element.\n" +
            "  </audio>\n" +
            "  <p>If you hear a Miaow, it is served over HTTP</p>\n" +
            "\n" +
            "  <h2>Audio source</h2>\n" +
            "  <audio controls>\n" +
            "    <source src=\"/static/audio.mp3\" type=\"audio/mpeg\">\n" +
            "    Your browser does not support the audio element.\n" +
            "  </audio>\n" +
            "  <p>If you hear a Miaow, it is served over HTTP</p>\n" +
            "  \n" +
            "\n" +
            "  <h2>Video source</h2>\n" +
            "  <video controls>\n" +
            "    <source src=\"/static/video.mp4\">\n" +
            "    Your browser does not support the video tag.\n" +
            "  </video>\n" +
            "  <p>If you see the earth, it is served over HTTP</p>\n" +
            "\n" +
            "  <hr>\n" +
            "\n" +
            "  <h1>Blockable Content</h1>\n" +
            "\n" +
            "  <h2>Script src</h2>\n" +
            "\n" +
            "  <p id=\"script\">No script was loaded</p>\n" +
            "\n" +
            "  <h2>Link href stylesheet</h2>\n" +
            "\n" +
            "  <p id=\"style\">If this is red, it is served over HTTP. If it is green, it is served over HTTPS. If it is black, it is blocked.</p>\n" +
            "\n" +
            "\n" +
            "\n" +
            "  <h2>iframe src</h2>\n" +
            "\n" +
            "  <iframe src=\"http://mixed-content.test/redir\" width=\"600\" height=\"400\"></iframe>\n" +
            "  <p>If you see 'served over HTTP' in the iframe, it is served over HTTP. If you see 'served over HTTPS', it is served over HTTPS. Otherwise, it is blocked.</p>\n" +
            "  \n" +
            "  \n" +
            "  \n" +
            "  <!-- fetch request -->\n" +
            "\n" +
            "  <h2>Fetch</h2>\n" +
            "   <p id=\"fetch\">No fetch result yet</p>\n" +
            "   <script>\n" +
            "    fetch(\"/static/text.txt\")\n" +
            "      .then(response => response.text())\n" +
            "      .then(data => {\n" +
            "        document.getElementById(\"fetch\").textContent = \n" +
            "          \"Fetch succeeded over: \" + data;\n" +
            "      })\n" +
            "      .catch(err => {\n" +
            "        document.getElementById(\"fetch\").textContent = \n" +
            "          \"Fetch blocked or failed: \" + err;\n" +
            "      });\n" +
            "  </script>\n" +
            "\n" +
            "\n" +
            "  <!-- XMLHttpRequest -->\n" +
            "   <h2>XMLHttpRequest</h2>\n" +
            "   <p id=\"xhr\">No XHR result yet</p>\n" +
            "  <script>\n" +
            "    var xhr = new XMLHttpRequest();\n" +
            "    xhr.open(\"GET\", \"/static/text.txt\", true);\n" +
            "    xhr.onload = function() {\n" +
            "      if (xhr.status === 200) {\n" +
            "        document.getElementById(\"xhr\").textContent =\n" +
            "          \"XHR succeeded over: \" + xhr.responseText;\n" +
            "      } else {\n" +
            "        document.getElementById(\"xhr\").textContent =\n" +
            "          \"XHR failed with status: \" + xhr.status;\n" +
            "      }\n" +
            "    };\n" +
            "    xhr.onerror = function() {\n" +
            "      document.getElementById(\"xhr\").textContent = \"XHR blocked or network error\";\n" +
            "    };\n" +
            "    xhr.send();\n" +
            "  </script>\n" +
            "\n" +
            "  <!-- CSS URL -->\n" +
            "   <h2>CSS URL background-image</h2>\n" +
            "  <div class=\"css-url-test\" style=\"width:200px; height:100px; border:1px solid black;\">\n" +
            "    CSS background test\n" +
            "  </div>\n" +
            "  <style>\n" +
            "    .css-url-test {\n" +
            "      background-image: url(\"/static/image.png\");\n" +
            "      background-size: contain;\n" +
            "      background-repeat: no-repeat;\n" +
            "      background-position: center;\n" +
            "    }\n" +
            "  </style>\n" +
            "  <p>If the box shows an HTTP image, it is served over HTTP. If it shows an HTTPS image, it is served over HTTPS. If it is blank, it is blocked.</p>\n" +
            "\n" +
            "    <h2>Object data attribute</h2>\n" +
            "  <object data=\"/redir\" width=\"400\" height=\"200\"></object>\n" +
            "  <p>If you see 'served over HTTP' in the iframe, it is served over HTTP. If you see 'served over HTTPS', it is served over HTTPS. Otherwise, it is blocked.</p>\n" +
            "\n" +
            "  <h2>Navigator sendBeacon url</h2>\n" +
            "  <p id=\"beacon\">Beacon not sent yet</p>\n" +
            "  <script>\n" +
            "    let beaconData = new Blob([\"Beacon test data\"], { type: \"text/plain\" });\n" +
            "    let sent = navigator.sendBeacon(\"static/beacon\", beaconData);\n" +
            "    document.getElementById(\"beacon\").textContent = sent\n" +
            "      ? \"Beacon send attempted over HTTP\"\n" +
            "      : \"Beacon send failed (blocked or not supported)\";\n" +
            "  </script>\n" +
            "\n" +
            "  <h2>Image srcset</h2>\n" +
            "  <img \n" +
            "    src=\"/static/image.png\"\n" +
            "    srcset=\"\n" +
            "      /static/image-small.png 300w\n" +
            "    \"\n" +
            "    sizes=\"(max-width: 600px) 300px\"\n" +
            "    alt=\"HTTP srcset test\">\n" +
            "  <p>If the image displays red, one of the srcset candidates was loaded over HTTP. If it displays green, it was loaded over HTTPS. If it is blank, it was blocked.</p>\n" +
            "\n" +
            "  <h2>Web font</h2>\n" +
            "  <style>\n" +
            "    @font-face {\n" +
            "    font-family: 'CustomFont';\n" +
            "    font-style: italic;\n" +
            "    font-weight: 300;\n" +
            "    font-display: swap;\n" +
            "    src: url(\"/static/font.woff2\") format('woff2');\n" +
            "    unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;\n" +
            "}\n" +
            "    .weeb-font {\n" +
            "      font-family: \"CustomFont\", sans-serif;\n" +
            "      font-size: 20px;\n" +
            "    }\n" +
            "  </style>\n" +
            "  <p class=\"web-font\">If you see Comic Sans, it was loaded over HTTP. If you see a colorful font, it was loaded over HTTPS. Otherwise, it was blocked</p>\n" +
            "  \n" +
            "\n" +
            "  <h1>Others</h1>\n" +
            "  <h2>Links to other pages</h2>\n" +
            "  <a href=\"/redir\">Link to other page</a>\n" +
            "</body>\n" +
            "</html>\n" +
            "\n";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_main);
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (v, insets) -> {
            Insets systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom);
            return insets;
        });

        WebView webView = findViewById(R.id.webView);

        webView.getSettings().setJavaScriptEnabled(true);

        // Mixed Content Mode setting
        String mcSetting = getIntent().getStringExtra("mc");
        Log.i("MCSetting", "Mixed Content Mode setting: " + mcSetting);
        if (mcSetting != null && mcSetting.equals("0")) {
            Log.i("MCSetting", "Setting Mixed Content Mode to ALWAYS_ALLOW");
            webView.getSettings().setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        } else if (mcSetting != null && mcSetting.equals("2")) {
            webView.getSettings().setMixedContentMode(android.webkit.WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE);
        } else if (mcSetting != null && mcSetting.equals("1")) {
            webView.getSettings().setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        }

        // Allow navigation?
        String allowNav = getIntent().getStringExtra("nav");
        if (allowNav != null && allowNav.equals("1")) {
            Log.i("AllowNav", "Enabling navigation within WebView");
            webView.setWebViewClient(new android.webkit.WebViewClient());
        }

        // Load URL
        String url = getIntent().getStringExtra("url");
        Log.i("LoadURL", "Loading URL: " + url);
        if (url != null) {
            webView.loadUrl(url);
        }

        // Load Data
        String data = getIntent().getStringExtra("data");
        if (data != null) {
            Log.i("LoadData", "Loading Data into WebView");
            webView.loadData(websiteString, "text/html", "UTF-8");
        }

        // Load Data With Base URL
        String dataBaseUrl = getIntent().getStringExtra("data_base_url");

        if (dataBaseUrl != null) {
            Log.i("LoadDataBaseURL", "Loading Data with Base URL into WebView");
            String realBaseUrl = null;
            if (dataBaseUrl.equals("null")) {
                realBaseUrl = null;
            } else {
                realBaseUrl = dataBaseUrl;
            }
            webView.loadDataWithBaseURL(realBaseUrl, websiteString, "text/html", "UTF-8", null);
        }

        String file = getIntent().getStringExtra("file");
        if (file != null && file.equals("1")) {
            Log.i("LoadFile", "Loading file into WebView: " + file);
            webView.loadUrl("file:///android_asset/index.html");
        }

        // get the WebView version
        String webViewVersion = android.webkit.WebView.getCurrentWebViewPackage().versionName;
        Log.i("WebViewVersion", "WebView Version: " + webViewVersion);
        setTitle("WebView Version: " + webViewVersion);

    }
}