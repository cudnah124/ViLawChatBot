// Giao diện gọi API backend và hiển thị phản hồi dạng stream
const chatbox = document.getElementById('chatbox');
const form = document.getElementById('chat-form');
const input = document.getElementById('user-input');

form.onsubmit = async function(e) {
    e.preventDefault();
    const msg = input.value.trim();
    if (!msg) return;
    chatbox.innerHTML += `<div><b>Bạn:</b> ${msg}</div>`;
    input.value = '';

    // Hiển thị đang gửi...
    const botDiv = document.createElement('div');
    botDiv.innerHTML = '<b>Vilaw:</b> <span id="vilaw-stream"></span>';
    chatbox.appendChild(botDiv);
    const streamSpan = botDiv.querySelector('#vilaw-stream');

    // Gọi API backend (stream)
    try {
        const response = await fetch('http://localhost:8000/api/v1/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: msg })
        });
        if (!response.body) throw new Error('No stream');
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let done = false;
        while (!done) {
            const { value, done: doneReading } = await reader.read();
            done = doneReading;
            if (value) {
                streamSpan.innerHTML += decoder.decode(value, { stream: true });
                chatbox.scrollTop = chatbox.scrollHeight;
            }
        }
    } catch (err) {
        streamSpan.innerHTML = '<span style="color:red">Lỗi kết nối backend!</span>';
    }
};
