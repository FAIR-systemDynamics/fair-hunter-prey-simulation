// SPDX-FileCopyrightText: 2026 Vasiliy Seibert
// SPDX-License-Identifier: MIT
const agenda = document.getElementById('lecture-agenda');
const toggle = document.getElementById('agenda-toggle');
const sections = [...document.querySelectorAll('.slides > section')];
const nav = agenda.querySelector('nav');
sections.forEach((slide, index) => {
  const anchor = document.createElement('a');
  anchor.href = '#/' + slide.id;
  anchor.textContent = `${index + 1}. ${slide.querySelector('h1').textContent}`;
  const group = document.createElement('small');
  group.textContent = slide.dataset.group;
  anchor.append(group);
  anchor.addEventListener('click', () => agenda.close());
  nav.append(anchor);
});
function openAgenda() {
  if (agenda.open) return;
  [...nav.children].forEach((a, index) => {
    if (sections[index].classList.contains('present')) a.setAttribute('aria-current', 'page');
    else a.removeAttribute('aria-current');
  });
  agenda.showModal();
  nav.querySelector('[aria-current]')?.scrollIntoView({block: 'center'});
  document.getElementById('agenda-close').focus();
}
toggle.addEventListener('click', openAgenda);
document.getElementById('agenda-close').addEventListener('click', () => agenda.close());
agenda.addEventListener('close', () => toggle.focus());
document.addEventListener('keydown', event => {
  if (event.key.toLowerCase() === 'm' && !event.ctrlKey && !event.metaKey && !['INPUT','TEXTAREA'].includes(event.target.tagName)) {
    event.preventDefault();
    if (agenda.open) agenda.close(); else openAgenda();
  }
});
Reveal.initialize({
  width: 1280, height: 800, margin: 0.02, minScale: 0.15, maxScale: 1.6,
  scrollActivationWidth: null,
  hash: true, history: true, center: false, controls: true, progress: true,
  slideNumber: 'c/t', transition: 'none', backgroundTransition: 'none',
  pdfSeparateFragments: false, pdfMaxPagesPerSlide: 1,
  keyboardCondition: () => !agenda.open,
  plugins: [RevealNotes, RevealSearch]
});
Reveal.on('slidechanged', event => {
  document.title = event.currentSlide.querySelector('h1').textContent + ' · FAIR4RS';
  if (matchMedia('(max-width:680px)').matches) window.scrollTo(0,0);
});
