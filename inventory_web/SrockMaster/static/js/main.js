// Form validation
function validateForm() {
    const name = document.getElementById('name').value;
    const price = document.getElementById('price').value;
    const quantity = document.getElementById('quantity').value;
    const category = document.getElementById('category').value;

    if (!name || !price || !quantity || !category) {
        alert('Please fill in all fields');
        return false;
    }

    if (price < 0 || quantity < 0) {
        alert('Price and quantity must be positive numbers');
        return false;
    }

    return true;
}

// Delete confirmation
function confirmDelete(productId) {
    if (confirm('Are you sure you want to delete this product?')) {
        document.getElementById(`delete-form-${productId}`).submit();
    }
}

// Search functionality
function searchProducts() {
    const input = document.getElementById('searchInput');
    const filter = input.value.toLowerCase();
    const table = document.getElementById('productsTable');
    const rows = table.getElementsByTagName('tr');

    for (let i = 1; i < rows.length; i++) {
        const nameCell = rows[i].getElementsByTagName('td')[1];
        if (nameCell) {
            const text = nameCell.textContent || nameCell.innerText;
            rows[i].style.display = text.toLowerCase().indexOf(filter) > -1 ? '' : 'none';
        }
    }
}