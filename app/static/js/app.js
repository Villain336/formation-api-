/* Formation API - Client JS */

// Copy to clipboard
document.addEventListener('click', function(e) {
    if (e.target.closest('[data-copy]')) {
        const btn = e.target.closest('[data-copy]');
        const text = btn.getAttribute('data-copy');
        navigator.clipboard.writeText(text).then(function() {
            const original = btn.textContent;
            btn.textContent = 'Copied!';
            setTimeout(function() { btn.textContent = original; }, 2000);
        });
    }

    // Code block copy
    if (e.target.closest('.code-block__copy')) {
        const btn = e.target.closest('.code-block__copy');
        const pre = btn.closest('.code-block').querySelector('pre');
        navigator.clipboard.writeText(pre.textContent.trim()).then(function() {
            const original = btn.textContent;
            btn.textContent = 'Copied!';
            setTimeout(function() { btn.textContent = original; }, 2000);
        });
    }
});

// Mobile nav toggle
document.addEventListener('DOMContentLoaded', function() {
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            var target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // Active doc sidebar link
    var currentPath = window.location.pathname;
    document.querySelectorAll('.docs-sidebar a, .dash-sidebar a').forEach(function(link) {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});

// API Key visibility toggle
function toggleKeyVisibility(btn) {
    var display = btn.previousElementSibling;
    if (display.getAttribute('data-masked') === 'true') {
        display.textContent = display.getAttribute('data-full');
        display.setAttribute('data-masked', 'false');
        btn.textContent = 'Hide';
    } else {
        display.textContent = display.getAttribute('data-prefix') + '••••••••••••••••';
        display.setAttribute('data-masked', 'true');
        btn.textContent = 'Reveal';
    }
}
