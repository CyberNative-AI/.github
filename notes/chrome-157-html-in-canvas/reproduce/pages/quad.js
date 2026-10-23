// Full-canvas textured quad for WebGL2 pages (NGL, BGL). Returns { gl, tex, draw }.
window.__quad = function (canvas) {
  const gl = canvas.getContext('webgl2', { preserveDrawingBuffer: true });
  const vs = `#version 300 es
in vec2 p; out vec2 uv; void main(){ uv = vec2(p.x*0.5+0.5, 0.5-p.y*0.5); gl_Position = vec4(p,0.,1.); }`;
  const fs = `#version 300 es
precision mediump float; in vec2 uv; uniform sampler2D t; out vec4 o; void main(){ o = texture(t, uv); }`;
  const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); return s; };
  const prog = gl.createProgram(); gl.attachShader(prog, sh(gl.VERTEX_SHADER, vs)); gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, fs)); gl.linkProgram(prog);
  const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);
  const loc = gl.getAttribLocation(prog, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
  const tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  const draw = () => { gl.viewport(0, 0, canvas.width, canvas.height); gl.clearColor(0.5, 0.5, 0.5, 1); gl.clear(gl.COLOR_BUFFER_BIT);
    gl.useProgram(prog); gl.bindTexture(gl.TEXTURE_2D, tex); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4); };
  return { gl, tex, draw };
};
