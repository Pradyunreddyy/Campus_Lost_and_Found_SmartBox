const API = "https://campus-lost-and-found-smartbox.onrender.com/api";
const $ = (id) => document.getElementById(id);
let allItems = [];

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Something went wrong");
  return data;
}
function escapeHtml(value = "") {
  return String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}
function statusClass(status) {
  return status === "Lost" ? "lost" : status === "Claimed" ? "claimed" : status === "In Smart Box" ? "inbox" : "";
}
function renderStats(items) {
  $("totalCount").textContent = items.length;
  $("waitingCount").textContent = items.filter(x => x.status === "Found" || x.status === "In Smart Box").length;
  $("returnedCount").textContent = items.filter(x => x.status === "Claimed").length;
  $("boxCount").textContent = items.filter(x => x.status === "In Smart Box").length;
}
function renderItems() {
  const search = $("searchInput").value.toLowerCase();
  const status = $("statusFilter").value;
  const filtered = allItems.filter(item => {
    const matches = [item.name, item.location, item.rfid, item.category].join(" ").toLowerCase().includes(search);
    return matches && (!status || item.status === status);
  });
  $("itemsTable").innerHTML = filtered.length ? filtered.map(item => `
    <tr>
      <td>${escapeHtml(item.name)}<br><span style="font-weight:400;color:#a0a3b2">${escapeHtml(item.category || item.type || "Other")}</span></td>
      <td>${escapeHtml(item.location || "—")}</td>
      <td>${escapeHtml(item.date || "—")}</td>
      <td><span class="pill ${statusClass(item.status)}">${escapeHtml(item.status)}</span></td>
      <td>${escapeHtml(item.rfid || "—")}</td>
      <td>${item.status !== "Claimed" ? `<button class="small-action" data-claim="${escapeHtml(item.id)}">Mark claimed</button>` : "✓"}</td>
    </tr>`).join("") : `<tr><td colspan="6" class="empty">No items found. Report an item to get started.</td></tr>`;
}
async function loadItems() {
  try {
    const data = await request("/items");
    allItems = data.items || [];
    renderStats(allItems); renderItems();
  } catch (error) {
    $("itemsTable").innerHTML = `<tr><td colspan="6" class="empty">${escapeHtml(error.message)}. Start the backend server and refresh.</td></tr>`;
  }
}
$("itemForm").addEventListener("submit", async event => {
  event.preventDefault();
  const form = new FormData(event.target);
  const item = Object.fromEntries(form.entries());
  try {
    await request("/items", { method: "POST", body: JSON.stringify(item) });
    event.target.reset();
    $("formMessage").textContent = "Item record saved successfully.";
    loadItems();
  } catch (error) { $("formMessage").textContent = error.message; }
});
$("itemsTable").addEventListener("click", async event => {
  const id = event.target.dataset.claim;
  if (!id) return;
  try { await request(`/items/${id}`, { method: "PATCH", body: JSON.stringify({status:"Claimed"}) }); loadItems(); }
  catch (error) { alert(error.message); }
});
$("searchInput").addEventListener("input", renderItems);
$("statusFilter").addEventListener("change", renderItems);
$("addTop").addEventListener("click", () => $("register").scrollIntoView({behavior:"smooth"}));
$("viewAll").addEventListener("click", () => { $("searchInput").value = ""; $("statusFilter").value = ""; renderItems(); });

async function scan(action) {
  const tag = $("rfidTag").value.trim();
  if (!tag) { $("rfidMessage").hidden = false; $("rfidMessage").textContent = "Enter an RFID tag ID first."; return; }
  try {
    const result = await request("/rfid/scan", { method:"POST", body:JSON.stringify({tag, action}) });
    $("rfidMessage").hidden = false;
    $("rfidMessage").textContent = result.message;
    $("oledText").textContent = result.display || "SCAN COMPLETE";
    $("oledSub").textContent = `Tag: ${tag}`;
    $("deviceState").textContent = "Demo event recorded";
    loadItems();
  } catch (error) {
    $("rfidMessage").hidden = false; $("rfidMessage").textContent = error.message;
    $("oledText").textContent = "SCAN FAILED";
  }
}
$("rfidForm").addEventListener("submit", e => { e.preventDefault(); scan("checkin"); });
$("checkoutBtn").addEventListener("click", () => scan("checkout"));
loadItems();
