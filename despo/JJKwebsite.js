const SECURITY_TOKEN = 'JJK_SECURE_888';
const GAS_WEB_APP_URL = 'https://script.google.com/macros/s/AKfycbzDdDOHTXsUke8Hh5ZuKZeeP5mZimzlgssb_5KPMeYaqBrlKVjhtqSeCcFebZfyPYDMNA/exec';
const MAX_MESSAGE_LENGTH = 300;
const CHAT_COOLDOWN_MS = 1500;
const ALLOWED_EXTERNAL_HOSTS = new Set(['reurl.cc', 'ddc.ai', 'www.facebook.com', 'lin.ee']);
const AI_AVATAR_URL = 'https://formosachangcoltd.wpcomstaging.com/wp-content/uploads/2026/03/京簡康-公仔-AI完整檔-04.png';
const MSG_BLOCKED_LINK = 'External link blocked.';
const MSG_INVALID_LINK = 'Invalid external link.';
const MSG_WAIT = 'Please wait before sending another message.';
const MSG_SERVICE_DOWN = 'Service temporarily unavailable. Please try again.';
const MSG_NO_RESPONSE = 'No response received. Please try again.';

let chatRequestInFlight = false;
let lastChatRequestAt = 0;

const menuData = [
    { id: 1, name: "香魯牛腱餐盒", price: 170, desc: "精選十三香滷包，慢火燉煮牛腱，濃郁風味，層次分明。", img: "https://formosachangcoltd.wpcomstaging.com/wp-content/uploads/2026/03/香魯牛煎餐盒-去番茄.png" },
    { id: 2, name: "焙煎胡麻肉片餐盒", price: 115, desc: "嚴選日式焙煎胡麻醬，香味濃郁，搭配豬肉片。", img: "https://formosachangcoltd.wpcomstaging.com/wp-content/uploads/2026/03/焙煎胡麻肉片餐盒-去番茄.png" },
    { id: 3, name: "蔥鹽雞胸餐盒", price: 135, desc: "雙油淬煉紅蔥油與橄欖油黃金比例，搭配新鮮青蔥，爽脆蔥油香。", img: "https://formosachangcoltd.wpcomstaging.com/wp-content/uploads/2026/03/蔥鹽雞胸-外帶.jpg" },
    { id: 4, name: "烤檸檬鮭魚餐盒", price: 199, desc: "鮭魚肉含高蛋白質，蒸烤後皮酥肉嫩，外酥內軟。", img: "https://formosachangcoltd.wpcomstaging.com/wp-content/uploads/2026/03/烤檸檬鮭魚餐盒-去番茄.png" },
    { id: 5, name: "日式烤雞腿餐盒", price: 170, desc: "去骨雞腿刷上日式醬料，烤至金黃焦香，吮指美味。", img: "https://formosachangcoltd.wpcomstaging.com/wp-content/uploads/2026/03/日式烤雞腿餐盒-去番茄.png" },
    { id: 6, name: "烤雪霜肉餐盒", price: 160, desc: "雪霜肉油花均勻口感Q彈，撒上玫瑰鹽簡單原味。", img: "https://formosachangcoltd.wpcomstaging.com/wp-content/uploads/2026/03/烤雪霜肉餐盒-去番茄.png" },
    { id: 7, name: "香烤桔汁里肌餐盒", price: 145, desc: "上選里肌刷上獨家桔汁，蒸烤後清爽甜香。", img: "https://formosachangcoltd.wpcomstaging.com/wp-content/uploads/2026/03/香烤桔汁里肌餐盒-去番茄.png" },
    { id: 8, name: "烤挪威鯖魚餐盒", price: 145, desc: "挪威鯖魚油脂豐厚，鹹香細緻。高品質魚肉。", img: "https://formosachangcoltd.wpcomstaging.com/wp-content/uploads/2026/03/烤挪威鯖魚餐盒-去番茄.png" },
    { id: 9, name: "韓式泡菜雞胸餐盒", price: 135, desc: "低溫蒸煮雞胸搭配韓式泡菜，脆口清爽低負擔。", img: "https://formosachangcoltd.wpcomstaging.com/wp-content/uploads/2026/03/韓式泡菜雞胸餐盒-去番茄.png" },
    { id: 10, name: "壽喜燒豚肉片餐盒", price: 125, desc: "汆燙軟嫩豬肉片淋上日式壽喜燒醬。", img: "https://formosachangcoltd.wpcomstaging.com/wp-content/uploads/2026/03/壽喜燒豚肉片餐盒-去番茄.png" },
    { id: 11, name: "黑胡椒嫩雞胸餐盒", price: 135, desc: "新鮮雞胸以低溫蒸煮熟化，保留肉質鮮嫩。", img: "https://formosachangcoltd.wpcomstaging.com/wp-content/uploads/2026/03/黑胡椒嫩雞胸餐盒-去番茄.png" },
    { id: 12, name: "經典豬雞妙算餐盒", price: 135, desc: "胡麻豬肉片與黑胡椒香嫩雞胸雙饗組合。", img: "https://formosachangcoltd.wpcomstaging.com/wp-content/uploads/2026/03/經典豬雞妙算餐盒-去番茄.png" },
];

