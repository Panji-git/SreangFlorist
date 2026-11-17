/**
 * Sreang Florist — Bespoke Botanical Atelier & Retail Analytics System
 * Vanilla JavaScript Single Page Application (SPA) Controller
 */

// Application State
const state = {
  currentUser: null,
  isAdmin: false,
  basePrice: 185000.0,
  attributes: {
    bunga_utama: [],
    bahan_wrap: [],
    gaya_rangkaian: [],
    ukuran: [],
  },
  selectedAttributes: {
    bunga_utama: null,
    bahan_wrap: null,
    gaya_rangkaian: null,
    ukuran: null,
  },
  recommendation: null,
  currentAdminStatusFilter: "",
};

// ============================================================================
// INITIALIZATION
// ============================================================================
document.addEventListener("DOMContentLoaded", async () => {
  // Check stored customer session
  const storedUser = localStorage.getItem("sreang_customer");
  if (storedUser) {
    try {
      state.currentUser = JSON.parse(storedUser);
      await refreshCurrentUser();
    } catch (e) {
      console.warn("Invalid session cache:", e);
      localStorage.removeItem("sreang_customer");
    }
  }

  // Set default pickup date (tomorrow)
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const tomorrowStr = tomorrow.toISOString().split("T")[0];
  const dateInput = document.getElementById("checkout-pickup-date");
  if (dateInput) {
    dateInput.value = tomorrowStr;
    dateInput.min = new Date().toISOString().split("T")[0];
  }

  updateAuthUI();
  await loadCatalogAttributes();
  await loadSpecialRecommendation();
});

// ============================================================================
// AUTHENTICATION & SESSION
// ============================================================================
function updateAuthUI() {
  const badge = document.getElementById("user-badge");
  const loginBtn = document.getElementById("btn-login-modal");
  const nameDisp = document.getElementById("user-name-display");
  const pointsDisp = document.getElementById("user-points-display");
  const tierPill = document.getElementById("user-tier-pill");

  if (state.currentUser) {
    badge.classList.remove("hidden");
    badge.classList.add("flex");
    loginBtn.classList.add("hidden");

    nameDisp.textContent = state.currentUser.name;
    pointsDisp.textContent = `${state.currentUser.total_points || 0} Poin`;
    tierPill.textContent = (state.currentUser.tier_status || "Bronze Tier").replace(" Tier", "");
  } else {
    badge.classList.add("hidden");
    badge.classList.remove("flex");
    loginBtn.classList.remove("hidden");
  }
}

async function refreshCurrentUser() {
  if (!state.currentUser) return;
  try {
    const res = await fetch(`/api/auth/me?user_id=${state.currentUser.id}`);
    if (res.ok) {
      const data = await res.json();
      state.currentUser = { ...state.currentUser, ...data };
      localStorage.setItem("sreang_customer", JSON.stringify(state.currentUser));
      updateAuthUI();
    }
  } catch (err) {
    console.warn("Could not refresh profile:", err);
  }
}

function openLoginModal() {
  document.getElementById("modal-customer-login").classList.remove("hidden");
}

function closeLoginModal() {
  document.getElementById("modal-customer-login").classList.add("hidden");
}

async function handleCustomerLoginSubmit(e) {
  e.preventDefault();
  const name = document.getElementById("login-input-name").value.trim();
  const phone = document.getElementById("login-input-phone").value.trim();

  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, phone_number: phone }),
    });

    const data = await res.json();
    if (res.ok && data.success) {
      state.currentUser = data.user;
      localStorage.setItem("sreang_customer", JSON.stringify(data.user));
      updateAuthUI();
      closeLoginModal();
      showNotification(`Selamat datang, ${data.user.name}!`);
    } else {
      alert(data.detail || "Gagal masuk. Periksa kembali nama & nomor HP.");
    }
  } catch (err) {
    alert("Terjadi kesalahan koneksi server.");
  }
}

function handleCustomerLogout() {
  state.currentUser = null;
  localStorage.removeItem("sreang_customer");
  updateAuthUI();
  switchCustomerTab("studio");
  showNotification("Anda telah keluar dari akun.");
}

// Admin Auth
function openAdminLoginModal() {
  document.getElementById("modal-admin-login").classList.remove("hidden");
}

function closeAdminLoginModal() {
  document.getElementById("modal-admin-login").classList.add("hidden");
}

async function handleAdminLoginSubmit(e) {
  e.preventDefault();
  const id = document.getElementById("admin-input-id").value.trim();
  const pin = document.getElementById("admin-input-pin").value.trim();

  try {
    const res = await fetch("/api/auth/admin-login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier: id, pin_code: pin }),
    });

    const data = await res.json();
    if (res.ok && data.success) {
      state.isAdmin = true;
      closeAdminLoginModal();
      enterAdminPortal();
      showNotification("Selamat datang di Portal Admin Sreang Florist.");
    } else {
      alert(data.detail || "Kredensial atau PIN Admin salah.");
    }
  } catch (err) {
    alert("Koneksi gagal ke server admin.");
  }
}

