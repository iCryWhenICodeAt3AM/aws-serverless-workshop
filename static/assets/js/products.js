document.addEventListener("DOMContentLoaded", function() {
  fetch("/api/products")
    .then(response => response.json())
    .then(products => {
      const categories = ["All", ...new Set(products.map(product => product.category))];
      const categoryButtons = document.getElementById("category-buttons");
      let activeButton = null;

      categories.forEach(category => {
        const button = document.createElement("button");
        button.className = category === "All" ? "btn btn-primary category-item" : "btn btn-outline-secondary category-item";
        button.textContent = category;
        button.addEventListener("click", () => {
          displayMenu(category);
          if (activeButton) {
            activeButton.classList.remove("btn-primary");
            activeButton.classList.add("btn-outline-secondary");
          }
          button.classList.remove("btn-outline-secondary");
          button.classList.add("btn-primary");
          activeButton = button;
        });
        categoryButtons.appendChild(button);
        if (category === "All") {
          activeButton = button;
        }
      });

      displayMenu("All");

      function displayMenu(category) {
        const menu = document.getElementById("menu");
        menu.innerHTML = "";
        const filteredProducts = category === "All" ? products : products.filter(product => product.category === category);
        filteredProducts.forEach(product => {
          const brandImage = product.brand.toLowerCase().replace(/ /g, '') + ".jpg";
          const productCard = `
            <div class="col-md-6 mb-4">
              <div class="card food-item h-100" data-product-id="${product.product_id}">
                <div class="row g-0">
                  <div class="col-4">
                    <img src="../static/assets/${brandImage}" class="img-fluid rounded-start" alt="${product.item}" style="width: 100%; height: auto;">
                  </div>
                  <div class="col-8">
                    <div class="card-body">
                      <h5 class="card-title">${product.item}</h5>
                      <p class="card-text text-muted small">${product.product_description}</p>
                      <div class="d-flex justify-content-between align-items-center">
                        <span class="fw-bold">Php ${product.price}</span>
                        <button class="btn btn-sm btn-primary">Add</button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          `;
          menu.insertAdjacentHTML("beforeend", productCard);
        });
      }

      // Featured Restaurants
      const featuredRestaurants = document.getElementById("featured-restaurants");
      const restaurantDropdown = document.getElementById("restaurant-dropdown");
      const brands = [...new Set(products.map(product => product.brand))];
      brands.forEach(brand => {
        const brandProducts = products.filter(product => product.brand === brand);
        const categories = [...new Set(brandProducts.map(product => product.category))].slice(0, 3);
        const brandImage = brand.toLowerCase().replace(/ /g, '') + ".jpg";
        const restaurantCard = `
          <div class="col-md-4 col-sm-6">
            <div class="card restaurant-card h-100 shadow-sm">
              <a href="/restaurant.html?restaurant=${brand}">
                <img src="../static/assets/${brandImage}" class="card-img-top" alt="${brand}" style="width: 100%; height: auto;">
              </a>
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-2">
                  <h5 class="card-title mb-0">${brand}</h5>
                  <span class="badge bg-secondary">${brandProducts.length} items</span>
                </div>
                <p class="card-text text-muted small">${categories.join(' • ')}</p>
              </div>
            </div>
          </div>
        `;
        featuredRestaurants.insertAdjacentHTML("beforeend", restaurantCard);

        const dropdownItem = `
          <li><a class="dropdown-item" href="/restaurant.html?restaurant=${brand}">${brand}</a></li>
        `;
        restaurantDropdown.insertAdjacentHTML("beforeend", dropdownItem);
      });
    });
});
