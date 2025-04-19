/**
 * Reports Management Scripts
 * For Puma Warehouse Management System
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize date pickers
    initializeDatePickers();
    
    // Initialize export buttons
    initializeExportButtons();
    
    // Initialize charts if needed
    initializeDashboardCharts();
});

/**
 * Initialize date picker elements
 */
function initializeDatePickers() {
    // Find all date picker inputs
    const datepickers = document.querySelectorAll('.datepicker');
    
    datepickers.forEach(picker => {
        // Initialize with a date selector
        picker.type = 'date';
    });
}

/**
 * Initialize export buttons functionality
 */
function initializeExportButtons() {
    // Export to PDF button
    const pdfButtons = document.querySelectorAll('.export-pdf');
    pdfButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const form = this.closest('form');
            if (form) {
                // Set hidden field for report type
                const reportTypeField = form.querySelector('input[name="report_type"]');
                if (reportTypeField) {
                    reportTypeField.value = 'pdf';
                }
                form.submit();
            }
        });
    });
    
    // Export to Excel button
    const excelButtons = document.querySelectorAll('.export-excel');
    excelButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const form = this.closest('form');
            if (form) {
                // Set hidden field for report type
                const reportTypeField = form.querySelector('input[name="report_type"]');
                if (reportTypeField) {
                    reportTypeField.value = 'excel';
                }
                form.submit();
            }
        });
    });
}

/**
 * Initialize dashboard charts using Chart.js
 */
function initializeDashboardCharts() {
    // Check if we're on a page with charts
    const inventoryChartEl = document.getElementById('inventory-chart');
    const movementChartEl = document.getElementById('movement-chart');
    
    if (inventoryChartEl) {
        renderInventoryChart(inventoryChartEl);
    }
    
    if (movementChartEl) {
        renderMovementChart(movementChartEl);
    }
}

/**
 * Render inventory by category chart
 * @param {HTMLElement} canvas - The canvas element to render the chart on
 */
function renderInventoryChart(canvas) {
    // Get chart data from data attributes
    const labels = JSON.parse(canvas.getAttribute('data-labels') || '[]');
    const values = JSON.parse(canvas.getAttribute('data-values') || '[]');
    
    // If no data, show "No Data" message
    if (labels.length === 0 || values.length === 0) {
        const context = canvas.getContext('2d');
        context.font = '16px Arial';
        context.fillText('No inventory data available', 50, 100);
        return;
    }
    
    // Create chart
    new Chart(canvas, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: [
                    '#FF0000', // Puma Red
                    '#000000', // Black
                    '#4BC0C0', // Teal
                    '#FFCE56', // Yellow
                    '#E7E9ED', // Light Gray
                    '#36A2EB', // Blue
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        fontSize: 12
                    }
                },
                title: {
                    display: true,
                    text: 'Inventory by Category',
                    fontSize: 16
                }
            }
        }
    });
}

/**
 * Render inventory movement chart
 * @param {HTMLElement} canvas - The canvas element to render the chart on
 */
function renderMovementChart(canvas) {
    // Get chart data from data attributes
    const labels = JSON.parse(canvas.getAttribute('data-labels') || '[]');
    const stockIn = JSON.parse(canvas.getAttribute('data-stock-in') || '[]');
    const stockOut = JSON.parse(canvas.getAttribute('data-stock-out') || '[]');
    
    // If no data, show "No Data" message
    if (labels.length === 0) {
        const context = canvas.getContext('2d');
        context.font = '16px Arial';
        context.fillText('No movement data available', 50, 100);
        return;
    }
    
    // Create chart
    new Chart(canvas, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Stock In',
                    data: stockIn,
                    backgroundColor: '#28a745', // Green for stock in
                    borderColor: '#28a745',
                    borderWidth: 1
                },
                {
                    label: 'Stock Out',
                    data: stockOut,
                    backgroundColor: '#dc3545', // Red for stock out
                    borderColor: '#dc3545',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Quantity'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Period'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Inventory Movement',
                    fontSize: 16
                },
                legend: {
                    position: 'top'
                }
            }
        }
    });
}
