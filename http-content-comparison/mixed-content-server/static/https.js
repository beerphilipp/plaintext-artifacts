document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("script").textContent = "Script loaded over HTTP";
  console.log("JS loaded on", window.location.protocol);
});

