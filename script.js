document.addEventListener('DOMContentLoaded', function() {
    fetch('/.netlify/functions/getApiKey')
        .then(response => response.json())
        .then(data => {
            let LIFF_ID = data.LIFF_ID;  // Assign API Key to variable
            
            // Initialize LIFF after LIFF_ID is fetched
            liff.init({
                liffId: LIFF_ID // use key from the secret
            }).then(() => {
                console.log("LIFF initialized!");
            }).catch((error) => {
                console.error("LIFF initialization failed", error);
            });
        })
        .catch(error => {
            console.error("Error fetching LIFF_ID:", error);
        });
    
    const form = document.getElementById('productReviewForm');
    const submitButton = document.getElementById('submitButton');
    // Form submit handler
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Clear previous error messages
        clearErrorMessages();

        // Validate form
        if (validateForm()) {
            // Disable submit button to prevent multiple submissions
            submitButton.disabled = true;
            submitButton.textContent = 'Submitting...';
            const formData = {
                productGroup: document.getElementById('productGroup').value,
                productName: document.getElementById('productName').value,
                rating: document.querySelector('input[name="rating"]:checked').value,
                review: document.getElementById('review').value,
            };
            // Prepare message to send back to LINE
            const message = {
            type: "text",
            text: `Review Submitted:\n----------\n- Product Group: ${formData.productGroup}\n- Product Name: ${formData.productName}\n- Rating: ${formData.rating}/5\n- Review: ${formData.review}\n----------`
            };
            if (liff.isInClient()) {
                liff.sendMessages([message])
                    .then(() => {
                        console.log("Message sent");
                        // Close LIFF app
                        liff.closeWindow();
                    })
                    .catch((error) => {
                        console.error("Error sending message", error);
                        alert("Error sending message");
                    });
            } else {
                // When running in external browser
                alert("This app must be opened in LINE to submit reviews.");
                console.log("Message preview:", message.text);
            }
        };
    });
});
// Validate the form
function validateForm() {
    let isValid = true;
    
    // Validate Product Group
    const productGroup = document.getElementById('productGroup');
    if (!productGroup.value) {
        displayError('productGroupError', 'Please select a product group');
        isValid = false;
    }
    
    // Validate Product Name
    const productName = document.getElementById('productName');
    if (!productName.value.trim()) {
        displayError('productNameError', 'Please enter a product name');
        isValid = false;
    }
    
    // Validate Rating
    // const rating = document.querySelector('input[name="rating"]:checked');
    const rating = document.querySelector('input[name="rating"]:checked');
    if (!rating) {
        displayError('ratingError', 'Please select a rating');
        isValid = false;
    }
    
    // Validate Review
    
    const review = document.getElementById('review');
    if (!review.value.trim()) {
        displayError('reviewError', 'Please enter your review');
        isValid = false;
    } else if (review.value.trim().length < 10) {
        displayError('reviewError', 'Review must be at least 10 characters');
        isValid = false;
    }
    
    return isValid;
}
// Clear all error messages
function clearErrorMessages() {
    const errorElements = document.querySelectorAll('.error-message');
    errorElements.forEach(element => {
        element.textContent = '';
    });
}
// Display error message
function displayError(elementId, message) {
    document.getElementById(elementId).textContent = message;
}