function enterAdminPortal() {
  document.getElementById("customer-header").classList.add("hidden");
  document.getElementById("admin-header").classList.remove("hidden");

  // Hide customer panes
  document.getElementById("customer-view-studio").classList.add("hidden");
  document.getElementById("customer-view-loyalty").classList.add("hidden");
  document.getElementById("customer-view-orders").classList.add("hidden");

  // Show admin root
  document.getElementById("admin-view-root").classList.remove("hidden");
  switchAdminTab("orders");
}

function exitAdminPortal() {
  state.isAdmin = false;
  document.getElementById("admin-header").classList.add("hidden");
  document.getElementById("customer-header").classList.remove("hidden");

  document.getElementById("admin-view-root").classList.add("hidden");
  switchCustomerTab("studio");
}

// ============================================================================
// NAVIGATION TABS
// ============================================================================
function switchCustomerTab(tab) {
  // Panes
  const pStudio = document.getElementById("customer-view-studio");
  const pLoyalty = document.getElementById("customer-view-loyalty");
  const pOrders = document.getElementById("customer-view-orders");

  // Buttons
  const bStudio = document.getElementById("nav-btn-studio");
  const bLoyalty = document.getElementById("nav-btn-loyalty");
  const bOrders = document.getElementById("nav-btn-orders");

  [pStudio, pLoyalty, pOrders].forEach((p) => p.classList.add("hidden"));
  [bStudio, bLoyalty, bOrders].forEach((b) => {
    b.classList.remove("text-cypress", "border-cypress");
    b.classList.add("text-cypress/60", "border-transparent");
  });

  if (tab === "studio") {
    pStudio.classList.remove("hidden");
    bStudio.classList.add("text-cypress", "border-cypress");
    bStudio.classList.remove("text-cypress/60", "border-transparent");
  } else if (tab === "loyalty") {
    if (!state.currentUser) {
      openLoginModal();
      return;
    }
    pLoyalty.classList.remove("hidden");
    bLoyalty.classList.add("text-cypress", "border-cypress");
    bLoyalty.classList.remove("text-cypress/60", "border-transparent");
    loadCustomerLoyalty();
  } else if (tab === "orders") {
    if (!state.currentUser) {
      openLoginModal();
      return;
    }
    pOrders.classList.remove("hidden");
    bOrders.classList.add("text-cypress", "border-cypress");
    bOrders.classList.remove("text-cypress/60", "border-transparent");
    loadCustomerOrders();
  }
}

function switchAdminTab(tab) {
  const pOrders = document.getElementById("admin-pane-orders");
  const pInventory = document.getElementById("admin-pane-inventory");
  const pAnalytics = document.getElementById("admin-pane-analytics");

  const bOrders = document.getElementById("admin-tab-orders");
  const bInventory = document.getElementById("admin-tab-inventory");
  const bAnalytics = document.getElementById("admin-tab-analytics");

  [pOrders, pInventory, pAnalytics].forEach((p) => p.classList.add("hidden"));
  [bOrders, bInventory, bAnalytics].forEach((b) => {
    b.classList.remove("text-white", "border-amber-gold");
    b.classList.add("text-parchment-warm/70", "border-transparent");
  });

  if (tab === "orders") {
    pOrders.classList.remove("hidden");
    bOrders.classList.add("text-white", "border-amber-gold");
    bOrders.classList.remove("text-parchment-warm/70", "border-transparent");
    loadAdminOrders();
  } else if (tab === "inventory") {
    pInventory.classList.remove("hidden");
    bInventory.classList.add("text-white", "border-amber-gold");
    bInventory.classList.remove("text-parchment-warm/70", "border-transparent");
    loadAdminInventory();
  } else if (tab === "analytics") {
    pAnalytics.classList.remove("hidden");
    bAnalytics.classList.add("text-white", "border-amber-gold");
    bAnalytics.classList.remove("text-parchment-warm/70", "border-transparent");
    loadAdminAnalytics();
  }
}

// ============================================================================
// CATALOG & ATELIER CRAFTING STUDIO
// ============================================================================
async function loadCatalogAttributes() {
  try {
    const res = await fetch("/api/catalog/attributes");
    const data = await res.json();
    state.basePrice = data.base_price || 185000.0;
    state.attributes = data.categories;

    renderCategoryGrid("bunga_utama", data.categories.bunga_utama);
    renderCategoryGrid("bahan_wrap", data.categories.bahan_wrap);
    renderCategoryGrid("gaya_rangkaian", data.categories.gaya_rangkaian);
    renderCategoryGrid("ukuran", data.categories.ukuran);

    updateLivePrice();
  } catch (err) {
    console.error("Failed to load catalog attributes:", err);
  }
}

