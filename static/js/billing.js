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

function checkout() {
  const items = Object.entries(cart).map(([id, item]) => ({ product_id: parseInt(id), qty: item.qty }));
  if (items.length === 0) { alert('Cart is empty'); return; }

  const checkoutUrl = document.getElementById('billingRoot').dataset.checkoutUrl;

  fetch(checkoutUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ items })
  })
    .then(r => r.json())
    .then(data => {
      if (data.error) {
        document.getElementById('checkoutMsg').innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        return;
      }
      document.getElementById('checkoutMsg').innerHTML =
        `<div class="alert alert-success">Bill #${data.bill_id} created — Total ₹${data.total}</div>`;
      cart = {};
      renderCart();
      setTimeout(() => location.reload(), 1200); // refresh stock numbers
    });
}

document.getElementById('search').addEventListener('input', e => {
  const q = e.target.value.toLowerCase();
  document.querySelectorAll('#productTable tr').forEach(row => {
    row.style.display = row.dataset.name.includes(q) ? '' : 'none';
  });
});
