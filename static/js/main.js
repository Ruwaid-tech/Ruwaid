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

(function themeSwitcher() {
    const btn = document.getElementById('theme-toggle');
    const body = document.body;
    const stored = localStorage.getItem('arthub-theme');
    if (stored === 'dark') {
        body.classList.add('dark-mode');
    }
    const setLabel = () => {
        if (btn) {
            btn.textContent = body.classList.contains('dark-mode') ? '☀️ Light' : '🌙 Dark';
        }
    };
    setLabel();
    if (btn) {
        btn.addEventListener('click', () => {
            body.classList.toggle('dark-mode');
            const mode = body.classList.contains('dark-mode') ? 'dark' : 'light';
            localStorage.setItem('arthub-theme', mode);
            setLabel();
        });
    }
})();
