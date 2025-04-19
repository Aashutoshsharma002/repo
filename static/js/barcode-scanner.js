/**
 * Barcode Scanner Utility
 * For Jockey Warehouse Management System
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize scanner functionality
    initBarcodeScanner();
});

/**
 * Initialize barcode scanner functionality
 */
function initBarcodeScanner() {
    const barcodeInput = document.getElementById('barcode-input');
    
    if (!barcodeInput) return;
    
    // Set focus to barcode input when page loads
    barcodeInput.focus();
    
    // Handle barcode input on Enter key
    barcodeInput.addEventListener('keydown', function(e) {
        // Check if Enter key is pressed
        if (e.key === 'Enter') {
            e.preventDefault();
            processBarcode(this.value);
        }
    });
    
    // Also listen for blur events from rapid scanning 
    // Most barcode scanners will emit an Enter key after scanning
    let lastInput = '';
    barcodeInput.addEventListener('input', function(e) {
        lastInput = this.value;
        
        // If a barcode scanner is used, it typically inputs all characters very quickly
        clearTimeout(this.timeout);
        this.timeout = setTimeout(() => {
            // If the value hasn't changed in 50ms and contains data, we assume it's complete
            if (this.value === lastInput && this.value.trim() !== '') {
                // Only auto-submit if it looks like a barcode (longer than 8 chars)
                if (this.value.trim().length >= 8) {
                    processBarcode(this.value);
                }
            }
        }, 50);
    });
    
    // Reset button event handler
    const resetButton = document.getElementById('reset-scan');
    if (resetButton) {
        resetButton.addEventListener('click', function() {
            clearScanResults();
            barcodeInput.value = '';
            barcodeInput.focus();
        });
    }
    
    // Re-focus input when clicking anywhere in the scanner area
    const scannerArea = document.querySelector('.barcode-scanner');
    if (scannerArea) {
        scannerArea.addEventListener('click', function(e) {
            // Don't re-focus if clicking on a button or input
            if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'INPUT') {
                barcodeInput.focus();
            }
        });
    }
    
    // Keep focus on input field when the window regains focus
    window.addEventListener('focus', function() {
        if (document.activeElement !== barcodeInput) {
            barcodeInput.focus();
        }
    });
}

/**
 * Process the scanned barcode
 * @param {string} barcode - The scanned barcode
 */
function processBarcode(barcode) {
    if (!barcode || barcode.trim() === '') {
        showScanError('Please scan or enter a barcode');
        return;
    }
    
    // Show loading indicator
    showScanLoading();
    
    // Create form data
    const formData = new FormData();
    formData.append('barcode', barcode.trim());
    
    // Send request to server
    fetch('/products/search-by-barcode', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            displayProductInfo(data.product);
            
            // Check if we need to populate inventory form
            populateInventoryForm(data.product);
        } else {
            showScanError(data.message || 'Product not found');
        }
    })
    .catch(error => {
        console.error('Error searching by barcode:', error);
        showScanError('Error searching for product. Please try again.');
    })
    .finally(() => {
        // Hide loading indicator
        hideScanLoading();
    });
}

/**
 * Display product information after successful scan
 * @param {Object} product - The product data
 */