function renderCategoryGrid(category, items) {
  const container = document.getElementById(`grid-${category}`);
  if (!container) return;

  container.innerHTML = items
    .map((item) => {
      const priceText =
        item.price_modifier > 0
          ? `+Rp ${item.price_modifier.toLocaleString("id-ID")}`
          : "Termasuk Base Price";
      const stockBadge =
        item.stock < 999
          ? `<span class="text-[10px] text-cypress/50">Stok: ${item.stock}</span>`
          : "";

      return `
        <div 
          id="attr-card-${item.id}"
          onclick="handleSelectAttribute('${category}', ${item.id})"
          class="attribute-card bg-white p-5 rounded-2xl border border-cypress/10 hover:border-amber-gold/50 shadow-sm flex flex-col justify-between"
        >
          <div>
            <div class="flex items-start justify-between">
              <h4 class="font-serif font-bold text-base text-cypress">${item.name}</h4>
              <span class="selection-check hidden text-amber-gold text-lg font-bold">✓</span>
            </div>
          </div>
          <div class="mt-4 pt-3 border-t border-cypress/5 flex items-center justify-between text-xs">
            <span class="font-semibold text-amber-gold">${priceText}</span>
            ${stockBadge}
          </div>
        </div>
      `;
    })
    .join("");
}

function handleSelectAttribute(category, attrId) {
  const item = state.attributes[category].find((a) => a.id === attrId);
  if (!item) return;

  state.selectedAttributes[category] = item;

  // Update card UI
  state.attributes[category].forEach((a) => {
    const card = document.getElementById(`attr-card-${a.id}`);
    if (card) {
      if (a.id === attrId) {
        card.classList.add("selected");
        card.querySelector(".selection-check").classList.remove("hidden");
      } else {
        card.classList.remove("selected");
        card.querySelector(".selection-check").classList.add("hidden");
      }
    }
  });

  updateLivePrice();
}

function updateLivePrice() {
  let modifierSum = 0;
  let selectedCount = 0;

  for (const cat of ["bunga_utama", "bahan_wrap", "gaya_rangkaian", "ukuran"]) {
    if (state.selectedAttributes[cat]) {
      selectedCount++;
      modifierSum += state.selectedAttributes[cat].price_modifier;
    }
  }

  const total = state.basePrice + modifierSum;
  document.getElementById("live-total-price").textContent = `Rp ${total.toLocaleString("id-ID")}`;
  document.getElementById("selection-counter").textContent = selectedCount;

  const proceedBtn = document.getElementById("btn-proceed-checkout");
  const validationTag = document.getElementById("validation-tag");

  if (selectedCount === 4) {
    proceedBtn.disabled = false;
    validationTag.textContent = "Lengkap (4/4)";
    validationTag.className = "text-[10px] bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full border border-emerald-200 font-semibold";
  } else {
    proceedBtn.disabled = true;
    validationTag.textContent = `Pilih 4 Dimensi (${selectedCount}/4)`;
    validationTag.className = "text-[10px] bg-amber-50 text-amber-700 px-2 py-0.5 rounded-full border border-amber-200 font-semibold";
  }
}

// ============================================================================
// FP-GROWTH SPECIAL RECOMMENDATION BANNER
// ============================================================================
async function loadSpecialRecommendation() {
  try {
    const res = await fetch("/api/catalog/recommendations");
    const data = await res.json();
    state.recommendation = data;

    if (data.has_recommendation && data.items.length > 0) {
      const banner = document.getElementById("recommendation-banner");
      banner.classList.remove("hidden");

      document.getElementById("rec-title").textContent = data.title;
      document.getElementById("rec-badge").textContent = data.badge || "Pilihan Terfavorit";
      document.getElementById("rec-description").textContent = data.description;

      const liftVal = (data.lift || 1.0).toFixed(2);
      const confPct = Math.round((data.confidence || 0.9) * 100);
      document.getElementById("rec-compatibility-badge").textContent = `Keselarasan ${confPct}% • Lift ${liftVal}`;

      const grid = document.getElementById("rec-items-grid");
      grid.innerHTML = data.items
        .map(
          (item) => `
          <div class="bg-white/80 p-3 rounded-xl border border-cypress/10 shadow-xs">
            <span class="text-[10px] uppercase font-bold text-amber-gold tracking-wider block">
              ${formatCategoryName(item.category)}
            </span>
            <span class="font-serif font-bold text-sm text-cypress block mt-0.5">
              ${item.name}
            </span>
          </div>
        `
        )
        .join("");
    }
  } catch (err) {
    console.warn("Recommendation load failed:", err);
  }
}

