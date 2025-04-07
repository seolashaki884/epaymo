// Import SweetAlert2
import Swal from 'sweetalert2';

// Example of your addToCart function
async function addToCart(documentId) {
    console.log("addToCart function triggered for document ID:", documentId);
    
    try {
        const response = await fetch(`/add-to-cart/${documentId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'), // Django CSRF token
            },
            body: JSON.stringify({ document_id: documentId }),
        });

        const data = await response.json();

        if (data.cart_item_count !== undefined) {
            updateCartCount(data.cart_item_count);

            // SweetAlert2 usage
            Swal.fire({
                title: 'Item Added!',
                text: 'The document has been added to your cart.',
                icon: 'success',
                position: 'top',
                toast: true,
                timer: 2000,
                showConfirmButton: false,
            });
        } else {
            console.error("Error: Invalid response data", data);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function updateCartCount(count) {
    document.getElementById("cart-count").textContent = count;  // Assuming you have an element with id `cart-count`
}
