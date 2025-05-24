// Search/filter products in inventory table
function searchProducts() {
    const input = document.getElementById("searchInput");
    const filter = input.value.toLowerCase();
    const table = document.getElementById("productsTable");
    const trs = table.getElementsByTagName("tr");
    for (let i = 1; i < trs.length; i++) {
        let show = false;
        const tds = trs[i].getElementsByTagName("td");
        for (let j = 0; j < tds.length - 1; j++) {
            if (tds[j].textContent.toLowerCase().indexOf(filter) > -1) {
                show = true;
                break;
            }
        }
        trs[i].style.display = show ? "" : "none";
    }
}

// Delete confirmation modal
let deleteProductId = null;
function confirmDelete(productId, productName) {
    deleteProductId = productId;
    document.getElementById("deleteModalText").textContent = `Are you sure you want to delete "${productName}"?`;
    document.getElementById("deleteModal").style.display = "flex";
}
function closeModal() {
    document.getElementById("deleteModal").style.display = "none";
    deleteProductId = null;
}
document.addEventListener("DOMContentLoaded", function() {
    const btn = document.getElementById("confirmDeleteBtn");
    if (btn) {
        btn.onclick = function() {
            if (deleteProductId) {
                document.getElementById(`delete-form-${deleteProductId}`).submit();
            }
        };
    }
});

// Simple form validation for add product
function validateForm() {
    const name = document.getElementById("name").value.trim();
    const category = document.getElementById("category").value.trim();
    const price = document.getElementById("price").value;
    const quantity = document.getElementById("quantity").value;
    if (!name || !category || price <= 0 || quantity < 0) {
        alert("Please fill all fields with valid values.");
        return false;
    }
    return true;
}