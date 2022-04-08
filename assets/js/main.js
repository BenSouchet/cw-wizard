function showCardsList(seller_id) {
    document.activeElement.blur()

    var popup = document.getElementById("popup-container");
    if (!popup) { return false; }

    // Step 1: Try to retrieve the DOM elem
    var cards_container = document.getElementById("seller-"+seller_id+"-cards");
    if (!cards_container) { return false; }

    // Step 2: Replace the popup grid contents with the cards
    var cards_list = document.getElementById("cards-list");
    if (!cards_list) { return false; }
    cards_list.innerHTML = cards_container.innerHTML;

    // Step 3: Fill seller info in popup
    var seller_link_tag = document.getElementById("seller-"+seller_id);
    if (!seller_link_tag) { return false; }
    var seller_link_popup_tag = document.getElementById("popup-seller-name");
    if (!seller_link_popup_tag) { return false; }
    seller_link_popup_tag.href = seller_link_tag.href
    seller_link_popup_tag.innerText = seller_link_tag.innerText;

    var seller_sales_number_tag = document.getElementById("seller-"+seller_id+"-sales-number");
    var seller_sales_popup_tag = document.getElementById("popup-seller-sales-number");
    if (!seller_sales_popup_tag) { return false; }
    seller_sales_popup_tag.innerText = '('+ seller_sales_number_tag.innerText + ' Sales)';

    // Step 4: Block overflow body
    var body = document.querySelector("body");
    body.style.overflow = "hidden";

    // Step 5: Show the popup
    popup.classList.remove("hidden");
}

function closePopup() {
    var popup = document.getElementById("popup-container");
    if (!popup) { return false; }
    // Step 1: Closing means hide it
    popup.classList.add("hidden");

    // Step 2: Block overflow body
    var body = document.querySelector("body");
    body.style.overflow = "auto";

    return false;
}
