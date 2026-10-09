// SPDX-FileCopyrightText: 2026 Vasiliy Seibert
// SPDX-License-Identifier: MIT

  Reveal.initialize({
    hash: true,
    history: true,
    keyboard: {79: 'toggleOverview'},
    keyboardCondition: () => !document.getElementById('nav-panel').classList.contains('open'),
    slideNumber: 'c/t',
    controls: true,
    controlsLayout: 'edges',
    controlsBackArrows: 'faded',
    progress: true,
    transition: new URLSearchParams(location.search).has('capture') ? 'none' : 'fade',
    transitionSpeed: 'default',
    backgroundTransition: new URLSearchParams(location.search).has('capture') ? 'none' : 'fade',
    scrollActivationWidth: null,
    pdfMaxPagesPerSlide: 1,
    width: 1280,
    height: 800,
    margin: 0.04,
    minScale: 0.2,
    maxScale: 2.0,
    pdfSeparateFragments: false,
    plugins: [RevealHighlight, RevealNotes, RevealSearch]
  });

  // ---------- Agenda navigation overlay ----------
  Reveal.on('ready', buildAgendaMenu);
  Reveal.on('slidechanged', highlightCurrentInMenu);

  const panel   = document.getElementById('nav-panel');
  const overlay = document.getElementById('nav-overlay');
  const toggle  = document.getElementById('nav-toggle');
  const closeBtn= panel.querySelector('.nav-close');

  panel.inert = true;
  function openMenu() { panel.inert = false; panel.classList.add('open'); overlay.classList.add('open'); panel.setAttribute('aria-hidden','false'); panel.setAttribute('aria-modal','true'); toggle.setAttribute('aria-expanded','true'); document.querySelector('.reveal').inert=true; highlightCurrentInMenu(); closeBtn.focus(); }
  function closeMenu() { panel.inert = true; panel.classList.remove('open'); overlay.classList.remove('open'); panel.setAttribute('aria-hidden','true'); panel.removeAttribute('aria-modal'); toggle.setAttribute('aria-expanded','false'); document.querySelector('.reveal').inert=false; toggle.focus(); }
  function isOpen()    { return panel.classList.contains('open'); }

  toggle.addEventListener('click', () => isOpen() ? closeMenu() : openMenu());
  overlay.addEventListener('click', closeMenu);
  closeBtn.addEventListener('click', closeMenu);

  document.addEventListener('keydown', (e) => {
    if (e.target.closest('input, textarea, [contenteditable]')) return;
    if (e.key === 'm' || e.key === 'M') { e.preventDefault(); isOpen() ? closeMenu() : openMenu(); }
    if (e.key === 'Escape' && isOpen()) closeMenu();
  });

  function buildAgendaMenu() {
    const groupsEl = panel.querySelector('.nav-groups');
    const slides = Reveal.getSlides();
    const groups = [];
    let current = null;

    slides.forEach((s, i) => {
      const isDivider = s.classList.contains('divider');
      const isTitle   = s.classList.contains('title-slide');
      const brand     = s.querySelector('.slide-header .brand')?.textContent?.trim() || '';
      const chipRaw   = s.querySelector('.slide-header .chip')?.textContent?.trim() || '';
      const h1node    = s.querySelector('h1');
      const h1Text    = h1node ? h1node.textContent.replace(/\s+/g,' ').trim() : '';
      const divNum    = s.querySelector('.divider .num')?.textContent?.trim() || '';
      const divHead   = s.querySelector('.divider h1')?.textContent?.trim() || '';

      // Start a new group on every title slide or divider
      if (isTitle || isDivider || s.id === 'shared-specification' || s.id === 'appendix-repository' || s.id === 'checklist') {
        current = {
          num: isTitle ? '00' : divNum,
          name: s.id === 'shared-specification' ? 'Case-study additions' : s.id === 'appendix-repository' ? 'Optional appendix' : s.id === 'checklist' || s.id === 'discussion' ? 'Wrap-up' : isTitle ? 'Opening' : (divHead || 'Block'),
          isPractical: /Practical/i.test(divHead) || /Practical/i.test(brand),
          items: []
        };
        groups.push(current);
      } else if (!current) {
        current = { num: '00', name: 'Opening', isPractical: false, items: [] };
        groups.push(current);
      }

      // Kind tag
      let kind = '';
      if (isDivider || isTitle) kind = '';
      else if (/Principle/i.test(chipRaw))  kind = 'principle';
      else if (/In practice/i.test(chipRaw)) kind = 'practice';
      else if (current.isPractical)          kind = 'practical';

      current.items.push({
        index: i,
        label: (isTitle ? 'Title · ' + h1Text : isDivider ? 'Divider · ' + divHead : h1Text || chipRaw || ('Slide ' + (i+1))),
        kind
      });
    });

    groupsEl.innerHTML = groups.map(g => `
      <div class="nav-group${g.isPractical ? ' practical' : ''}">
        <div class="group-head">
          <span class="num">${escapeHTML(g.num)}</span>
          <span class="name">${escapeHTML(g.name)}</span>
        </div>
        ${g.items.map(it => `
          <a class="nav-slide" data-idx="${it.index}" href="#/${slides[it.index].id || it.index}">
            <span class="idx">${String(it.index+1).padStart(2,'0')}</span>
            <span class="lbl">${escapeHTML(it.label)}</span>
            ${it.kind ? `<span class="kind ${it.kind}">${it.kind}</span>` : ''}
          </a>`).join('')}
      </div>
    `).join('');

    groupsEl.querySelectorAll('.nav-slide').forEach(a => {
      a.addEventListener('click', (e) => {
        e.preventDefault();
        const idx = Number(a.getAttribute('data-idx'));
        Reveal.slide(idx);
        closeMenu();
      });
    });

    highlightCurrentInMenu();
  }

  function highlightCurrentInMenu() {
    const idx = Reveal.getState().indexh;
    panel.querySelectorAll('.nav-slide').forEach(a => {
      a.classList.toggle('current', Number(a.getAttribute('data-idx')) === idx);
    });
    const current = panel.querySelector('.nav-slide.current');
    if (current && isOpen()) current.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }

  function escapeHTML(s) {
    return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

// Keep the original grouped panel; add keyboard focus containment and restoration.
panel.addEventListener('keydown', event => {
  if (event.key !== 'Tab') return;
  const items = [...panel.querySelectorAll('button,a[href]')];
  const first = items[0], last = items[items.length-1];
  if (event.shiftKey && document.activeElement === first) {event.preventDefault(); last.focus();}
  else if (!event.shiftKey && document.activeElement === last) {event.preventDefault(); first.focus();}
});
Reveal.on('slidechanged', event => {
  document.title = event.currentSlide.querySelector('h1').textContent + ' · FAIR4RS';
  if (matchMedia('(max-width:680px)').matches) window.scrollTo(0,0);
});
