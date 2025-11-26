document.addEventListener('click', (e) => {
    if (e.target.classList.contains('toggle')) {
        const id = e.target.getAttribute('data-target');
        const input = document.getElementById(id);
        if (input) {
            const newType = input.type === 'password' ? 'text' : 'password';
            input.type = newType;
            e.target.textContent = newType === 'password' ? 'Show' : 'Hide';
        }
    }
    if (e.target.closest('.delete-form')) {
        if (!confirm('Delete this artwork?')) {
            e.preventDefault();
        }
    }
});