function displayProductInfo(product) {
    const resultContainer = document.getElementById('scan-result');
    if (!resultContainer) return;
    
    // Format price
    const formattedPrice = new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(product.price);
    
    // Determine stock status
    let stockStatusClass = 'bg-success';
    let stockStatusText = 'In Stock';
    
    if (product.quantity <= 0) {
        stockStatusClass = 'bg-danger';
        stockStatusText = 'Out of Stock';
    } else if (product.quantity < 10) {
        stockStatusClass = 'bg-warning';
        stockStatusText = 'Low Stock';
    }
    
    // Create product card
    resultContainer.innerHTML = `
        <div class="card mb-3 border-primary">
            <div class="card-header bg-light">
                <h5 class="mb-0"><i class="fas fa-box me-2"></i>Product Found</h5>
            </div>
            <div class="row g-0">
                <div class="col-md-4">
                    <div class="product-image p-2" style="height: 200px; background-image: url('${product.image || '/static/images/no-image.svg'}'); background-size: contain; background-position: center; background-repeat: no-repeat;"></div>
                </div>
                <div class="col-md-8">
                    <div class="card-body">
                        <h5 class="card-title">${product.name}</h5>
                        <p class="card-text">SKU: <strong>${product.sku}</strong></p>
                        <p class="card-text">Barcode: <strong>${product.barcode}</strong></p>
                        <p class="card-text">
                            Status: <span class="badge ${stockStatusClass}">${stockStatusText}</span>
                            <span class="ms-2">Quantity: <strong>${product.quantity}</strong></span>
                        </p>
                        <p class="card-text">Price: <strong>${formattedPrice}</strong></p>
                        <div class="mt-3">
                            <a href="${product.url}" class="btn btn-primary">
                                <i class="fas fa-eye me-2"></i>View Details
                            </a>
                            <a href="/inventory/stock-in?product_id=${product.id}" class="btn btn-success ms-2">
                                <i class="fas fa-plus-circle me-2"></i>Stock In
                            </a>
                            <a href="/inventory/stock-out?product_id=${product.id}" class="btn btn-danger ms-2">
                                <i class="fas fa-minus-circle me-2"></i>Stock Out
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    resultContainer.style.display = 'block';
}

/**
 * Populate inventory form with product data
 * @param {Object} product - The product data
 */
function populateInventoryForm(product) {
    // Check if product ID field exists (we're on an inventory form)
    const productIdField = document.getElementById('product_id');
    if (!productIdField) return;
    
    // Set field values
    productIdField.value = product.id;
    
    // Update product info display if it exists
    const productInfoContainer = document.getElementById('product-info');
    if (productInfoContainer) {
        productInfoContainer.innerHTML = `
            <div class="alert alert-info">
                <strong>${product.name}</strong> (SKU: ${product.sku})
                <br>Current Stock: ${product.quantity}
            </div>
        `;
        productInfoContainer.style.display = 'block';
    }
    
    // Set focus to quantity field if it exists
    const quantityField = document.getElementById('quantity');
    if (quantityField) {
        quantityField.focus();
    }
}

/**
 * Show error message
 * @param {string} message - The error message
 */
function showScanError(message) {
    const errorContainer = document.getElementById('scan-error');
    if (!errorContainer) return;
    
    errorContainer.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-exclamation-circle me-2 fs-4"></i>
            <div>
                <strong>Barcode Error</strong><br>
                ${message}
            </div>
        </div>
        <div class="mt-2">
            <small>Please try again or check if the barcode is registered in the system.</small>
        </div>
    `;
    errorContainer.style.display = 'block';
    
    // Hide after 7 seconds
    setTimeout(() => {
        errorContainer.style.display = 'none';
    }, 7000);
}

/**
 * Show loading indicator
 */
function showScanLoading() {
    const loadingIndicator = document.getElementById('scan-loading');
    if (loadingIndicator) {
        loadingIndicator.style.display = 'block';
    }
}

/**
 * Hide loading indicator
 */
function hideScanLoading() {
    const loadingIndicator = document.getElementById('scan-loading');
    if (loadingIndicator) {
        loadingIndicator.style.display = 'none';
    }
}

/**
 * Clear scan results
 */
function clearScanResults() {
    const resultContainer = document.getElementById('scan-result');
    const errorContainer = document.getElementById('scan-error');
    const productInfoContainer = document.getElementById('product-info');
    
    if (resultContainer) {
        resultContainer.innerHTML = '';
        resultContainer.style.display = 'none';
    }
    
    if (errorContainer) {
        errorContainer.textContent = '';
        errorContainer.style.display = 'none';
    }
    
    if (productInfoContainer) {
        productInfoContainer.innerHTML = '';
        productInfoContainer.style.display = 'none';
    }
    
    // Reset form fields if they exist
    const productIdField = document.getElementById('product_id');
    if (productIdField) {
        productIdField.value = '';
    }
}