function showToast(message) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.className = 'show';
    window.setTimeout(() => {
        toast.className = '';
    }, 3000);
}

function setText(element, value) {
    element.textContent = value;
    return element;
}

function createElement(tagName, className, text) {
    const element = document.createElement(tagName);
    if (className) element.className = className;
    if (typeof text === 'string') element.textContent = text;
    return element;
}

function safeOpen(url) {
    try {
        const parsedUrl = new URL(url, window.location.href);
        if (parsedUrl.protocol !== 'https:' || !ALLOWED_EXTERNAL_HOSTS.has(parsedUrl.hostname)) {
            showToast(MSG_BLOCKED_LINK);
            return;
        }
        const newWindow = window.open(parsedUrl.toString(), '_blank', 'noopener,noreferrer');
        if (newWindow) newWindow.opener = null;
    } catch (_error) {
        showToast(MSG_INVALID_LINK);
    }
}

function openAIChat(show = true) {
    const chat = document.getElementById('aiChat');
    if (!chat) return;
    chat.classList.toggle('chat-active', show);
}

function toggleModal(show) {
    const modal = document.getElementById('storeModal');
    if (!modal) return;
    if (show) {
        modal.classList.remove('hidden');
        modal.classList.add('modal-active');
        return;
    }
    modal.classList.add('hidden');
    modal.classList.remove('modal-active');
}

function buildMealCard(meal) {
    const card = createElement('div', 'menu-card bg-white rounded-[3rem] overflow-hidden border border-slate-100 flex flex-col h-full shadow-sm relative group');

    const ttsButton = createElement('button', 'absolute top-5 right-5 bg-white/90 hover:bg-brand-orange hover:text-white text-brand-orange w-11 h-11 rounded-full flex items-center justify-center shadow-lg z-10 transition-all active:scale-90', 'TTS');
    ttsButton.type = 'button';
    ttsButton.setAttribute('aria-label', `播放${meal.name}語音介紹`);
    ttsButton.addEventListener('click', () => {
        void callGAS(ttsButton, 'tts', `${meal.name}?${meal.desc}`);
    });

    const imageContainer = createElement('div', 'h-64 bg-slate-50 flex items-center justify-center p-8 overflow-hidden');
    const image = document.createElement('img');
    image.src = meal.img;
    image.alt = meal.name;
    image.className = 'max-h-full max-w-full object-contain product-img transition-transform duration-700 group-hover:scale-110';
    image.loading = 'lazy';
    image.decoding = 'async';
    imageContainer.appendChild(image);

    const content = createElement('div', 'p-10 flex-grow flex flex-col border-t border-slate-50 text-center');
    const header = createElement('div', 'flex justify-between items-center mb-4');
    header.append(
        createElement('h3', 'text-xl font-bold text-slate-900', meal.name),
        createElement('span', 'text-brand-orange font-bold text-xl', `$${meal.price}`),
    );
    const description = createElement('p', 'text-slate-500 text-lg leading-relaxed font-light', meal.desc);
    content.append(header, description);

    card.append(ttsButton, imageContainer, content);
    return card;
}

function renderMenu() {
    const container = document.getElementById('mealContainer');
    if (!container) return;
    container.replaceChildren(...menuData.map(buildMealCard));
}

function appendUserMessage(history, text) {
    history.appendChild(createElement('div', 'ml-auto bg-brand-orange text-white p-4 rounded-3xl rounded-tr-none text-sm max-w-[85%] shadow-md', text));
}

function appendAiMessage(history, text) {
    const wrapper = createElement('div', 'flex gap-3');
    const avatar = document.createElement('img');
    avatar.src = AI_AVATAR_URL;
    avatar.alt = 'AI ??';
    avatar.className = 'h-10 w-10 rounded-full bg-orange-100 p-1 object-contain';

    const message = createElement('div', 'bg-white border p-4 rounded-3xl rounded-tl-none text-slate-700 max-w-[85%] shadow-sm leading-relaxed', text);
    wrapper.append(avatar, message);
    history.appendChild(wrapper);
}