function formatCategoryName(cat) {
  const map = {
    bunga_utama: "Bunga Utama",
    bahan_wrap: "Bahan Wrap",
    gaya_rangkaian: "Gaya Rangkaian",
    ukuran: "Ukuran Tangkai",
  };
  return map[cat] || cat;
}

function applyRecommendation() {
  if (!state.recommendation || !state.recommendation.items) return;

  state.recommendation.items.forEach((item) => {
    if (item.category && item.id) {
      handleSelectAttribute(item.category, item.id);
    }
  });

  // Smooth scroll to studio
  const studio = document.getElementById("crafting-studio");
  if (studio) {
    studio.scrollIntoView({ behavior: "smooth" });
  }

  showNotification("Kombinasi Rekomendasi Terpilih di Atelier Studio!");
}

// ============================================================================
// CHECKOUT & PRE-ORDER SCHEDULING
// ============================================================================
function openCheckoutModal() {
  if (!state.currentUser) {
    openLoginModal();
    return;
  }

  // Populate Summary
  const summaryContainer = document.getElementById("checkout-summary-items");
  summaryContainer.innerHTML = `
    <div><span class="text-cypress/50 block">Bunga:</span> ${state.selectedAttributes.bunga_utama?.name}</div>
    <div><span class="text-cypress/50 block">Wrap:</span> ${state.selectedAttributes.bahan_wrap?.name}</div>
    <div><span class="text-cypress/50 block">Gaya:</span> ${state.selectedAttributes.gaya_rangkaian?.name}</div>
    <div><span class="text-cypress/50 block">Ukuran:</span> ${state.selectedAttributes.ukuran?.name}</div>
  `;

  // Update Points Section
  const availPoints = state.currentUser.total_points || 0;
  document.getElementById("checkout-available-points").textContent = `Poin Anda: ${availPoints} Poin (Dapat ditukar)`;
  const usePointsCheckbox = document.getElementById("checkout-use-points");
  usePointsCheckbox.checked = false;

  updateCheckoutPrice();
  document.getElementById("modal-checkout").classList.remove("hidden");
}

function closeCheckoutModal() {
  document.getElementById("modal-checkout").classList.add("hidden");
}

function toggleUsePoints() {
  updateCheckoutPrice();
}

function updateCheckoutPrice() {
  let modifierSum = 0;
  for (const cat of ["bunga_utama", "bahan_wrap", "gaya_rangkaian", "ukuran"]) {
    if (state.selectedAttributes[cat]) {
      modifierSum += state.selectedAttributes[cat].price_modifier;
    }
  }

  let total = state.basePrice + modifierSum;
  const usePoints = document.getElementById("checkout-use-points").checked;
  const points = state.currentUser?.total_points || 0;

  if (usePoints && points > 0) {
    const discount = points * 100; // 1 point = Rp 100
    total = Math.max(0, total - discount);
  }

  document.getElementById("checkout-final-price").textContent = `Rp ${total.toLocaleString("id-ID")}`;
}

async function submitOrder() {
  const pickupDate = document.getElementById("checkout-pickup-date").value;
  const pickupTimeSlot = document.getElementById("checkout-time-slot").value;
  const cardTheme = document.getElementById("checkout-card-theme").value;
  const cardMessage = document.getElementById("checkout-card-message").value.trim();
  const usePoints = document.getElementById("checkout-use-points").checked;

  const pointsToUse = usePoints ? state.currentUser.total_points : 0;
  const attributeIds = [
    state.selectedAttributes.bunga_utama.id,
    state.selectedAttributes.bahan_wrap.id,
    state.selectedAttributes.gaya_rangkaian.id,
    state.selectedAttributes.ukuran.id,
  ];

  try {
    const res = await fetch("/api/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: state.currentUser.id,
        attribute_ids: attributeIds,
        pickup_date: pickupDate,
        pickup_time_slot: pickupTimeSlot,
        card_theme: cardTheme,
        card_message: cardMessage,
        points_to_use: pointsToUse,
      }),
    });

    const data = await res.json();
    if (res.ok && data.success) {
      closeCheckoutModal();

      // Show Confirmation Modal
      document.getElementById("success-order-id").textContent = data.order.id;
      document.getElementById("success-pickup-info").textContent = `${data.order.pickup_date} • ${data.order.pickup_time_slot}`;
      document.getElementById("success-price-info").textContent = `Rp ${data.order.total_price.toLocaleString("id-ID")}`;
      document.getElementById("success-points-info").textContent = `+${data.order.points_earned} Poin (Saat status Selesai)`;
      document.getElementById("modal-order-success").classList.remove("hidden");

      // Refresh user points
      await refreshCurrentUser();
    } else {
      alert(data.detail || "Gagal membuat pesanan. Periksa pilihan komponen.");
    }
  } catch (err) {
    alert("Terjadi kesalahan saat memproses pesanan.");
  }
}

