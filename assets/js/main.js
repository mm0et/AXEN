/**
 * AXEN — Main JavaScript
 * Preloader, AOS, Swiper, Navbar, Counter, Back-to-Top, Contact Form
 */

document.addEventListener('DOMContentLoaded', () => {

  /* ===== PRELOADER ===== */
  const preloader = document.getElementById('preloader');
  window.addEventListener('load', () => {
    setTimeout(() => {
      preloader?.classList.add('loaded');
      setTimeout(() => preloader?.remove(), 400);
    }, 600);
  });

  /* ===== AOS INIT ===== */
  AOS.init({
    duration: 700,
    easing: 'ease-out-cubic',
    once: true,
    offset: 80,
    disable: 'mobile'
  });

  /* ===== SWIPER — Testimonials ===== */
  new Swiper('.testimonial-swiper', {
    slidesPerView: 1,
    spaceBetween: 24,
    loop: true,
    autoplay: { delay: 5000, disableOnInteraction: false },
    pagination: { el: '.swiper-pagination', clickable: true },
    breakpoints: {
      640: { slidesPerView: 2 },
      1024: { slidesPerView: 3 }
    }
  });

  /* ===== THEME SWITCHER ===== */
  const themeBtns = document.querySelectorAll('.theme-btn');
  const savedTheme = localStorage.getItem('axen-theme') || 'default';

  function applyTheme(theme) {
    if (theme === 'default') {
      document.documentElement.removeAttribute('data-theme');
    } else {
      document.documentElement.setAttribute('data-theme', theme);
    }
    themeBtns.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.themeTarget === theme);
    });
    localStorage.setItem('axen-theme', theme);
  }

  // Apply saved theme on load
  applyTheme(savedTheme);

  themeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      applyTheme(btn.dataset.themeTarget);
    });
  });

  /* ===== NAVBAR SCROLL ===== */
  const navbar = document.getElementById('navbar');
  const backToTop = document.getElementById('backToTop');

  function handleScroll() {
    const y = window.scrollY;
    // Navbar shadow
    navbar?.classList.toggle('scrolled', y > 20);
    // Back to top visibility
    backToTop?.classList.toggle('visible', y > 400);
  }

  window.addEventListener('scroll', handleScroll, { passive: true });
  handleScroll();

  /* ===== HAMBURGER ===== */
  const hamburger = document.getElementById('hamburger');
  const navMenu = document.getElementById('navMenu');

  hamburger?.addEventListener('click', () => {
    hamburger.classList.toggle('active');
    navMenu?.classList.toggle('active');
  });

  // Close menu on link click
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => {
      hamburger?.classList.remove('active');
      navMenu?.classList.remove('active');
    });
  });

  /* ===== ACTIVE NAV ON SCROLL ===== */
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-link');

  function updateActiveNav() {
    const scrollY = window.scrollY + 120;
    sections.forEach(section => {
      const top = section.offsetTop;
      const height = section.offsetHeight;
      const id = section.getAttribute('id');
      if (scrollY >= top && scrollY < top + height) {
        navLinks.forEach(link => {
          link.classList.remove('active');
          if (link.getAttribute('href') === `#${id}`) {
            link.classList.add('active');
          }
        });
      }
    });
  }

  window.addEventListener('scroll', updateActiveNav, { passive: true });

  /* ===== COUNTER ANIMATION ===== */
  const counters = document.querySelectorAll('.stat-number');

  function animateCounter(el) {
    const target = parseInt(el.getAttribute('data-count'));
    const duration = 2000;
    const start = performance.now();

    function update(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out quad
      const ease = 1 - (1 - progress) * (1 - progress);
      el.textContent = Math.floor(ease * target);
      if (progress < 1) requestAnimationFrame(update);
      else el.textContent = target;
    }

    requestAnimationFrame(update);
  }

  // Intersection Observer for counters
  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        counterObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  counters.forEach(c => counterObserver.observe(c));

  /* ===== SMOOTH SCROLL ===== */
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      e.preventDefault();
      const target = document.querySelector(anchor.getAttribute('href'));
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  /* ===== CONTACT FORM ===== */
  const contactForm = document.getElementById('contactForm');

  contactForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = contactForm.querySelector('button[type="submit"]');
    const originalText = btn.innerHTML;
    
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';
    btn.disabled = true;

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500));

    btn.innerHTML = '<i class="fas fa-check"></i> Mensaje enviado';
    btn.style.background = '#16A34A';
    contactForm.reset();

    setTimeout(() => {
      btn.innerHTML = originalText;
      btn.style.background = '';
      btn.disabled = false;
    }, 3000);
  });

  /* ===== DYNAMIC SVG LINES FOR WORKFLOW ===== */
  (function initWorkflowLines() {
    const board = document.querySelector('.iso-board');
    const svg = board?.querySelector('.iso-lines');
    if (!board || !svg) return;

    const connections = [
      ['1', 'center'],
      ['2', 'center'],
      ['3', 'center'],
      ['4', 'center'],
      ['5', 'center'],
      ['6', 'center']
    ];

    const NS = 'http://www.w3.org/2000/svg';

    const lineGroups = connections.map(([from, to]) => {
      const dash = document.createElementNS(NS, 'line');
      dash.classList.add('iso-dash');
      const glow = document.createElementNS(NS, 'line');
      glow.classList.add('iso-dash-glow');
      svg.appendChild(dash);
      svg.appendChild(glow);
      return { from, to, dash, glow };
    });

    function getNodeCenter(nodeId) {
      const node = board.querySelector(`[data-node-id="${nodeId}"]`);
      if (!node) return { x: 450, y: 300 };
      const boardRect = board.getBoundingClientRect();
      const nodeRect = node.getBoundingClientRect();
      const relX = (nodeRect.left + nodeRect.width / 2 - boardRect.left) / boardRect.width;
      const relY = (nodeRect.top + nodeRect.height / 2 - boardRect.top) / boardRect.height;
      return { x: relX * 900, y: relY * 600 };
    }

    function updateLines() {
      lineGroups.forEach(({ from, to, dash, glow }) => {
        const a = getNodeCenter(from);
        const b = getNodeCenter(to);
        [dash, glow].forEach(line => {
          line.setAttribute('x1', a.x);
          line.setAttribute('y1', a.y);
          line.setAttribute('x2', b.x);
          line.setAttribute('y2', b.y);
        });
      });
    }

    requestAnimationFrame(() => requestAnimationFrame(updateLines));
    window.addEventListener('resize', updateLines);

    // Update during first 3s for AOS animations
    let ticks = 0;
    const boot = setInterval(() => { updateLines(); if (++ticks > 30) clearInterval(boot); }, 100);
  })();

});
