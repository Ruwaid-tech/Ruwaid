function togglePassword(id) {
    const input = document.getElementById(id);
    if (!input) return;
    const isHidden = input.type === 'password';
    input.type = isHidden ? 'text' : 'password';
}

// subtle animation for hero cards
window.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.floating-card');
    cards.forEach((card, idx) => {
        card.style.animationDelay = `${idx * 0.2}s`;
    });
});
