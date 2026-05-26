(function () {
  const $ = (id) => document.getElementById(id);
  const nf = new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 2 });
  const state = {
    socket: null,
    reconnectTimer: null,
    reconnectDelay: 800,
    lastPrice: null,
    barriers: null,
  };

  function fmt(value, digits = 2) {
    const number = Number(value);
    if (!Number.isFinite(number)) return "--";
    return number.toFixed(digits);
  }

  function fmtOi(value) {
    const number = Number(value);
    if (!Number.isFinite(number)) return "--";
    return nf.format(Math.round(number));
  }

  function setText(id, value) {
    const el = $(id);
    if (el) el.textContent = value;
  }

  function setStatus(status, detail) {
    const dot = $("apiDot");
    const text = $("apiStatusText");
    if (dot) dot.className = `api-status-dot ${status}`;
    if (text) {
      const label = status === "connected" ? "실시간 연결" : status === "mock" ? "모의 스트림" : "연결 대기";
      text.textContent = detail ? `${label} - ${detail}` : label;
    }
    if (window.KISBridge && typeof window.KISBridge.setStatus === "function") {
      try {
        window.KISBridge.setStatus(status);
      } catch (_) {
        // Existing legacy dashboards can have their own bridge implementation.
      }
    }
  }

  function updatePrice(price) {
    const number = Number(price);
    if (!Number.isFinite(number)) return;
    const previous = state.lastPrice;
    state.lastPrice = number;

    ["spotPrice", "k200"].forEach((id) => setText(id, fmt(number)));
    const spot = $("spotPrice") || $("k200");
    if (spot && previous !== null) {
      spot.classList.toggle("positive", number >= previous);
      spot.classList.toggle("negative", number < previous);
    }
    if (previous !== null) {
      const change = number - previous;
      setText("priceChange", `${change >= 0 ? "+" : ""}${fmt(change)} pt`);
    }
  }

  function updateOrderbook(data) {
    const oim = Number(data.oim);
    if (Number.isFinite(oim)) {
      const label = `${oim >= 0 ? "+" : ""}${oim.toFixed(3)}`;
      setText("oimVal", label);
      const el = $("oimVal");
      if (el) {
        el.classList.toggle("bull", oim >= 0);
        el.classList.toggle("bear", oim < 0);
      }
      setText("bidAskRatio", oim >= 0 ? "BID > ASK" : "ASK > BID");
    }
    if (data.micro_price !== null && data.micro_price !== undefined) {
      setText("microPrice", fmt(data.micro_price, 2));
      const gap = Number(data.micro_price) - Number(state.lastPrice || data.micro_price);
      setText("microGapVal", `${gap >= 0 ? "+" : ""}${fmt(gap, 2)} pt`);
    }
    setText("bidTotal", fmtOi(data.bid_total));
    setText("askTotal", fmtOi(data.ask_total));
  }

  function wallValue(wall) {
    return wall && wall.strike !== null && wall.strike !== undefined ? `${fmt(wall.strike)} pt` : "--";
  }

  function wallDistance(wall) {
    if (!wall || wall.distance === null || wall.distance === undefined) return "--";
    const distance = Number(wall.distance);
    return `${distance >= 0 ? "+" : ""}${fmt(distance)} pt`;
  }

  function wallStrength(wall) {
    if (!wall || wall.strength === null || wall.strength === undefined) return "--";
    return `${Math.round(Number(wall.strength) * 100)}%`;
  }

  function renderRail(barriers) {
    const range = barriers.range || {};
    const support = Number(range.support);
    const resistance = Number(range.resistance);
    const price = Number(barriers.current_price || barriers.underlying_price || state.lastPrice);
    if (!Number.isFinite(support) || !Number.isFinite(resistance) || support === resistance) return;
    const min = Math.min(support, resistance) - 1;
    const max = Math.max(support, resistance) + 1;
    const pos = (value) => `${Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100))}%`;

    const markers = [
      ["railPut", support],
      ["railCall", resistance],
      ["railCurrent", price],
      ["railMaxPain", Number(barriers.max_pain)],
      ["railGammaFlip", Number(barriers.gamma_flip)],
    ];
    markers.forEach(([id, value]) => {
      const el = $(id);
      if (el && Number.isFinite(value)) el.style.left = pos(value);
    });
  }

  function renderOiRows(rows) {
    const container = $("oiRows") || $("oiChart");
    if (!container || !Array.isArray(rows)) return;
    container.innerHTML = "";
    const maxVal = Math.max(1, ...rows.map((row) => Math.max(Number(row.call || row.call_oi || 0), Number(row.put || row.put_oi || 0))));
    rows.forEach((row) => {
      const call = Number(row.call || row.call_oi || 0);
      const put = Number(row.put || row.put_oi || 0);
      const item = document.createElement("div");
      item.className = `oi-row${row.highlight ? " highlight" : ""}`;
      item.innerHTML = `
        <span class="oi-strike">${fmt(row.strike, Number(row.strike) % 1 === 0 ? 0 : 1)}</span>
        <div class="oi-bars">
          <span class="oi-center"></span>
          <span class="oi-call" style="width:${(call / maxVal) * 48}%"></span>
          <span class="oi-put" style="width:${(put / maxVal) * 48}%"></span>
        </div>
        <span class="oi-num call-num">${fmtOi(call)}</span>
        <span class="oi-num put-num">${fmtOi(put)}</span>
      `;
      container.appendChild(item);
    });
  }

  function renderAlerts(alerts) {
    const container = $("alertsList");
    if (!container) return;
    container.innerHTML = "";
    if (!Array.isArray(alerts) || alerts.length === 0) {
      const empty = document.createElement("div");
      empty.className = "alert-item quiet";
      empty.textContent = "장벽 터치/이탈 경고 없음";
      container.appendChild(empty);
      return;
    }
    alerts.forEach((alert) => {
      const item = document.createElement("div");
      item.className = `alert-item ${alert.severity || "watch"}`;
      item.textContent = alert.message || `${alert.kind} ${wallDistance(alert)}`;
      container.appendChild(item);
    });
  }

  function applyBarriers(barriers) {
    if (!barriers) return;
    state.barriers = barriers;
    const putWall = barriers.put_wall || {};
    const callWall = barriers.call_wall || {};
    updatePrice(barriers.current_price || barriers.underlying_price);

    setText("putWallValue", wallValue(putWall));
    setText("callWallValue", wallValue(callWall));
    setText("klPutWall", wallValue(putWall));
    setText("klCallWall", wallValue(callWall));
    setText("maxPainValue", wallValue({ strike: barriers.max_pain }));
    setText("klMaxPain", wallValue({ strike: barriers.max_pain }));
    setText("gammaFlipValue", wallValue({ strike: barriers.gamma_flip }));
    setText("putWallDistance", wallDistance(putWall));
    setText("callWallDistance", wallDistance(callWall));
    setText("putWallStrength", wallStrength(putWall));
    setText("callWallStrength", wallStrength(callWall));
    setText("pcrVal", barriers.put_call_ratio === null ? "--" : fmt(barriers.put_call_ratio, 2));
    setText("dominantSide", barriers.dominant_side || "--");
    setText("totalCallOi", fmtOi(barriers.total_call_oi));
    setText("totalPutOi", fmtOi(barriers.total_put_oi));
    setText("supportLabel", wallValue(putWall));
    setText("resistanceLabel", wallValue(callWall));
    setText("rangeWidth", barriers.range && barriers.range.width !== null ? `${fmt(barriers.range.width)} pt` : "--");
    setText("lastUpdate", new Date(barriers.timestamp || Date.now()).toLocaleTimeString("ko-KR", { hour12: false }));

    renderRail(barriers);
    renderOiRows(barriers.oi_data);
    renderAlerts(barriers.alerts);
  }

  function handleMessage(data) {
    if (!data || !data.type) return;
    if (data.type === "snapshot") {
      updatePrice(data.current_price);
      updateOrderbook(data);
      applyBarriers(data.barriers);
      return;
    }
    if (data.type === "futures_tick") {
      updatePrice(data.current_price || data.FUTS_PRPR);
      return;
    }
    if (data.type === "orderbook") {
      updateOrderbook(data);
      return;
    }
    if (data.type === "barriers") {
      applyBarriers(data);
      return;
    }
    if (data.type === "oi_snapshot") {
      applyBarriers({
        type: "barriers",
        timestamp: data.timestamp,
        current_price: data.current_price,
        put_wall: data.put_wall,
        call_wall: data.call_wall,
        max_pain: data.max_pain,
        gamma_flip: data.gamma_flip,
        put_call_ratio: data.put_call_ratio,
        oi_data: data.oi_data,
        alerts: data.alerts,
        range: {
          support: data.put_wall && data.put_wall.strike,
          resistance: data.call_wall && data.call_wall.strike,
          width: data.call_wall && data.put_wall ? Number(data.call_wall.strike) - Number(data.put_wall.strike) : null,
        },
      });
    }
  }

  function wsUrl() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}/ws/stream`;
  }

  function connect() {
    if (state.socket && state.socket.readyState <= 1) return;
    setStatus("mock", "WebSocket 연결 중");
    const socket = new WebSocket(wsUrl());
    state.socket = socket;

    socket.addEventListener("open", () => {
      state.reconnectDelay = 800;
      setStatus("connected", "OI 장벽 수신 중");
    });
    socket.addEventListener("message", (event) => {
      try {
        handleMessage(JSON.parse(event.data));
      } catch (_) {
        setStatus("disconnected", "메시지 파싱 실패");
      }
    });
    socket.addEventListener("close", () => {
      setStatus("disconnected", "재연결 대기");
      clearTimeout(state.reconnectTimer);
      state.reconnectTimer = setTimeout(connect, state.reconnectDelay);
      state.reconnectDelay = Math.min(8000, state.reconnectDelay * 1.6);
    });
    socket.addEventListener("error", () => {
      setStatus("disconnected", "소켓 오류");
    });
  }

  window.OIBarrierBridge = {
    connect,
    handleMessage,
    applyBarriers,
    state,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", connect);
  } else {
    connect();
  }
})();
