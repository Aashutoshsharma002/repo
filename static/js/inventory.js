/**
 * Inventory Management Scripts
 * For Puma Warehouse Management System
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize datepickers
    initDatepickers();
    
    // Initialize barcode scanner for inventory
    initInventoryBarcodeScan();
});

/**
 * Initialize date picker elements
 */
function initDatepickers() {
    // Find all date picker inputs
    const datepickers = document.querySelectorAll('.datepicker');
    
    datepickers.forEach(picker => {
        // Initialize with a date selector
        picker.type = 'date';
    });
}

/**
 * Initialize barcode scanning for inventory operations
 */
function initInventoryBarcodeScan() {
    const barcodeInput = document.getElementById('inventory-barcode-input');
    
    if (!barcodeInput) return;
    
    // Set focus to barcode input when page loads
    barcodeInput.focus();
    
    // Handle barcode input
    barcodeInput.addEventListener('keydown', function(e) {
        // Check if Enter key is pressed
        if (e.key === 'Enter') {
            e.preventDefault();
            processInventoryBarcode(this.value);
        }
    });
    
    // Reset button event handler
    const resetButton = document.getElementById('reset-inventory-scan');
    if (resetButton) {
        resetButton.addEventListener('click', function() {
            clearInventoryForm();
            barcodeInput.value = '';
            barcodeInput.focus();
        });
    }
}

/**
 * Process barcode for inventory operations
 * @param {string} barcode - The scanned barcode
 */
function processInventoryBarcode(barcode) {
    if (!barcode || barcode.trim() === '') {
        showInventoryError('Please scan or enter a barcode');
        return;
    }
    
    // Show loading indicator
    const loadingElement = document.getElementById('inventory-loading');
    if (loadingElement) {
        loadingElement.style.display = 'block';
    }
    
    // Create form data
    const formData = new FormData();
    formData.append('barcode', barcode.trim());
    
    // Send request to server
    fetch('/inventory/get-product', {
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
            populateInventoryForm(data.product);
        } else {
            showInventoryError(data.message || 'Product not found');
        }
    })
    .catch(error => {
        console.error('Error searching by barcode:', error);
        showInventoryError('Error searching for product. Please try again.');
    })
    .finally(() => {
        // Hide loading indicator
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    });
}

/**
 * Populate inventory form with product data
 * @param {Object} product - The product data
 */
function populateInventoryForm(product) {
    // Set product ID in form
    const productIdField = document.getElementById('product_id');
    if (productIdField) {
        productIdField.value = product.id;
    }
    
    // Update product info display
    const productInfoContainer = document.getElementById('product-info');
    if (productInfoContainer) {
        productInfoContainer.innerHTML = `
            <div class="card mb-3">
                <div class="row g-0">
                    <div class="col-md-4">
                        <img src="${product.image || '/static/images/no-image.svg'}" class="img-fluid rounded-start product-detail-image" alt="${product.name}">
                    </div>
                    <div class="col-md-8">
                        <div class="card-body">
                            <h5 class="card-title">${product.name}</h5>
                            <p class="card-text">SKU: ${product.sku}</p>
                            <p class="card-text">Current Stock: <span class="${product.quantity > 10 ? 'status-in-stock' : (product.quantity > 0 ? 'status-low-stock' : 'status-out-of-stock')}">${product.quantity}</span></p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        productInfoContainer.style.display = 'block';
    }
    
    // Show form
    const formContainer = document.getElementById('inventory-form-container');
    if (formContainer) {
        formContainer.style.display = 'block';
    }
    
    // Set focus to quantity field
    const quantityField = document.getElementById('quantity');
    if (quantityField) {
        quantityField.value = '1'; // Default quantity
        quantityField.focus();
        quantityField.select();
    }
}

/**
 * Show error message
 * @param {string} message - The error message
 */
function showInventoryError(message) {
    const errorContainer = document.getElementById('inventory-error');
    if (!errorContainer) return;
    
    errorContainer.textContent = message;
    errorContainer.style.display = 'block';
    
    // Hide after 5 seconds
    setTimeout(() => {
        errorContainer.style.display = 'none';
    }, 5000);
}

/**
 * Clear inventory form
 */
function clearInventoryForm() {
    // Reset product info
    const productInfoContainer = document.getElementById('product-info');
    if (productInfoContainer) {
        productInfoContainer.innerHTML = '';
        productInfoContainer.style.display = 'none';
    }
    
    // Hide form
    const formContainer = document.getElementById('inventory-form-container');
    if (formContainer) {
        formContainer.style.display = 'none';
    }
    
    // Reset form fields
    const productIdField = document.getElementById('product_id');
    if (productIdField) {
        productIdField.value = '';
    }
    
    const quantityField = document.getElementById('quantity');
    if (quantityField) {
        quantityField.value = '';
    }
    
    const reasonField = document.getElementById('reason');
    if (reasonField) {
        reasonField.value = '';
    }
    
    // Clear error message
    const errorContainer = document.getElementById('inventory-error');
    if (errorContainer) {
        errorContainer.textContent = '';
        errorContainer.style.display = 'none';
    }
}