function closeSuccessModal() {
  document.getElementById("modal-order-success").classList.add("hidden");
  switchCustomerTab("orders");
}

// ============================================================================
// SREANG CLUB LOYALTY PASS VIEW
// ============================================================================
async function loadCustomerLoyalty() {
  if (!state.currentUser) return;

  try {
    const res = await fetch(`/api/loyalty/status/${state.currentUser.id}`);
    const data = await res.json();

    document.getElementById("loyalty-customer-name").textContent = data.name;
    document.getElementById("loyalty-customer-phone").textContent = data.phone_number;
    document.getElementById("loyalty-tier-badge").textContent = data.tier;
    document.getElementById("loyalty-tier-icon").textContent = data.icon || "✨";
    document.getElementById("loyalty-points-val").textContent = data.total_points;
    document.getElementById("loyalty-completed-orders").textContent = `${data.total_completed_orders} Pesanan`;

    document.getElementById("loyalty-progress-text").textContent = `${data.total_points} / ${data.reward_target_points} Poin`;
    document.getElementById("loyalty-progress-bar").style.width = `${data.progress_percentage}%`;

    // Dynamic pass style class
    const cardBg = document.getElementById("loyalty-card-bg");
    cardBg.className = "text-parchment-warm rounded-3xl p-8 relative overflow-hidden shadow-2xl transition-all";
    if (data.tier === "Gold Tier") {
      cardBg.classList.add("gold-pass");
    } else if (data.tier === "Silver Tier") {
      cardBg.classList.add("silver-pass");
    } else {
      cardBg.classList.add("bronze-pass");
    }

    // Render perks
    const perksList = document.getElementById("loyalty-perks-list");
    perksList.innerHTML = (data.perks || [])
      .map(
        (perk) => `
        <li class="flex items-start space-x-2">
          <span class="text-amber-gold font-bold">✓</span>
          <span>${perk}</span>
        </li>
      `
      )
      .join("");
  } catch (err) {
    console.error("Failed to load loyalty pass:", err);
  }
}

// ============================================================================
// CUSTOMER ORDER HISTORY
// ============================================================================
async function loadCustomerOrders() {
  if (!state.currentUser) return;
  const container = document.getElementById("customer-orders-container");
  container.innerHTML = `<p class="text-xs text-cypress/50">Memuat riwayat pesanan...</p>`;

  try {
    const res = await fetch(`/api/orders?user_id=${state.currentUser.id}`);
    const orders = await res.json();

    if (!orders.length) {
      container.innerHTML = `
        <div class="text-center py-12 bg-white rounded-2xl border border-cypress/10">
          <p class="text-cypress/60 text-sm">Belum ada riwayat pesanan.</p>
          <button onclick="switchCustomerTab('studio')" class="mt-3 text-xs bg-cypress text-white px-4 py-2 rounded-xl font-medium">
            Mulai Kustomisasi Buket Sekarang
          </button>
        </div>
      `;
      return;
    }

    container.innerHTML = orders
      .map((o) => {
        let statusBadge = "bg-amber-100 text-amber-800";
        if (o.status === "Diproses") statusBadge = "bg-blue-100 text-blue-800";
        if (o.status === "Selesai") statusBadge = "bg-emerald-100 text-emerald-800";
        if (o.status === "Dibatalkan") statusBadge = "bg-rose-100 text-rose-800";

        return `
        <div class="bg-white p-5 rounded-2xl border border-cypress/10 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div class="space-y-1">
            <div class="flex items-center space-x-3">
              <span class="font-serif font-bold text-lg text-cypress">${o.id}</span>
              <span class="text-xs px-2.5 py-0.5 rounded-full font-semibold ${statusBadge}">${o.status}</span>
            </div>
            <p class="text-xs text-cypress/70">
              <strong>Jadwal Ambil:</strong> ${o.pickup_date} • ${o.pickup_time_slot}
            </p>
            <p class="text-xs text-cypress/60 italic">
              "${o.components || "Kustomisasi Atelier"}"
            </p>
          </div>

          <div class="text-right">
            <span class="text-xs text-cypress/60 block">Total Transaksi</span>
            <span class="font-serif font-bold text-lg text-cypress">Rp ${o.total_price.toLocaleString("id-ID")}</span>
            <span class="text-[11px] text-amber-gold font-medium block">+${o.points_earned} Poin Loyalitas</span>
          </div>
        </div>
      `;
      })
      .join("");
  } catch (err) {
    container.innerHTML = `<p class="text-xs text-rose-600">Gagal memuat pesanan.</p>`;
  }
}

