// JavaScript Vanilla untuk Interaktivitas dan PWA Features
// Fokus: Navigasi halus, validasi form, error handling, push notifications placeholder

// 1. Navigasi Responsif: Toggle menu hamburger
document.addEventListener('DOMContentLoaded', () => {
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');

    if (hamburger && navMenu) {
        hamburger.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            // Animasi halus untuk hamburger lines (opsional)
            hamburger.classList.toggle('active');
        });
    }

    // Update active nav link berdasarkan halaman saat ini
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPage) {
            link.classList.add('active');
        }
    });

    // Smooth scroll untuk anchor links (jika ada di masa depan)
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});

// 2. Validasi Formulir Kontak dan AJAX Placeholder
const contactForm = document.getElementById('contactForm');
const formMessage = document.getElementById('formMessage');

if (contactForm) {
    contactForm.addEventListener('submit', (e) => {
        e.preventDefault();

        // Validasi sisi klien
        const name = document.getElementById('name').value.trim();
        const email = document.getElementById('email').value.trim();
        const message = document.getElementById('message').value.trim();

        if (!name || !email || !message) {
            showMessage('Semua field harus diisi!', 'error');
            return;
        }

        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            showMessage('Email tidak valid!', 'error');
            return;
        }

        // Simulasi AJAX: Di produksi, ganti dengan fetch ke backend
        fetch('/api/contact', {  // Placeholder endpoint
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, message })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Gagal mengirim');
            }
            return response.json();
        })
        .then(data => {
            showMessage('Pesan berhasil dikirim!', 'success');
            contactForm.reset();
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('Terjadi kesalahan. Coba lagi nanti.', 'error');
        });
    });
}

function showMessage(text, type) {
    if (formMessage) {
        formMessage.textContent = text;
        formMessage.className = type;  // Tambahkan class CSS untuk styling (e.g., .error {color: red;})
        setTimeout(() => { formMessage.textContent = ''; }, 5000);
    }
}

// 3. PWA: Push Notifications Placeholder
// Gunakan Push.js atau native API; butuh setup server untuk VAPID keys
function initPushNotifications() {
    if ('Notification' in window && Notification.permission === 'default') {
        // Placeholder: Request permission
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                console.log('Push enabled');
                // Integrasi server: Kirim subscription ke backend
                // if (Push && Push.Permission.has()) { Push.create('Update Blog', { body: 'Post baru tersedia!', icon: '/img/logo.png' }); }
            }
        });
    }
}

// Panggil initPushNotifications() jika diperlukan, e.g., on load atau button click

// 4. Lazy Loading Polyfill (untuk browser lama, tapi modern support native)
if ('loading' in HTMLImageElement.prototype) {
    // Native lazy loading didukung
} else {
    // Polyfill sederhana
    const images = document.querySelectorAll('img[loading="lazy"]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;  // Asumsi data-src digunakan jika perlu
                img.classList.remove('lazy');
                observer.unobserve(img);
            }
        });
    });
    images.forEach(img => imageObserver.observe(img));
}

// 5. Optimasi: Preload critical resources (bisa ditambahkan di HTML head jika perlu)
// No heavy libs, keep vanilla for performance