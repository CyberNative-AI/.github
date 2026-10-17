// live-region-check.js: does a streamed chat reply land inside an ARIA live region?
// Paste into the browser DevTools console on your chat page BEFORE you send a message.
// When the reply has finished, run:  liveCheck("a few words from the end of the reply")
// It reports the page's live regions, whether that text is inside one, and how many DOM
// changes happened inside live regions while the reply streamed. It reads open shadow roots.
// It does not tell you what a screen reader will say; test that with a real screen reader.
(() => {
  const LIVE_ROLES = new Set(['log', 'status', 'alert']);
  const liveAncestor = (n) => {
    for (let e = n.nodeType === 1 ? n : n.parentNode; e; e = e.parentNode || e.host) {
      if (e.nodeType !== 1) continue;
      const live = e.getAttribute('aria-live');
      if (live === 'off') return null;
      if (live === 'polite' || live === 'assertive' || LIVE_ROLES.has(e.getAttribute('role'))) return e;
    }
    return null;
  };
  const describe = (e) => {
    if (!e) return null;
    const a = ['role', 'aria-live', 'aria-relevant', 'aria-atomic', 'aria-busy']
      .filter((k) => e.hasAttribute(k)).map((k) => `[${k}=${e.getAttribute(k)}]`).join('');
    return e.tagName.toLowerCase() + a;
  };
  const roots = () => {
    const out = [document];
    const walk = (r) => {
      const tw = document.createTreeWalker(r, NodeFilter.SHOW_ELEMENT);
      for (let n = tw.currentNode; n; n = tw.nextNode()) if (n.shadowRoot) { out.push(n.shadowRoot); walk(n.shadowRoot); }
    };
    walk(document);
    return out;
  };
  let changes = 0;
  for (const r of roots()) {
    new MutationObserver((ms) => { for (const m of ms) if (liveAncestor(m.target)) changes += 1; })
      .observe(r, { subtree: true, childList: true, characterData: true });
  }
  window.liveCheck = (endText) => {
    const regions = [];
    let node = null;
    for (const r of roots()) {
      r.querySelectorAll('[aria-live],[role=log],[role=status],[role=alert]').forEach((e) => regions.push(describe(e)));
      const tw = document.createTreeWalker(r, NodeFilter.SHOW_TEXT);
      for (let n = tw.nextNode(); n; n = tw.nextNode()) {
        if (endText && n.nodeValue.includes(endText) && !['SCRIPT', 'STYLE', 'TEMPLATE', 'NOSCRIPT'].includes(n.parentNode?.nodeName)) node = n;
      }
    }
    const result = {
      liveRegions: regions,
      replyInsideLiveRegion: node ? describe(liveAncestor(node)) : (endText ? 'text not found' : 'no text given'),
      changesInsideLiveRegionsSincePaste: changes,
    };
    console.log(JSON.stringify(result, null, 2));
    return result;
  };
  console.log('live-region-check ready: send a message, wait for the full reply, then run liveCheck("<words from its end>")');
})();