// ============================================================================
// ADMIN: ORDERS MANAGEMENT
// ============================================================================
async function loadAdminOrders(statusFilter = state.currentAdminStatusFilter) {
  state.currentAdminStatusFilter = statusFilter;
  const container = document.getElementById("admin-orders-table-container");
  container.innerHTML = `<p class="p-6 text-xs text-cypress/50">Memuat pesanan...</p>`;

  try {
    let url = "/api/orders?limit=100";
    if (statusFilter) url += `&status=${encodeURIComponent(statusFilter)}`;

    const res = await fetch(url);
    const orders = await res.json();

    if (!orders.length) {
      container.innerHTML = `<p class="p-8 text-center text-sm text-cypress/50">Tidak ada pesanan dengan filter status ini.</p>`;
      return;
    }

    container.innerHTML = `
      <table class="w-full text-left text-xs border-collapse">
        <thead class="bg-cypress/5 text-cypress font-semibold uppercase tracking-wider text-[11px] border-b border-cypress/10">
          <tr>
            <th class="p-4">ID Pesanan</th>
            <th class="p-4">Pelanggan</th>
            <th class="p-4">Jadwal Ambil</th>
            <th class="p-4">Rincian Komponen</th>
            <th class="p-4">Total Harga</th>
            <th class="p-4">Status</th>
            <th class="p-4 text-center">Aksi Operasional</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-cypress/5">
          ${orders
            .map((o) => {
              let statusBadge = "bg-amber-100 text-amber-800";
              if (o.status === "Diproses") statusBadge = "bg-blue-100 text-blue-800";
              if (o.status === "Selesai") statusBadge = "bg-emerald-100 text-emerald-800";
              if (o.status === "Dibatalkan") statusBadge = "bg-rose-100 text-rose-800";

              return `
              <tr class="hover:bg-cypress/5 transition">
                <td class="p-4 font-mono font-bold text-cypress">${o.id}</td>
                <td class="p-4">
                  <div class="font-bold text-cypress">${o.customer_name}</div>
                  <div class="text-[10px] text-cypress/50">${o.phone_number}</div>
                </td>
                <td class="p-4">
                  <div>${o.pickup_date}</div>
                  <div class="text-[10px] text-cypress/50">${o.pickup_time_slot}</div>
                </td>
                <td class="p-4 max-w-xs text-cypress/80 truncate" title="${o.components}">
                  ${o.components}
                </td>
                <td class="p-4 font-bold text-cypress">
                  Rp ${o.total_price.toLocaleString("id-ID")}
                </td>
                <td class="p-4">
                  <span class="px-2.5 py-1 rounded-full text-[10px] font-bold ${statusBadge}">
                    ${o.status}
                  </span>
                </td>
                <td class="p-4 text-center">
                  <div class="flex items-center justify-center space-x-1.5">
                    ${
                      o.status === "Menunggu"
                        ? `<button onclick="updateOrderStatus('${o.id}', 'Diproses')" class="bg-blue-600 hover:bg-blue-700 text-white px-2.5 py-1 rounded-lg text-[10px] font-semibold transition">Proses</button>`
                        : ""
                    }
                    ${
                      o.status === "Diproses"
                        ? `<button onclick="updateOrderStatus('${o.id}', 'Selesai')" class="bg-emerald-600 hover:bg-emerald-700 text-white px-2.5 py-1 rounded-lg text-[10px] font-semibold transition">Selesaikan</button>`
                        : ""
                    }
                    ${
                      o.status === "Selesai"
                        ? `<span class="text-emerald-700 text-[10px] font-bold">✓ Poin Masuk</span>`
                        : ""
                    }
                  </div>
                </td>
              </tr>
            `;
            })
            .join("")}
        </tbody>
      </table>
    `;
  } catch (err) {
    container.innerHTML = `<p class="p-6 text-xs text-rose-600">Gagal memuat pesanan admin.</p>`;
  }
}

function filterAdminOrders(status) {
  const buttons = document.querySelectorAll(".admin-filter-btn");
  buttons.forEach((b) => {
    b.className = "admin-filter-btn bg-white hover:bg-cypress/5 text-cypress px-3 py-1.5 rounded-lg border border-cypress/10 font-medium";
  });
  event.target.className = "admin-filter-btn bg-cypress text-white px-3 py-1.5 rounded-lg font-medium";
  loadAdminOrders(status);
}

