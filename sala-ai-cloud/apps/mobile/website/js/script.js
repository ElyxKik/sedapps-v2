// Sala AI - Shared JS

// Mobile nav toggle
document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) {
    window.lucide.createIcons();
  }

  const hamburger = document.querySelector('.hamburger');
  const nav = document.querySelector('.nav');
  const body = document.body;

  function closeMenu() {
    if (!nav) return;
    nav.classList.remove('open');
    hamburger.classList.remove('active');
    body.classList.remove('nav-locked');
  }

  if (hamburger && nav) {
    hamburger.addEventListener('click', () => {
      const isOpen = nav.classList.toggle('open');
      hamburger.classList.toggle('active', isOpen);
      body.classList.toggle('nav-locked', isOpen);
    });
    nav.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', closeMenu);
    });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') closeMenu();
    });
  }

  // FAQ accordion
  document.querySelectorAll('.faq-q').forEach(q => {
    q.addEventListener('click', () => {
      const a = q.nextElementSibling;
      q.classList.toggle('open');
      a.classList.toggle('open');
    });
  });

  // Domain search (mock)
  const domainForm = document.getElementById('domain-form');
  if (domainForm) {
    domainForm.addEventListener('submit', e => {
      e.preventDefault();
      const input = document.getElementById('domain-input');
      const results = document.getElementById('domain-results');
      const domain = input.value.trim().toLowerCase().replace(/^https?:\/\//, '').replace(/\/$/, '');
      if (!domain || !domain.includes('.')) {
        results.innerHTML = '<div class="domain-result unavailable"><span class="status">Entre un domaine valide, ex : monsite.fr</span></div>';
        return;
      }
      const tlds = ['.fr', '.com', '.net', '.be', '.eu', '.io'];
      let html = '';
      const baseName = domain.split('.')[0];
      tlds.forEach(tld => {
        const candidate = baseName + tld;
        const available = Math.random() > 0.4;
        html += `<div class="domain-result ${available ? 'available' : 'unavailable'}">
          <span style="font-size:16px;font-weight:600;color:var(--navy)">${candidate}</span>
          <span class="status" style="margin-left:auto">${available ? 'Disponible' : 'Indisponible'}</span>
          ${available ? '<button class="btn btn-primary" style="padding:8px 20px;font-size:13px" onclick="alert(\'L\\\'achat de domaine sera bientôt disponible.\')">Choisir</button>' : ''}
        </div>`;
      });
      results.innerHTML = html;
    });
  }

  // Contact form (mock)
  const contactForm = document.getElementById('contact-form');
  if (contactForm) {
    contactForm.addEventListener('submit', e => {
      e.preventDefault();
      const btn = contactForm.querySelector('button[type="submit"]');
      btn.textContent = 'Envoi en cours...';
      btn.disabled = true;
      setTimeout(() => {
        contactForm.innerHTML = '<div style="text-align:center;padding:40px"><div class="success-icon"><i data-lucide="check"></i></div><h3 style="font-size:22px;font-weight:700;color:var(--ink);margin-bottom:8px">Message envoyé !</h3><p style="color:var(--muted)">Merci, l\'équipe Sala AI te répondra rapidement.</p></div>';
        if (window.lucide) {
          window.lucide.createIcons();
        }
      }, 1200);
    });
  }

  // Scroll reveal
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) entry.target.classList.add('fade-up');
    });
  }, { threshold: 0.1 });
  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

  // Hero tabs
  document.querySelectorAll('.hero-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.hero-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
    });
  });
});
