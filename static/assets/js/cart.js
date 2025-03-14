// Ensure PubNub is included
// <script src="https://cdn.pubnub.com/sdk/javascript/pubnub.4.29.9.min.js"></script>

document.addEventListener("DOMContentLoaded", function() {
  let cart = [];
  const userId = sessionStorage.getItem('user_id') || 'default_user'; // Replace with actual user ID logic

  function updateCart() {
    const cartContainer = document.getElementById('cart');
    cartContainer.innerHTML = '';
    let total = 0;

    if (Array.isArray(cart)) {
      cart.forEach(item => {
        const itemTotal = item.quantity * item.price;
        const cartItem = `
          <div class="cart-item py-3">
            <div class="d-flex justify-content-between">
              <div>
                <h6 class="mb-1">${item.quantity}x ${item.item}</h6>
                <p class="text-muted small mb-0">${item.description}</p>
              </div>
              <div class="text-end">
                <span class="fw-bold">Php ${(itemTotal).toFixed(2)}</span>
                <div class="btn-group btn-group-sm mt-1">
                  <button class="btn btn-outline-secondary" onclick="updateQuantity('${item.product_id}', -1)">-</button>
                  <button class="btn btn-outline-secondary" onclick="updateQuantity('${item.product_id}', 1)">+</button>
                </div>
              </div>
            </div>
          </div>
        `;
        cartContainer.insertAdjacentHTML('beforeend', cartItem);
        total += itemTotal;
      });
    }

    document.querySelector('.card-footer .fw-bold:last-child').textContent = `Php ${(total).toFixed(2)}`;
    sessionStorage.setItem('cart', JSON.stringify(cart));
  }

  function addToCart(product) {
    const quantity = parseInt(prompt("Enter quantity:", "1"));
    if (isNaN(quantity) || quantity <= 0) {
      alert("Invalid quantity. Please enter a positive number.");
      return;
    }
    product.quantity = quantity;

    fetch(`/api/cart/${userId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(product)
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`Server error: ${response.statusText}`);
      }
      return response.json();
    })
    .then(() => {
      // Fetch the updated cart and reload the display
      fetchCart();
    })
    .catch(error => {
      console.error('Error adding to cart:', error);
      alert('An error occurred while adding the item to the cart. Please try again.');
    });
  }

  function updateQuantity(productId, change) {
    const product = cart.find(item => item.product_id === productId);
    if (product) {
      product.quantity = parseInt(product.quantity) + change;
      if (product.quantity <= 0) {
        cart = cart.filter(item => item.product_id !== productId);
      }
      updateCart();
    }
  }

  function fetchCart() {
    fetch(`/api/cart/${userId}`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`Server error: ${response.statusText}`);
        }
        return response.json();
      })
      .then(data => {
        cart = data.cart || [];
        updateCart();
      })
      .catch(error => {
        console.error('Error fetching cart:', error);
        alert('An error occurred while fetching the cart. Please try again.');
      });
  }

  // Attach event listeners to Add buttons
  document.addEventListener('click', function(event) {
    if (event.target.classList.contains('btn-primary') && event.target.textContent === 'Add') {
      const productCard = event.target.closest('.card');
      const product = {
        product_id: productCard.dataset.productId,
        item: productCard.querySelector('.card-title').textContent,
        description: productCard.querySelector('.card-text').textContent,
        price: parseFloat(productCard.querySelector('.fw-bold').textContent.replace('Php', ''))
      };
      addToCart(product);
    }
  });

  window.updateQuantity = updateQuantity; // Make updateQuantity function globally accessible

  fetchCart(); // Fetch the cart when the page loads
});
