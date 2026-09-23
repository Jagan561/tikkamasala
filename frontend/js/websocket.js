/**
 * WebSocket client with auto-reconnect.
 */
let _ws = null;
let _wsReconnectTimer = null;
let _wsHandlers = {};

function wsConnect() {
  const token = api.getToken();
  if (!token) return;

  const wsUrl = `ws://localhost:8000/api/ws/orders?token=${encodeURIComponent(token)}`;
  _ws = new WebSocket(wsUrl);

  _ws.onopen = () => {
    console.log('WebSocket connected');
    clearTimeout(_wsReconnectTimer);
    // Keep-alive ping every 30s
    _ws._pingInterval = setInterval(() => {
      if (_ws.readyState === WebSocket.OPEN) _ws.send('ping');
    }, 30000);
  };

  _ws.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      if (data.event === 'pong') return;
      console.log('WS event:', data);
      const handler = _wsHandlers[data.event] || _wsHandlers['*'];
      if (handler) handler(data);
      // Dispatch DOM event for pages to listen
      document.dispatchEvent(new CustomEvent('ws:' + data.event, { detail: data }));
    } catch (err) {
      console.error('WS parse error:', err);
    }
  };

  _ws.onclose = (e) => {
    clearInterval(_ws._pingInterval);
    if (e.code !== 4001) {
      // Reconnect unless auth failure
      _wsReconnectTimer = setTimeout(wsConnect, 3000);
    }
  };

  _ws.onerror = (err) => {
    console.warn('WebSocket error:', err);
  };
}

function wsOn(event, handler) {
  _wsHandlers[event] = handler;
}

function wsDisconnect() {
  if (_ws) { _ws.close(); _ws = null; }
  clearTimeout(_wsReconnectTimer);
}
