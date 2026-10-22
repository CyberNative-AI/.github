// Preload for an unchanged stackbrew.js run: `new Date()` and `Date.now()` return FAKE_NOW
// (an ISO string); dates parsed from explicit strings are untouched.
const FAKE = Date.parse(process.env.FAKE_NOW);
if (isNaN(FAKE)) throw new Error('FAKE_NOW unset/invalid');
const R = Date;
class D extends R { constructor(...a) { if (a.length === 0) super(FAKE); else super(...a); } static now() { return FAKE; } }
globalThis.Date = D;
