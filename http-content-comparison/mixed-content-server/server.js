const fs = require("fs");
const http = require("http");
const https = require("https");
const express = require("express");
const path = require("path");

const app = express();

app.get("/", (req, res) => {
  if (req.protocol === "https") {
    res.sendFile(path.join(__dirname, "index_https.html"));
  } else {
    res.sendFile(path.join(__dirname, "index_http.html"));
  }
});

app.get("/redir", (req, res) => {
  if (req.protocol === "https") {
    res.sendFile(path.join(__dirname, "empty_https.html"));
  } else {
    res.sendFile(path.join(__dirname, "empty_http.html"));
  }
});

// Route: same image path, different content depending on HTTP/HTTPS
app.get("/static/image.png", (req, res) => {
  if (req.protocol === "https") {
    res.sendFile(path.join(__dirname, "static", "https.png"));
  } else {
    res.sendFile(path.join(__dirname, "static", "http.png"));
  }
});

app.get("/static/image-small.png", (req, res) => {
  if (req.protocol === "https") {
    res.sendFile(path.join(__dirname, "static", "https-small.png"));
  } else {
    res.sendFile(path.join(__dirname, "static", "http-small.png"));
  }
});

app.get("/static/beacon", (req, res) => {
  console.log("Beacon received");
  res.sendStatus(200);
});

app.get("/static/audio.mp3", (req, res) => {
  if (req.protocol === "https") {
    res.sendFile(path.join(__dirname, "static", "https.mp3"));
  } else {
    res.sendFile(path.join(__dirname, "static", "http.mp3"));
  }
});

app.get("/static/video.mp4", (req, res) => {
  if (req.protocol === "https") {
    res.sendFile(path.join(__dirname, "static", "https.mp4"));
  } else {
    res.sendFile(path.join(__dirname, "static", "http.mp4"));
  }
});

app.get("/static/script.js", (req, res) => {
  if (req.protocol === "https") {
    res.sendFile(path.join(__dirname, "static", "https.js"));
  } else {
    res.sendFile(path.join(__dirname, "static", "http.js"));
  }
});

app.get("/static/style.css", (req, res) => {
  if (req.protocol === "https") {
    res.sendFile(path.join(__dirname, "static", "https.css"));
  } else {
    res.sendFile(path.join(__dirname, "static", "http.css"));
  }
});

app.get("/static/text.txt", (req, res) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  if (req.protocol === "https") {
    res.sendFile(path.join(__dirname, "static", "https.txt"));
  } else {
    res.sendFile(path.join(__dirname, "static", "http.txt"));
  }
});

app.get("/static/font.woff2", (req, res) => {
  // serve the file
  res.setHeader("Access-Control-Allow-Origin", "*");
  if (req.protocol === "https") {
    res.sendFile(path.join(__dirname, "static", "https.woff2"));
  } else {
    res.sendFile(path.join(__dirname, "static", "http.woff2"));
  }
});

// SSL certs
const options = {
  key: fs.readFileSync("key.pem"),
  cert: fs.readFileSync("cert.pem"),
};

// HTTP server
http.createServer(app).listen(80, () => {
  console.log("HTTP server on http://localhost:80");
});

// HTTPS server
https.createServer(options, app).listen(443, () => {
  console.log("HTTPS server on https://localhost:443");
});
