document.addEventListener("DOMContentLoaded", function() {
  let cart = JSON.parse(sessionStorage.getItem('cart')) || [];
  const userId = sessionStorage.getItem('user_id') || 'default_user'; // Replace with actual user ID logic

  const pubnub = new PubNub({
    subscribeKey: PUBNUB_SUBSCRIBE_KEY,
    publishKey: PUBNUB_PUBLISH_KEY,
    uuid: userId
  });

  pubnub.addListener({
    message: function(event) {
      if (event.message.action === 'add_to_cart' && event.message.status === 'success') {
        fetchCart();
      }
    }
  });

  pubnub.subscribe({
    channels: [userId]
  });

  function updateCart() {
    const cartContainer = document.getElementById('cart');
    cartContainer.innerHTML = '';
    let total = 0;

    if (Array.isArray(cart)) {
      cart.forEach(item => {
        const cartItem = `
          <div class="cart-item py-3">
            <div class="d-flex justify-content-between">
              <div>
                <h6 class="mb-1">${item.quantity}x ${item.item}</h6>
                <p class="text-muted small mb-0">${item.description}</p>
              </div>
              <div class="text-end">
                <span class="fw-bold">$${(item.price / 100).toFixed(2)}</span>
                <div class="btn-group btn-group-sm mt-1">
                  <button class="btn btn-outline-secondary" onclick="updateQuantity('${item.product_id}', -1)">-</button>
                  <button class="btn btn-outline-secondary" onclick="updateQuantity('${item.product_id}', 1)">+</button>
                </div>
              </div>
            </div>
          </div>
        `;
        cartContainer.insertAdjacentHTML('beforeend', cartItem);
        total += item.price * item.quantity;
      });
    }

    document.querySelector('.card-footer .fw-bold:last-child').textContent = `$${(total / 100).toFixed(2)}`;
    sessionStorage.setItem('cart', JSON.stringify(cart));
  }

  function addToCart(product) {
    const quantity = parseInt(prompt("Enter quantity:", "1"));
    if (isNaN(quantity) || quantity <= 0) {
      alert("Invalid quantity. Please enter a positive number.");
      return;
    }
    product.quantity = quantity;

    fetch('/add_to_cart', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ user_id: userId, product: product })
    })
    .then(response => response.json())
    .then(updatedCart => {
      cart = updatedCart;
      updateCart();
    })
    .catch(error => console.error('Error adding to cart:', error));
  }

  function updateQuantity(productId, change) {
    const product = cart.find(item => item.product_id === productId);
    if (product) {
      product.quantity += change;
      if (product.quantity <= 0) {
        cart = cart.filter(item => item.product_id !== productId);
      }
      updateCart();
    }
  }

  function fetchCart() {
    fetch(`/get_cart/${userId}`)
      .then(response => response.json())
      .then(fetchedCart => {
        cart = fetchedCart;
        updateCart();
      })
      .catch(error => console.error('Error fetching cart:', error));
  }

  // Attach event listeners to Add buttons
  document.addEventListener('click', function(event) {
    if (event.target.classList.contains('btn-primary') && event.target.textContent === 'Add') {
      const productCard = event.target.closest('.card');
      const product = {
        product_id: productCard.dataset.productId,
        item: productCard.querySelector('.card-title').textContent,
        description: productCard.querySelector('.card-text').textContent,
        price: parseFloat(productCard.querySelector('.fw-bold').textContent.replace('$', '')) * 100
      };
      addToCart(product);
    }
  });

  window.updateQuantity = updateQuantity; // Make updateQuantity function globally accessible

  fetchCart(); // Fetch the cart when the page loads
});
