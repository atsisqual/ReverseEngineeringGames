const rows = document.querySelector("#results");

function add(name, ok, notes = "") {
  const tr = document.createElement("tr");
  const status = ok ? "yes" : "no";
  tr.innerHTML = `<td>${name}</td><td class="${ok ? "ok" : ""}">${status}</td><td>${notes}</td>`;
  rows.appendChild(tr);
}

add("WebAssembly", typeof WebAssembly === "object");
add("WebGL2", !!document.createElement("canvas").getContext("webgl2"));
add("WebGPU", "gpu" in navigator, "Optional high-end renderer");
add("Gamepad API", "getGamepads" in navigator);
add("WebAudio", "AudioContext" in globalThis || "webkitAudioContext" in globalThis);
add("SharedArrayBuffer", typeof SharedArrayBuffer !== "undefined", "Needed by common pthread/Wasm-thread configurations");
add("Cross-origin isolated", globalThis.crossOriginIsolated === true, "Required for SharedArrayBuffer in normal deployments");
add("OPFS", !!navigator.storage?.getDirectory, "Persistent filesystem option");
add("WebTransport", "WebTransport" in globalThis, "Optional networking transport");
add("WebRTC", "RTCPeerConnection" in globalThis);

document.querySelector("#isolation").innerHTML =
  globalThis.crossOriginIsolated
    ? "Cross-origin isolation is active."
    : "For pthreads, serve with <code>Cross-Origin-Opener-Policy: same-origin</code> and <code>Cross-Origin-Embedder-Policy: require-corp</code>.";
