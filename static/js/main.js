document.addEventListener('click', (e) => {
    if (e.target.classList.contains('toggle')) {
        const id = e.target.getAttribute('data-target');
        const input = document.getElementById(id);
        if (input) {
            input.type = input.type === 'password' ? 'text' : 'password';
        }
    }
    if (e.target.closest('.delete-form')) {
        if (!confirm('Delete this artwork?')) {
            e.preventDefault();
        }
    }
});