async function updateOrderStatus(orderId, newStatus) {
  try {
    const res = await fetch(`/api/orders/${encodeURIComponent(orderId)}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus }),
    });

    const data = await res.json();
    if (res.ok && data.success) {
      showNotification(`Pesanan ${orderId} beralih ke '${newStatus}'.`);
      if (newStatus === "Selesai") {
        showNotification("Poin loyalitas dan klaster RFM K-Means diperbarui otomatis!", 4000);
      }
      loadAdminOrders();
    } else {
      alert(data.detail || "Gagal mengubah status pesanan.");
    }
  } catch (err) {
    alert("Terjadi kesalahan jaringan.");
  }
}

// ============================================================================
// ADMIN: INVENTORY MANAGEMENT
// ============================================================================
async function loadAdminInventory() {
  const container = document.getElementById("admin-inventory-table-container");
  container.innerHTML = `<p class="p-6 text-xs text-cypress/50">Memuat inventori master...</p>`;

  try {
    const res = await fetch("/api/catalog/all-attributes");
    const items = await res.json();

    container.innerHTML = `
      <table class="w-full text-left text-xs border-collapse">
        <thead class="bg-cypress/5 text-cypress font-semibold uppercase tracking-wider text-[11px] border-b border-cypress/10">
          <tr>
            <th class="p-4">Kategori</th>
            <th class="p-4">Nama Komponen</th>
            <th class="p-4">Harga Tambahan (Modifier)</th>
            <th class="p-4">Stok Fisik</th>
            <th class="p-4">Status Aktif</th>
            <th class="p-4 text-center">Aksi Simpan</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-cypress/5">
          ${items
            .map(
              (item) => `
            <tr class="hover:bg-cypress/5 transition">
              <td class="p-4 font-bold text-cypress/70 uppercase text-[10px]">
                ${formatCategoryName(item.category)}
              </td>
              <td class="p-4 font-bold text-cypress font-serif text-sm">
                ${item.name}
              </td>
              <td class="p-4">
                <input 
                  id="inv-price-${item.id}" 
                  type="number" 
                  value="${item.price_modifier}" 
                  class="w-32 px-2.5 py-1.5 rounded-lg border border-cypress/20 text-xs focus:outline-none focus:border-amber-gold"
                >
              </td>
              <td class="p-4">
                <input 
                  id="inv-stock-${item.id}" 
                  type="number" 
                  value="${item.stock}" 
                  class="w-24 px-2.5 py-1.5 rounded-lg border border-cypress/20 text-xs focus:outline-none focus:border-amber-gold"
                >
              </td>
              <td class="p-4">
                <select id="inv-active-${item.id}" class="px-2.5 py-1.5 rounded-lg border border-cypress/20 text-xs">
                  <option value="1" ${item.is_active === 1 ? "selected" : ""}>Aktif (Tampil)</option>
                  <option value="0" ${item.is_active === 0 ? "selected" : ""}>Non-Aktif (Sembunyi)</option>
                </select>
              </td>
              <td class="p-4 text-center">
                <button onclick="saveInventoryItem(${item.id})" class="bg-cypress hover:bg-cypress-light text-white text-xs px-3 py-1.5 rounded-lg font-medium transition shadow-xs">
                  Simpan
                </button>
              </td>
            </tr>
          `
            )
            .join("")}
        </tbody>
      </table>
    `;
  } catch (err) {
    container.innerHTML = `<p class="p-6 text-xs text-rose-600">Gagal memuat inventori.</p>`;
  }
}

async function saveInventoryItem(id) {
  const stock = parseInt(document.getElementById(`inv-stock-${id}`).value, 10);
  const price = parseFloat(document.getElementById(`inv-price-${id}`).value);
  const isActive = parseInt(document.getElementById(`inv-active-${id}`).value, 10);

  try {
    const res = await fetch(`/api/catalog/attributes/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        stock: isNaN(stock) ? 0 : stock,
        price_modifier: isNaN(price) ? 0.0 : price,
        is_active: isActive,
      }),
    });

    const data = await res.json();
    if (res.ok && data.success) {
      showNotification(data.message || "Komponen berhasil diperbarui.");
      loadCatalogAttributes(); // sync catalog in studio
    } else {
      alert(data.detail || "Gagal menyimpan atribut.");
    }
  } catch (err) {
    alert("Terjadi kesalahan jaringan.");
  }
}

