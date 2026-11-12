const $ = (id) => document.getElementById(id);
const aiAvailable = document.body.dataset.aiAvailable === "true";
let products = [];
let toastTimer;

function money(value) {
  return new Intl.NumberFormat(undefined, { style: "currency", currency: "USD" }).format(Number(value || 0));
}
function escapeText(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);
}
function showToast(message, error = false) {
  const toast = $("toast");
  toast.textContent = message;
  toast.className = `toast show${error ? " error" : ""}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.className = "toast", 2800);
}
async function api(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok || data.success === false) throw new Error(data.error || "Something went wrong.");
  return data;
}
function statusLabel(status) {
  return ({ in_stock: "In stock", low_stock: "Low stock", out_of_stock: "Out of stock" })[status] || status;
}
function renderProducts(list) {
  $("resultCount").textContent = `${list.length} product${list.length === 1 ? "" : "s"}`;
  const body = $("productTableBody");
  if (!list.length) {
    body.innerHTML = `<tr><td colspan="6" class="empty-state">No products found. Add a product to get started.</td></tr>`;
    return;
  }
  body.innerHTML = list.map(p => `
    <tr>
      <td><div class="product-cell"><div class="product-avatar">${escapeText(p.name.slice(0,1).toUpperCase())}</div><div><strong>${escapeText(p.name)}</strong><small>${escapeText(p.product_id)}${p.product_type === "perishable" ? " · Perishable" : ""}</small></div></div></td>
      <td>${escapeText(p.category)}</td><td>${money(p.price)}</td>
      <td><span class="quantity">${p.quantity}</span></td>
      <td><span class="status status-${p.stock_status}">${statusLabel(p.stock_status)}</span></td>
      <td><div class="row-actions"><button class="icon-button" title="Edit" data-action="edit" data-id="${escapeText(p.product_id)}">✎</button><button class="icon-button" title="Delete" data-action="delete" data-id="${escapeText(p.product_id)}">×</button></div></td>
    </tr>`).join("");
}
function renderAttention() {
  const attention = products.filter(p => p.stock_status !== "in_stock");
  $("attentionList").innerHTML = attention.length ? attention.slice(0,5).map(p => `
    <div class="attention-item">
      <div class="attention-mark ${p.stock_status === "out_of_stock" ? "out" : ""}">${p.stock_status === "out_of_stock" ? "!" : "⌁"}</div>
      <div><strong>${escapeText(p.name)}</strong><small>${p.stock_status === "out_of_stock" ? "No units available" : `Reorder level: ${p.reorder_level}`}</small></div>
      <span class="attention-qty">${p.quantity} left</span>
    </div>`).join("") : `<div class="empty-mini">All products are above their reorder levels. Nice work!</div>`;
}
async function refresh() {
  const [productData, statsData] = await Promise.all([api("/api/products"), api("/api/stats")]);
  products = productData.products;
  renderProducts(products);
  renderAttention();
  const s = statsData.stats;
  $("totalProducts").textContent = s.total_products.toLocaleString();
  $("totalUnits").textContent = s.total_units.toLocaleString();
  $("inventoryValue").textContent = money(s.inventory_value);
  $("lowStockCount").textContent = s.low_stock_count.toLocaleString();
  $("outStockCount").textContent = s.out_of_stock_count.toLocaleString();
}
function openModal(product = null) {
  $("productForm").reset();
  $("productId").value = product?.product_id || "";
  $("modalTitle").textContent = product ? "Edit product" : "Add a product";
  $("productName").value = product?.name || "";
  $("productCategory").value = product?.category || "";
  $("productPrice").value = product?.price ?? "";
  $("productQuantity").value = product?.quantity ?? "";
  $("productReorder").value = product?.reorder_level ?? 5;
  $("productType").value = product?.product_type || "standard";
  $("productExpiry").value = product?.expiry_date || "";
  $("productDescription").value = product?.description || "";
  toggleExpiry();
  $("productModal").classList.add("open");
  $("productModal").setAttribute("aria-hidden", "false");
  $("productName").focus();
}
function closeModal() {
  $("productModal").classList.remove("open");
  $("productModal").setAttribute("aria-hidden", "true");
}
function toggleExpiry() {
  const perishable = $("productType").value === "perishable";
  document.querySelector(".expiry-field").classList.toggle("hidden", !perishable);
  $("productExpiry").required = perishable;
}
async function runAI(endpoint, title, payload = {}) {
  $("aiOutput").innerHTML = `<div class="output-placeholder"><span>◌</span><div><strong>${title} is working…</strong><p>Reviewing your current inventory data.</p></div></div>`;
  try {
    const data = await api(endpoint, { method: "POST", body: JSON.stringify(payload) });
    $("aiOutput").innerHTML = `<div class="ai-result"><h4>✳ ${escapeText(title)}</h4>${escapeText(data.answer).replace(/\n/g, "<br>")}</div>`;
  } catch (error) {
    $("aiOutput").innerHTML = `<div class="ai-result"><h4>AI response unavailable</h4>${escapeText(error.message)}</div>`;
  }
}
$("todayLabel").textContent = new Intl.DateTimeFormat(undefined, { weekday: "short", month: "short", day: "numeric", year: "numeric" }).format(new Date());
$("aiStatus").classList.toggle("offline", !aiAvailable);
$("aiStatus").innerHTML = aiAvailable ? "<i></i> Groq connected" : "<i></i> AI not configured";
if (!aiAvailable) $("aiStatus").classList.add("offline");

$("topAddBtn").addEventListener("click", () => openModal());
$("addProductBtn").addEventListener("click", () => openModal());
$("closeModal").addEventListener("click", closeModal);
$("cancelModal").addEventListener("click", closeModal);
$("productType").addEventListener("change", toggleExpiry);
$("productModal").addEventListener("click", e => { if (e.target === $("productModal")) closeModal(); });
$("productForm").addEventListener("submit", async e => {
  e.preventDefault();
  const id = $("productId").value;
  const payload = {
    name: $("productName").value.trim(),
    category: $("productCategory").value.trim(),
    price: $("productPrice").value,
    quantity: $("productQuantity").value,
    reorder_level: $("productReorder").value,
    product_type: $("productType").value,
    expiry_date: $("productExpiry").value,
    description: $("productDescription").value.trim()
  };
  try {
    await api(id ? `/api/products/${encodeURIComponent(id)}` : "/api/products", {
      method: id ? "PUT" : "POST", body: JSON.stringify(payload)
    });
    closeModal();
    await refresh();
    showToast(id ? "Product updated successfully." : "Product added successfully.");
  } catch (error) { showToast(error.message, true); }
});
$("productTableBody").addEventListener("click", async e => {
  const button = e.target.closest("button[data-action]");
  if (!button) return;
  const product = products.find(p => p.product_id === button.dataset.id);
  if (button.dataset.action === "edit" && product) openModal(product);
  if (button.dataset.action === "delete" && product && confirm(`Delete "${product.name}" from inventory?`)) {
    try {
      await api(`/api/products/${encodeURIComponent(product.product_id)}`, { method: "DELETE" });
      await refresh(); showToast("Product deleted.");
    } catch (error) { showToast(error.message, true); }
  }
});
let searchTimeout;
$("searchInput").addEventListener("input", () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(async () => {
    try {
      const data = await api(`/api/products?q=${encodeURIComponent($("searchInput").value)}`);
      renderProducts(data.products);
    } catch (error) { showToast(error.message, true); }
  }, 180);
});
$("viewLowStockBtn").addEventListener("click", () => {
  $("searchInput").value = "";
  renderProducts(products.filter(p => p.stock_status !== "in_stock"));
  $("products").scrollIntoView({ behavior: "smooth" });
});
$("analyzeBtn").addEventListener("click", () => runAI("/api/ai/analyze", "Inventory analysis"));
$("reorderBtn").addEventListener("click", () => runAI("/api/ai/reorder", "Smart reorder suggestions"));
$("assistantForm").addEventListener("submit", e => {
  e.preventDefault();
  const question = $("assistantQuestion").value.trim();
  if (!question) return;
  runAI("/api/ai/ask", "Inventory assistant", { question });
  $("assistantQuestion").value = "";
});
$("generateDescriptionBtn").addEventListener("click", async () => {
  const name = $("productName").value.trim();
  const category = $("productCategory").value.trim();
  if (!name || !category) { showToast("Enter a product name and category first.", true); return; }
  const button = $("generateDescriptionBtn");
  button.disabled = true; button.textContent = "Generating…";
  try {
    const data = await api("/api/ai/description", {
      method: "POST",
      body: JSON.stringify({ name, category, details: $("productDescription").value.trim() })
    });
    $("productDescription").value = data.answer;
    showToast("Description generated.");
  } catch (error) { showToast(error.message, true); }
  finally { button.disabled = false; button.textContent = "✧ Generate description with AI"; }
});
refresh().catch(error => showToast(error.message, true));
