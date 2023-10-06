window.history.scrollRestoration = 'manual';

document.addEventListener('DOMContentLoaded', function() {
  var nextPageLink = document.querySelector('.pagination__next');
  var prevPageLink = document.querySelector('.pagination__prev');
  var paginationLinks = document.querySelectorAll('.pagination__nav-item');
  var productList = document.querySelector('.product-list');
  var loadMoreButton = document.getElementById('load-more-button');
  var loadingMessage = document.getElementById('loading-message');
  var firstLoad = true;

  var currentPath = window.location.pathname;

  var savedProductList = localStorage.getItem('productList');
  var savedPath = localStorage.getItem('currentPath');
  if (savedProductList && savedPath === currentPath) {
    productList.innerHTML = savedProductList;
    if(nextPageLink) {
      nextPageLink.href = localStorage.getItem('nextPageLink');
    }
    firstLoad = false;
  } else if (savedPath && currentPath.includes('/collections/')) {
    localStorage.clear();
  }

  localStorage.setItem('currentPath', currentPath);

  function loadMoreProducts() {
  loadingMessage.style.display = 'block';
  return fetch(nextPageLink.href)
    .then(function(response) {
      return response.text();
    })
    .then(function(html) {
      var parser = new DOMParser();
      var doc = parser.parseFromString(html, 'text/html');
      var newProducts = doc.querySelectorAll('.product-item');

      newProducts.forEach(function(product) {
        productList.appendChild(product);
      });

      window.history.pushState(null, '', nextPageLink.href);

      nextPageLink = doc.querySelector('.pagination__next');
      prevPageLink = doc.querySelector('.pagination__prev');
      paginationLinks = doc.querySelectorAll('.pagination__nav-item');

      // Update the pagination
      var newPagination = doc.querySelector('#pagination');
      var pagination = document.getElementById('pagination');
      pagination.innerHTML = newPagination.innerHTML;

      if (nextPageLink) {
        if (firstLoad) {
          firstLoad = false;
          observer.observe(document.querySelector('.product-item:last-child'));
        } else {
          observer.observe(document.querySelector('.product-item:last-child'));
        }
      }

      loadingMessage.style.display = 'none';
    });
}


  function handleIntersect(entries, observer) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        observer.unobserve(entry.target);
        loadMoreProducts()
          .then(scrollToProduct);
      }
    });
  }

  function scrollToProduct() {
    var productId = window.location.hash.substring(1);
    if (productId) {
      var productItem = document.querySelector('.product-item[data-product-id="' + productId + '"]');
      if (productItem) {
        productItem.scrollIntoView();
        window.scrollBy(0, -200);
      }
    }
  }

  function reloadPageOnBack(event) {
    if (event.persisted) {
      var productId = window.location.hash.substring(1);
      if (productId) {
        localStorage.setItem('clickedProductId', productId);
      }
      var scrollPosition = localStorage.getItem('scrollPosition');
      if (scrollPosition) {
        window.scrollTo(0, scrollPosition);
      }
    }
  }

  if (nextPageLink) {
    var observer = new IntersectionObserver(handleIntersect, { rootMargin: '100px' });

    loadMoreButton.addEventListener('click', function() {
      loadMoreProducts()
        .then(function() {
          scrollToProduct();
          loadMoreButton.style.display = 'none';
          paginationLinks.forEach(function(link) {
            link.classList.add('is-active');
          });
        });

        // var pagination = document.getElementById('pagination');
        // pagination.style.display = 'none';
    });

  }

    productList.addEventListener('click', function(event) {
    var productLink = event.target.closest('.product-item a');
    if (productLink) {
      var productItem = productLink.closest('.product-item');
      if (productItem) {
        var productId = productItem.getAttribute('data-product-id');
        window.location.hash = productId;
        localStorage.setItem('clickedProductId', productId);
        localStorage.setItem('productList', productList.innerHTML);
        localStorage.setItem('scrollPosition', window.scrollY);  // Save the current scroll position
        if(nextPageLink) {
          localStorage.setItem('nextPageLink', nextPageLink.href);
        }
      }
    }
  });

  var allLinks = document.querySelectorAll('a');

  allLinks.forEach(function(link) {
    link.addEventListener('click', function(event) {
      if (!event.target.closest('.product-item a')) {
        localStorage.clear();
      }
    });
  });

  if (nextPageLink && prevPageLink) {
    nextPageLink.addEventListener('click', function() {
      localStorage.clear();
    });

    prevPageLink.addEventListener('click', function() {
      localStorage.clear();
    });

    paginationLinks.forEach(function(link) {
      link.addEventListener('click', function() {
        localStorage.clear();
      });
    });
  }

  scrollToProduct();
  window.addEventListener('pageshow', reloadPageOnBack);
});

