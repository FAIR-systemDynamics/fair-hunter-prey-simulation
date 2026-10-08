/* SPDX-License-Identifier: MIT */
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

(async () => {
  const browser = await chromium.launch({headless:true, channel:'chrome'});
  const page = await browser.newPage({viewport:{width:1512, height:1050}});
  const errors = [], checks = [];
  const output = '/tmp/kaibab-atlas-review';
  fs.mkdirSync(output, {recursive:true});
  page.on('pageerror', error => errors.push(error.message));
  const nav = page.locator('header nav');
  const drawing = page.locator('#drawing');
  const first = page.locator('#workflow-case2-parameter-to-figure');
  const second = page.locator('#workflow-python-inspection');
  const firstTitle = 'Set predator removal to 0.2/year, simulate the ecosystem, and follow the result into a figure.';
  const secondTitle = 'Read saved results with Python, inspect the data in a notebook, and compare the ecosystem trajectories.';
  async function catalog() {
    await nav.getByRole('link', {name:'Workflows', exact:true}).click();
    await page.locator('#workflow-page').waitFor({state:'visible'});
  }
  async function screenshot(name, fullPage=false) {
    await page.screenshot({path:`${output}/${name}.png`, fullPage});
  }
  try {
    await page.goto('http://127.0.0.1:8765/');
    await drawing.locator('svg .node').first().waitFor();
    assert.equal(await drawing.locator('.node').count(), 20);
    assert.deepEqual(await nav.locator('a').allTextContents(), ['Semantic Model','Workflows']);
    const model = drawing.locator('a[data-entity="file/models/kaibab_ecosystem_model.mdl"]');
    assert((await model.getAttribute('href')).includes('/blob/f156dcf37597c0587958f463985986f0ea91accf/'));
    await model.hover(); assert((await page.locator('#tip').innerText()).includes('GitHub source'));
    await page.keyboard.press('Escape'); assert(await page.locator('#tip').isHidden());
    await model.focus(); assert(await page.locator('#tip').isVisible());
    await drawing.locator('a[data-entity="overview/equations"]').click();
    await page.waitForFunction(() => document.getElementById('map-title').textContent === 'Governing equations');
    assert.equal(await drawing.locator('a[data-entity^="formula/"]').count(), 3);
    await nav.getByRole('link', {name:'Semantic Model', exact:true}).click();
    await page.waitForFunction(() => document.getElementById('map-title').textContent === 'Semantic Model');
    await screenshot('semantic-model');
    checks.push('Semantic Model retains 20 entities, source links, keyboard descriptions and equation exploration');

    await catalog();
    assert.equal(await page.locator('.workflow-section').count(), 2);
    assert.equal(await page.getByRole('navigation', {name:'Workflow contents'}).getByRole('link').count(), 2);
    assert(await page.locator('#canvas').isHidden());
    assert(await page.evaluate(() => document.documentElement.scrollHeight > innerHeight));
    assert(await page.evaluate(() => { const ids=[...document.querySelectorAll('[id]')].map(e=>e.id); return ids.length===new Set(ids).size; }));
    await screenshot('workflow-contents');
    await screenshot('workflow-catalog-full', true);
    await first.locator('.back-contents').scrollIntoViewIfNeeded();
    await first.locator('.back-contents').click();
    assert(await page.locator('#workflows-title').evaluate(el => el.getBoundingClientRect().top < 230));
    checks.push('Workflows has a linked contents list and two sequential examples with unique SVG IDs');

    await page.getByRole('navigation', {name:'Workflow contents'}).getByRole('link', {name:secondTitle, exact:true}).click();
    await page.waitForURL('**/#workflow-python-inspection');
    await page.waitForFunction(() => document.activeElement.id === 'heading-python-inspection');
    assert.equal(await page.locator('header nav a[aria-current]').innerText(), 'Workflows');
    assert.equal(await page.evaluate(() => document.activeElement.id), 'heading-python-inspection');
    assert(await second.locator('h2').evaluate(el => el.getBoundingClientRect().top >= document.querySelector('header').getBoundingClientRect().bottom));
    await screenshot('python-inspection-workflow');
    await page.reload();
    assert(await second.locator('h2').evaluate(el => el.getBoundingClientRect().top >= document.querySelector('header').getBoundingClientRect().bottom));
    await second.getByRole('link', {name:'Explore diagram', exact:true}).click();
    await page.waitForFunction(() => !document.getElementById('canvas').hidden);
    assert.equal(await drawing.locator('.node').count(), 13);
    assert.equal(await page.locator('#back-to-workflows').getAttribute('href'), '#workflow-python-inspection');
    const before = await drawing.getAttribute('style');
    await page.getByRole('button', {name:'Zoom in', exact:true}).click();
    assert.notEqual(await drawing.getAttribute('style'), before);
    await page.getByRole('button', {name:'Fit diagram'}).click();
    await drawing.locator('a[data-entity="processing/inspect-results-python"]').click();
    await page.waitForURL('**/#workflows/processing%2Finspect-results-python?from=python-inspection');
    await page.reload();
    assert.equal(await page.locator('#back-to-workflows').getAttribute('href'), '#workflow-python-inspection');
    await page.locator('#back-to-workflows').click();
    await page.waitForURL('**/#workflow-python-inspection');
    await page.locator('#workflow-page').waitFor({state:'visible'});
    assert(await page.locator('#workflow-page').isVisible());
    checks.push('Contents links, refresh, full diagram, entity exploration and return link preserve workflow context');

    assert.equal(await first.locator('h2').innerText(), firstTitle);
    assert.equal(await second.locator('h2').innerText(), secondTitle);
    assert.equal(await page.locator('[download]').count(), 0);
    for (const section of [first, second]) {
      const stageLabels = await section.locator('svg > text').allTextContents();
      assert.equal(stageLabels.filter(text=>/^[1-5] · /.test(text)).length, 5);
      for (const anchor of await section.locator('.workflow-actions a:not(.diagram-link)').all()) {
        assert((await anchor.getAttribute('href')).startsWith('https://github.com/FAIR-systemDynamics/fair-hunter-prey-simulation/blob/'));
        assert.equal(await anchor.getAttribute('target'), '_blank');
      }
    }
    const notebook = second.getByRole('link', {name:'View notebook in repository'});
    assert((await notebook.getAttribute('href')).endsWith('/docs/semantic/notebooks/inspect_results.ipynb'));
    assert.equal(await second.locator('a[data-entity^="notebook-section/"]').count(), 5);
    for (const anchor of await second.locator('a[data-entity^="notebook-section/"]').all()) {
      assert(/inspect_results\.py#L\d+-L\d+$/.test(await anchor.getAttribute('href')));
    }
    const flow = await second.locator('.edge[data-source="processing/inspect-results-python"]').evaluateAll(nodes=>nodes.map(n=>n.dataset.target));
    assert.deepEqual(flow.sort(), ['file/scripts/vensim_csv.py','notebook/inspect-results'].sort());
    const codeRight = await second.locator('a[data-entity="notebook/inspect-results"] rect').evaluate(el=>+el.getAttribute('x') + +el.getAttribute('width'));
    for (const rect of await second.locator('a[data-entity^="notebook-section/"] rect').all()) {
      assert(await rect.evaluate(el=>+el.getAttribute('x')) > codeRight);
    }
    checks.push('Descriptive titles, five numbered stages, source-only links and exact cell links are present in both workflow views');

    await page.locator('#search').fill('Inspect data with Python');
    await page.locator('#search').press('ArrowDown');
    await page.keyboard.press('Enter');
    await page.waitForURL('**/#workflows/processing%2Finspect-results-python?from=python-inspection');
    await page.waitForFunction(() => !document.getElementById('canvas').hidden);
    await page.locator('#search').fill('zzzz-no-match');
    assert((await page.locator('#results').innerText()).includes('No matching'));
    await page.getByRole('button', {name:'Clear search'}).click();
    assert.equal(await page.locator('#search').inputValue(), '');
    checks.push('Search preserves workflow context, supports keyboard selection, no-results feedback and explicit clear');

    await page.setViewportSize({width:390, height:844});
    await catalog();
    await screenshot('workflow-contents-mobile');
    await page.getByRole('navigation', {name:'Workflow contents'}).getByRole('link', {name:secondTitle, exact:true}).click();
    await page.waitForFunction(() => document.activeElement.id === 'heading-python-inspection');
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    const region = second.locator('.inline-diagram');
    assert(await region.evaluate(el => el.scrollWidth > el.clientWidth));
    await region.focus(); await page.keyboard.press('ArrowRight');
    await page.waitForFunction(() => document.querySelector('#workflow-python-inspection .inline-diagram').scrollLeft > 0);
    assert(await region.evaluate(el => getComputedStyle(el).scrollbarColor !== 'auto'));
    await screenshot('python-inspection-mobile');
    await page.emulateMedia({reducedMotion:'reduce'});
    await second.locator('.back-contents').click();
    await nav.getByRole('link', {name:'Semantic Model', exact:true}).click();
    await page.waitForFunction(() => document.getElementById('map-title').textContent === 'Semantic Model');
    assert(await page.locator('#workflow-page').isHidden());
    assert(await page.evaluate(() => getComputedStyle(document.body).overflow === 'hidden'));
    assert.equal(await drawing.locator('.node').count(), 20);
    await screenshot('semantic-model-mobile');
    checks.push('Mobile workflows scroll as a document, diagrams scroll horizontally by keyboard, and Semantic Model restores its canvas');

    const offline = await browser.newContext({offline:true});
    const local = await offline.newPage();
    await local.goto('file://' + path.resolve('docs/semantic/index.html') + '#workflow-python-inspection');
    assert.equal(await local.locator('.workflow-section').count(), 2);
    assert(await local.locator('#workflow-page').isVisible());
    await offline.close();
    const broken = await browser.newPage();
    await broken.route('**/data/model.js', route => route.abort());
    await broken.goto('http://127.0.0.1:8765/');
    assert((await broken.locator('#drawing').innerText()).includes('could not load'));
    assert(await broken.locator('#search').isDisabled());
    assert((await broken.locator('.repository-link').getAttribute('href')).endsWith('/docs/semantic/model.ttl'));
    await broken.close();
    checks.push('Both workflows open offline; missing-data failure keeps the RDF source link and recovery message');
    assert.deepEqual(errors, []);
    fs.writeFileSync('docs/semantic/browser-validation.json', JSON.stringify({passed:true, checks, errors}, null, 2) + '\n');
    console.log(checks.join('\n'));
  } finally { await browser.close(); }
})().catch(error => {console.error(error); process.exit(1);});
