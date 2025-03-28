function setupModal(modalId) {
    const modal = document.getElementById(modalId);
    
    if (!modal) return;

    // Store last focused element to restore focus when modal closes
    let lastFocusedElement;

    modal.addEventListener('show.bs.modal', function () {
        lastFocusedElement = document.activeElement;
        // Remove aria-hidden when modal opens
        modal.removeAttribute('aria-hidden');
    });

    modal.addEventListener('shown.bs.modal', function () {
        // Focus the first input or button in the modal
        const firstFocusable = modal.querySelector('input, button, select, textarea');
        if (firstFocusable) {
            firstFocusable.focus();
        }
    });

    modal.addEventListener('hide.bs.modal', function () {
        // Restore focus to the element that opened the modal
        if (lastFocusedElement) {
            lastFocusedElement.focus();
        }
    });

    // Handle keyboard accessibility
    modal.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        }
    });
}

// Example usage:
document.addEventListener('DOMContentLoaded', function() {
    setupModal('addCategoryModal');
});
