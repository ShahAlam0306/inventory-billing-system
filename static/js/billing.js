let cart = {}; // product_id -> {name, price, qty, stock}

function addToCart(id, name, price, stock) {
  if (!cart[id]) cart[id] = { name, price, qty: 0, stock };
  if (cart[id].qty >= stock) { alert('Not enough stock'); return; }
  cart[id].qty += 1;
  renderCart();
}

function changeQty(id, delta) {
  cart[id].qty += delta;
  if (cart[id].qty <= 0) delete cart[id];
  renderCart();
}

function removeFromCart(id) {
  delete cart[id];
  renderCart();
}

function renderCart() {
  const tbody = document.getElementById('cartTable');
  tbody.innerHTML = '';
  let total = 0;
  for (const id in cart) {
    const item = cart[id];
    const subtotal = item.qty * item.price;
    total += subtotal;
    tbody.innerHTML += `<tr>
      <td>${item.name}</td>
      <td>
        <button class="btn btn-sm btn-outline-secondary" onclick="changeQty(${id}, -1)">-</button>
        ${item.qty}
        <button class="btn btn-sm btn-outline-secondary" onclick="changeQty(${id}, 1)">+</button>
      </td>
      <td>₹${subtotal.toFixed(2)}</td>
      <td><button class="btn btn-sm btn-outline-danger" onclick="removeFromCart(${id})">x</button></td>
    </tr>`;
  }
  document.getElementById('cartTotal').textContent = total.toFixed(2);
}

function renderInvoice(data) {
  document.getElementById('invBillNo').textContent = `Bill #${data.bill_id}`;
  document.getElementById('invDate').textContent = data.date;
  document.getElementById('invCashier').textContent = data.cashier;
  document.getElementById('invTotal').textContent = data.total.toFixed(2);

  const itemsBody = document.getElementById('invItems');
  itemsBody.innerHTML = '';
  data.items.forEach(item => {
    itemsBody.innerHTML += `<tr>
      <td>${item.name}</td>
      <td class="num">${item.qty}</td>
      <td class="num">₹${item.price.toFixed(2)}</td>
      <td class="num">₹${item.subtotal.toFixed(2)}</td>
    </tr>`;
  });

  document.getElementById('downloadInvoiceBtn').href = data.pdf_url;

  const section = document.getElementById('invoiceSection');
  section.classList.remove('d-none');
  section.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function checkout() {
  const items = Object.entries(cart).map(([id, item]) => ({ product_id: parseInt(id), qty: item.qty }));
  if (items.length === 0) { alert('Cart is empty'); return; }

  const checkoutUrl = document.getElementById('billingRoot').dataset.checkoutUrl;
  const checkoutBtn = document.getElementById('checkoutBtn');
  checkoutBtn.disabled = true;
  checkoutBtn.textContent = 'Generating…';

  fetch(checkoutUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ items })
  })
    .then(r => r.json())
    .then(data => {
      checkoutBtn.disabled = false;
      checkoutBtn.textContent = 'Generate Bill';

      if (data.error) {
        document.getElementById('checkoutMsg').innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        return;
      }

      // Update stock numbers on the product list without a full page reload,
      // so the invoice below stays visible.
      for (const id in cart) {
        const row = document.querySelector(`#productTable tr[data-id="${id}"]`);
        if (row) {
          const newStock = row.dataset.stock - cart[id].qty;
          row.dataset.stock = newStock;
          row.querySelector('.stock-cell').textContent = newStock;
        }
      }

      document.getElementById('checkoutMsg').innerHTML =
        `<div class="alert alert-success">Bill #${data.bill_id} created — Total ₹${data.total.toFixed(2)}</div>`;

      renderInvoice(data);

      cart = {};
      renderCart();
    })
    .catch(() => {
      checkoutBtn.disabled = false;
      checkoutBtn.textContent = 'Generate Bill';
      document.getElementById('checkoutMsg').innerHTML =
        `<div class="alert alert-danger">Something went wrong generating the bill. Please try again.</div>`;
    });
}

document.addEventListener('DOMContentLoaded', () => {
  // Event-delegated Add button (rows now carry data-id/price/stock instead of
  // inline onclick params, so stock can be updated live after checkout).
  document.getElementById('productTable').addEventListener('click', e => {
    const btn = e.target.closest('.add-btn');
    if (!btn) return;
    const row = btn.closest('tr');
    addToCart(
      parseInt(row.dataset.id),
      row.querySelector('td').textContent,
      parseFloat(row.dataset.price),
      parseInt(row.dataset.stock)
    );
  });

  document.getElementById('checkoutBtn').addEventListener('click', checkout);

  document.getElementById('printInvoiceBtn').addEventListener('click', () => window.print());

  document.getElementById('newBillBtn').addEventListener('click', () => {
    document.getElementById('invoiceSection').classList.add('d-none');
    document.getElementById('checkoutMsg').innerHTML = '';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  document.getElementById('search').addEventListener('input', e => {
    const q = e.target.value.toLowerCase();
    document.querySelectorAll('#productTable tr').forEach(row => {
      row.style.display = row.dataset.name.includes(q) ? '' : 'none';
    });
  });
});