async function sendMessage() {
    const input = document.getElementById('userInput');
    const history = document.getElementById('chatHistory');
    const loading = document.getElementById('chatLoading');
    if (!input || !history || !loading) return;

    const text = input.value.trim().slice(0, MAX_MESSAGE_LENGTH);
    if (!text) return;

    const now = Date.now();
    if (chatRequestInFlight || now - lastChatRequestAt < CHAT_COOLDOWN_MS) {
        showToast(MSG_WAIT);
        return;
    }

    chatRequestInFlight = true;
    lastChatRequestAt = now;
    appendUserMessage(history, text);
    input.value = '';
    loading.classList.remove('hidden');
    history.scrollTop = history.scrollHeight;

    try {
        const aiResponse = await callGAS(loading, 'chat', text);
        appendAiMessage(history, aiResponse || MSG_NO_RESPONSE);
    } finally {
        loading.classList.add('hidden');
        history.scrollTop = history.scrollHeight;
        chatRequestInFlight = false;
    }
}

async function callGAS(element, action, text) {
    const isButton = element instanceof HTMLButtonElement;
    if (isButton && element.classList.contains('ai-loading')) return '';
    if (isButton) element.classList.add('ai-loading');

    try {
        const response = await fetch(GAS_WEB_APP_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action,
                text: String(text).slice(0, MAX_MESSAGE_LENGTH),
                menuData,
                token: SECURITY_TOKEN,
                userId: 'visitor_888',
            }),
        });

        const raw = await response.text();
        let result = {};
        try {
            result = JSON.parse(raw);
        } catch (_ignored) {
            throw new Error(`Backend did not return JSON (HTTP ${response.status}). Check GAS deploy URL and access permission.`);
        }

        if (!response.ok) {
            throw new Error(result.error || `Backend HTTP ${response.status}`);
        }
        if (result.error) throw new Error(result.error);

        if (action === 'tts') {
            const pcmData = result.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
            if (!pcmData) throw new Error('Missing audio payload');

            const pcmBlob = Uint8Array.from(atob(pcmData), (char) => char.charCodeAt(0));
            const wavHeader = new ArrayBuffer(44);
            const view = new DataView(wavHeader);
            view.setUint32(0, 0x52494646, false);
            view.setUint32(4, 36 + pcmBlob.length, true);
            view.setUint32(8, 0x57415645, false);
            view.setUint32(12, 0x666d7420, false);
            view.setUint16(20, 1, true);
            view.setUint16(22, 1, true);
            view.setUint32(24, 24000, true);
            view.setUint32(28, 48000, true);
            view.setUint16(32, 2, true);
            view.setUint16(34, 16, true);
            view.setUint32(36, 0x64617461, false);
            view.setUint32(40, pcmBlob.length, true);

            const audioUrl = URL.createObjectURL(new Blob([wavHeader, pcmBlob], { type: 'audio/wav' }));
            const audio = new Audio(audioUrl);
            audio.addEventListener('ended', () => URL.revokeObjectURL(audioUrl), { once: true });
            audio.addEventListener('error', () => URL.revokeObjectURL(audioUrl), { once: true });
            await audio.play();
            return '';
        }

        return result.candidates?.[0]?.content?.parts?.[0]?.text || MSG_NO_RESPONSE;
    } catch (error) {
        const message = error && error.message ? error.message : MSG_SERVICE_DOWN;
        showToast(message);
        return message;
    } finally {
        if (isButton) element.classList.remove('ai-loading');
    }
}

function bindEvents() {
    const openAiChatButton = document.getElementById('openAiChatButton');
    const closeAiChatButton = document.getElementById('closeAiChatButton');
    const openStoreModalButton = document.getElementById('openStoreModalButton');
    const closeStoreModalButton = document.getElementById('closeStoreModalButton');
    const sendMessageButton = document.getElementById('sendMessageButton');
    const userInput = document.getElementById('userInput');
    const storeModal = document.getElementById('storeModal');

    openAiChatButton?.addEventListener('click', () => openAIChat(true));
    closeAiChatButton?.addEventListener('click', () => openAIChat(false));
    openStoreModalButton?.addEventListener('click', () => toggleModal(true));
    closeStoreModalButton?.addEventListener('click', () => toggleModal(false));
    sendMessageButton?.addEventListener('click', () => { void sendMessage(); });

    userInput?.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.isComposing) {
            event.preventDefault();
            void sendMessage();
        }
    });

    storeModal?.addEventListener('click', (event) => {
        if (event.target === storeModal) toggleModal(false);
    });

    document.querySelectorAll('.store-link-button').forEach((button) => {
        button.addEventListener('click', () => {
            const url = button.getAttribute('data-open-url');
            if (!url) return;
            safeOpen(url);
            toggleModal(false);
        });
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            openAIChat(false);
            toggleModal(false);
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    renderMenu();
    bindEvents();
});
