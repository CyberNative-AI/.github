// Common probe: feature names present + paint-event count; engines add flags to window.__probe.
window.__probe = { errors: [] };
(function () {
  const p = window.__probe;
  const has = (o, k) => { try { return !!o && k in o; } catch (e) { return 'err'; } };
  p.ua = navigator.userAgent;
  p.c2d_drawElementImage = has(window.CanvasRenderingContext2D && CanvasRenderingContext2D.prototype, 'drawElementImage');
  const gl2 = window.WebGL2RenderingContext && WebGL2RenderingContext.prototype;
  p.gl_texElementImage2D = has(gl2, 'texElementImage2D');
  p.gl_texElementSubImage2D = has(gl2, 'texElementSubImage2D');
  p.canvas_requestPaint = has(HTMLCanvasElement.prototype, 'requestPaint');
  p.canvas_updateElementGeometry = has(HTMLCanvasElement.prototype, 'updateElementGeometry');
  p.canvas_content_reflect = has(HTMLCanvasElement.prototype, 'content');
  p.gpuqueue_copyElementImageToTexture = has(window.GPUQueue && GPUQueue.prototype, 'copyElementImageToTexture');
  p.gpuqueue_drawElementImageToTexture = has(window.GPUQueue && GPUQueue.prototype, 'drawElementImageToTexture');
  p.paints = 0;
  window.__watch = (canvas) => { canvas.addEventListener('paint', () => { p.paints++; }); };
})();
