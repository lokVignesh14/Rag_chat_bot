const WS_URL = (location.hostname === "localhost" || location.hostname === "127.0.0.1")
  ? "ws://127.0.0.1:8000/ws" : "wss://YOUR_DOMAIN/ws";

const btn = document.getElementById("krp-chat-btn");
const panel = document.getElementById("krp-chat-panel");
const stream = document.getElementById("chat-stream");
const q = document.getElementById("q");
const send = document.getElementById("send");
const mic = document.getElementById("mic");

let ws;

btn.onclick = () => {
  panel.style.display = panel.style.display === "flex" ? "none" : "flex";
  panel.style.flexDirection = "column";
  if (!ws || ws.readyState !== 1) {
    ws = new WebSocket(WS_URL);
    ws.onmessage = (evt) => {
      const msg = JSON.parse(evt.data);
      if (msg.type === "chunk") appendBotText(msg.data);
      if (msg.type === "images") appendImages(msg.data);
      if (msg.type === "done") appendDivider();
    };
  }
};

send.onclick = () => {
  if (!q.value.trim()) return;
  appendMe(q.value);
  ws.send(JSON.stringify({text:q.value}));
  q.value = "";
};

function appendMe(t){const d=document.createElement("div");d.className="bubble me";d.textContent=t;stream.appendChild(d);stream.scrollTop=stream.scrollHeight;}
function appendBotText(t){let last=stream.lastElementChild;if(!last || !last.classList.contains("bubble") || last.classList.contains("me")){last=document.createElement("div");last.className="bubble";last.textContent="";stream.appendChild(last);}last.textContent+=t;stream.scrollTop=stream.scrollHeight;}
function appendImages(urls){const wrap=document.createElement("div");wrap.className="images";urls.slice(0,4).forEach(u=>{const im=document.createElement("img");im.src=u;wrap.appendChild(im)});stream.appendChild(wrap);stream.scrollTop=stream.scrollHeight;}
function appendDivider(){const d=document.createElement("div");d.style.height="4px";stream.appendChild(d);}

//// Voice capture -> /stt
let mediaRecorder, chunks=[];
mic.onclick = async () => {
  if (!mediaRecorder || mediaRecorder.state==="inactive"){
    const streamAudio = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(streamAudio);
    chunks=[];
    mediaRecorder.ondataavailable = e => chunks.push(e.data);
    mediaRecorder.onstop = async () => {
      const blob = new Blob(chunks, { type: "audio/webm" });
      const fd = new FormData();
      fd.append("file", blob, "voice.webm");
      const base = (location.hostname==="localhost"||location.hostname==="127.0.0.1")? "http://127.0.0.1:8000": "";
      const res = await fetch(base + "/stt", { method:"POST", body: fd });
      const js = await res.json();
      q.value = js.text || "";
      if (q.value) send.click();
    };
    mediaRecorder.start();
    mic.textContent = "🛑";
  } else {
    mediaRecorder.stop();
    mic.textContent = "🎙️";
  }
};
