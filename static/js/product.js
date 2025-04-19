/**
 * Product Management Scripts
 * For Puma Warehouse Management System
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize image gallery functionality
    initializeImageGallery();
    
    // Initialize dynamic attributes
    initializeDynamicAttributes();
    
    // Initialize barcode generation
    initializeBarcodeGeneration();
});

/**
 * Initialize product image gallery functionality
 */
function initializeImageGallery() {
    // Set featured image functionality
    const setFeaturedButtons = document.querySelectorAll('.set-featured-btn');
    setFeaturedButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const imageId = this.getAttribute('data-image-id');
            setFeaturedImage(imageId);
        });
    });
    
    // Delete image functionality
    const deleteImageButtons = document.querySelectorAll('.delete-image-btn');
    deleteImageButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            if (confirm('Are you sure you want to delete this image?')) {
                const imageId = this.getAttribute('data-image-id');
                deleteProductImage(imageId);
            }
        });
    });
    
    // Image preview for new uploads
    const imageInput = document.getElementById('images');
    const imagePreviewContainer = document.getElementById('image-previews');
    
    if (imageInput && imagePreviewContainer) {
        imageInput.addEventListener('change', function() {
            // Clear existing previews
            imagePreviewContainer.innerHTML = '';
            
            // Create previews for each selected file
            for (let i = 0; i < this.files.length; i++) {
                const file = this.files[i];
                
                // Only process image files
                if (!file.type.match('image.*')) {
                    continue;
                }
                
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    const preview = document.createElement('div');
                    preview.classList.add('col-md-3', 'mb-3');
                    preview.innerHTML = `
                        <div class="card">
                            <img src="${e.target.result}" class="card-img-top" style="height: 150px; object-fit: contain;">
                            <div class="card-body p-2">
                                <p class="card-text small text-truncate">${file.name}</p>
                            </div>
                        </div>
                    `;
                    
                    imagePreviewContainer.appendChild(preview);
                };
                
                reader.readAsDataURL(file);
            }
        });
    }
}

/**
 * Set an image as the featured image
 * @param {string} imageId - The ID of the image to set as featured
 */
function setFeaturedImage(imageId) {
    // Create form data
    const formData = new FormData();
    
    // Send request to server
    fetch(`/products/set-featured-image/${imageId}`, {
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
            // Reload the page to show changes
            window.location.reload();
        } else {
            alert(data.message || 'Failed to set featured image');
        }
    })
    .catch(error => {
        console.error('Error setting featured image:', error);
        alert('Error setting featured image. Please try again.');
    });
}

/**
 * Delete a product image
 * @param {string} imageId - The ID of the image to delete
 */
function deleteProductImage(imageId) {
    // Create form data
    const formData = new FormData();
    
    // Send request to server
    fetch(`/products/delete-image/${imageId}`, {
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
            // Reload the page to show changes
            window.location.reload();
        } else {
            alert(data.message || 'Failed to delete image');
        }
    })
    .catch(error => {
        console.error('Error deleting image:', error);
        alert('Error deleting image. Please try again.');
    });
}

/**
 * Initialize dynamic attribute fields
 */
function initializeDynamicAttributes() {
    // Handle dropdown fields
    const dropdownFields = document.querySelectorAll('select[data-attribute-type="dropdown"]');
    
    dropdownFields.forEach(field => {
        // If has 'data-current-value' attribute, set it
        const currentValue = field.getAttribute('data-current-value');
        if (currentValue) {
            field.value = currentValue;
        }
    });
    
    // Handle checkbox fields
    const checkboxFields = document.querySelectorAll('input[data-attribute-type="checkbox"]');
    
    checkboxFields.forEach(field => {
        const currentValue = field.getAttribute('data-current-value');
        if (currentValue && currentValue.toLowerCase() === 'true') {
            field.checked = true;
        }
    });
}

/**
 * Initialize barcode generation functionality
 */
function initializeBarcodeGeneration() {
    const generateBarcodeBtn = document.getElementById('generate-barcode');
    const barcodeField = document.getElementById('barcode');
    
    if (generateBarcodeBtn && barcodeField) {
        generateBarcodeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Generate random barcode (12 digits for EAN-13, last digit is check digit)
            const randomDigits = Array.from({length: 12}, () => Math.floor(Math.random() * 10)).join('');
            barcodeField.value = randomDigits;
        });
    }
}
