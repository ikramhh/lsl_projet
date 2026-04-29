/* ========================================
   Main JS - Navbar + mobile menu + Carousel
   ======================================== */

let carouselIndex = 0;

function updateCarousel() {
  const track = document.getElementById('carousel-track');
  if (!track) return;
  const slides = track.querySelectorAll('.carousel-slide');
  const total = slides.length;
  if (total === 0) return;

  track.style.transform = `translateX(-${carouselIndex * 100}%)`;

  slides.forEach((slide) => {
    slide.querySelectorAll('.dot').forEach((dot, dIdx) => {
      dot.classList.toggle('active', dIdx === carouselIndex);
    });
  });
}

function nextSlide() {
  const track = document.getElementById('carousel-track');
  if (!track) return;
  const total = track.querySelectorAll('.carousel-slide').length;
  carouselIndex = (carouselIndex + 1) % total;
  updateCarousel();
}

function skipCarousel() {
  const track = document.getElementById('carousel-track');
  if (!track) return;
  const total = track.querySelectorAll('.carousel-slide').length;
  carouselIndex = total - 1;
  updateCarousel();
}

function togglePassword() {
  const input = document.getElementById('password');
  const icon = document.getElementById('eye-icon');
  if (!input || !icon) return;
  if (input.type === 'password') {
    input.type = 'text';
    icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L6.228 6.228" />';
  } else {
    input.type = 'password';
    icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"/><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>';
  }
}

function toggleUserMenu() {
  const menu = document.getElementById('userMenu');
  if (menu) {
    menu.classList.toggle('active');
  }
}

// Close user menu when clicking outside
document.addEventListener('click', (e) => {
  const userDropdown = document.querySelector('.user-dropdown');
  const userMenu = document.getElementById('userMenu');
  if (userDropdown && userMenu && !userDropdown.contains(e.target)) {
    userMenu.classList.remove('active');
  }
});

// Expose for inline onclick handlers
window.nextSlide = nextSlide;
window.skipCarousel = skipCarousel;
window.togglePassword = togglePassword;
window.toggleUserMenu = toggleUserMenu;

document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.menu-toggle');
  const navLinks = document.querySelector('.nav-links');
  const navAuth = document.querySelector('.nav-auth');

  if (toggle) {
    toggle.addEventListener('click', () => {
      const open = navLinks?.classList.toggle('open');
      navAuth?.classList.toggle('open', open);
    });
  }

  // Close mobile menu on link click
  document.querySelectorAll('.nav-links a').forEach(a => {
    a.addEventListener('click', () => {
      navLinks?.classList.remove('open');
      navAuth?.classList.remove('open');
    });
  });

  // Carousel button listeners (backup for inline onclick)
  document.querySelectorAll('.carousel-next').forEach(btn => {
    if (!btn.getAttribute('href')) {
      btn.addEventListener('click', nextSlide);
    }
  });
  document.querySelectorAll('.carousel-skip').forEach(btn => {
    btn.addEventListener('click', skipCarousel);
  });

  updateCarousel();
});
