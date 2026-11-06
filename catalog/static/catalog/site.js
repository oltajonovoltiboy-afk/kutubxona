document.addEventListener('DOMContentLoaded',()=>{
  if('serviceWorker' in navigator){navigator.serviceWorker.register('/service-worker.js').catch(()=>{});}
  document.querySelectorAll('form').forEach(form=>{if(form.id==='ai-form')return;form.addEventListener('submit',()=>{const btn=form.querySelector('button[type="submit"],button:not([type])');if(btn&&!btn.dataset.keepLabel){btn.dataset.keepLabel='1';btn.dataset.label=btn.textContent.trim();btn.disabled=true;btn.style.opacity='.75';setTimeout(()=>{btn.disabled=false;btn.style.opacity=''},5000)}})});
});

/* Mobile navigation */
document.addEventListener('DOMContentLoaded', function () {
  var toggle = document.querySelector('.menu-toggle');
  var nav = document.querySelector('.top nav');
  if (!toggle || !nav) return;

  function setOpen(open) {
    document.body.classList.toggle('nav-open', open);
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    toggle.setAttribute('aria-label', open ? 'Menyuni yopish' : 'Menyuni ochish');
  }

  toggle.addEventListener('click', function (e) {
    e.stopPropagation();
    setOpen(!document.body.classList.contains('nav-open'));
  });

  nav.querySelectorAll('a').forEach(function (link) {
    link.addEventListener('click', function () {
      setOpen(false);
    });
  });

  document.addEventListener('click', function (e) {
    if (!document.body.classList.contains('nav-open')) return;
    if (!e.target.closest('.top')) setOpen(false);
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') setOpen(false);
  });

  window.addEventListener('resize', function () {
    if (window.innerWidth > 760) setOpen(false);
  });
});