// ============================================================================
// ADMIN: LIVE ANALYTICAL HUB (TA DATA MINING GATEWAY)
// ============================================================================
async function loadAdminAnalytics() {
  try {
    const res = await fetch("/api/analytics/summary");
    const data = await res.json();

    // 1. KPI Cards
    const sil = data.kmeans.silhouette_score.toFixed(4);
    document.getElementById("metric-silhouette").textContent = sil;
    document.getElementById("metric-total-customers").textContent = data.kmeans.total_segmented_customers;
    document.getElementById("metric-fpgrowth-tx").textContent = data.fp_growth.total_mined_transactions;
    document.getElementById("metric-rules-count").textContent = data.fp_growth.total_rules;

    // 2. K-Means Clusters Table
    const clustersContainer = document.getElementById("analytics-clusters-container");
    clustersContainer.innerHTML = `
      <table class="w-full text-left text-xs border-collapse">
        <thead class="bg-cypress/5 text-cypress font-semibold uppercase tracking-wider text-[11px] border-b border-cypress/10">
          <tr>
            <th class="p-3">Klaster / Tier</th>
            <th class="p-3">Jumlah Anggota</th>
            <th class="p-3">Rata-rata Recency (Hari)</th>
            <th class="p-3">Rata-rata Frequency</th>
            <th class="p-3">Rata-rata Belanja (Monetary)</th>
            <th class="p-3">Composite Score</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-cypress/5">
          ${data.kmeans.clusters
            .map(
              (c) => `
            <tr class="hover:bg-cypress/5 transition">
              <td class="p-3 font-bold text-cypress">
                <span class="inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                  c.tier_label === "Gold Tier"
                    ? "bg-amber-100 text-amber-800"
                    : c.tier_label === "Silver Tier"
                    ? "bg-slate-200 text-slate-800"
                    : "bg-amber-800/10 text-amber-900"
                }">
                  ${c.tier_label}
                </span>
              </td>
              <td class="p-3 font-semibold">${c.size} Pelanggan</td>
              <td class="p-3">${c.avg_recency_days} hari lalu</td>
              <td class="p-3">${c.avg_frequency} kali pesanan</td>
              <td class="p-3 font-bold text-cypress">Rp ${c.avg_monetary_rp.toLocaleString("id-ID")}</td>
              <td class="p-3 text-amber-gold font-bold">${c.composite_score}</td>
            </tr>
          `
            )
            .join("")}
        </tbody>
      </table>
    `;

    // 3. FP-Growth Rules Table
    const rulesContainer = document.getElementById("analytics-rules-container");
    rulesContainer.innerHTML = `
      <table class="w-full text-left text-xs border-collapse">
        <thead class="bg-cypress/5 text-cypress font-semibold uppercase tracking-wider text-[11px] border-b border-cypress/10">
          <tr>
            <th class="p-3">Antecedent (Item Awal)</th>
            <th class="p-3">Consequent (Kombinasi Rekomendasi)</th>
            <th class="p-3">Support</th>
            <th class="p-3">Confidence</th>
            <th class="p-3">Lift Ratio</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-cypress/5">
          ${data.fp_growth.top_rules
            .map(
              (r) => `
            <tr class="hover:bg-cypress/5 transition">
              <td class="p-3 font-medium text-cypress">${r.antecedent.join(" + ")}</td>
              <td class="p-3 font-bold text-cypress">${r.consequent.join(" + ")}</td>
              <td class="p-3 font-mono">${(r.support * 100).toFixed(1)}%</td>
              <td class="p-3 font-mono font-bold text-emerald-700">${(r.confidence * 100).toFixed(1)}%</td>
              <td class="p-3 font-mono font-bold text-amber-gold">${r.lift.toFixed(2)}x</td>
            </tr>
          `
            )
            .join("")}
        </tbody>
      </table>
    `;
  } catch (err) {
    console.error("Failed to load analytics:", err);
  }
}

async function recalculateAnalytics() {
  try {
    const res = await fetch("/api/analytics/recalculate", { method: "POST" });
    const data = await res.json();
    if (res.ok && data.success) {
      showNotification("Model K-Means RFM berhasil dikalkulasi ulang!");
      loadAdminAnalytics();
    }
  } catch (err) {
    alert("Gagal menghitung ulang analitik.");
  }
}

// ============================================================================
// TOAST NOTIFICATION UTILITY
// ============================================================================
function showNotification(message, duration = 3000) {
  let toast = document.getElementById("app-toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "app-toast";
    toast.className =
      "fixed bottom-6 right-6 z-50 bg-cypress text-parchment-warm px-5 py-3 rounded-2xl shadow-2xl border border-amber-gold/30 text-xs font-semibold flex items-center space-x-2 transition-all transform translate-y-12 opacity-0 pointer-events-none";
    document.body.appendChild(toast);
  }

  toast.innerHTML = `<span>✨</span><span>${message}</span>`;
  toast.classList.remove("translate-y-12", "opacity-0", "pointer-events-none");

  setTimeout(() => {
    toast.classList.add("translate-y-12", "opacity-0", "pointer-events-none");
  }, duration);
}
