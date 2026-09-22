import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.dirname(fileURLToPath(import.meta.url));
const assets = path.join(root, 'assets');
const logo = `data:image/jpeg;base64,${fs.readFileSync(path.join(root, '..', 'logo', 'logo.jpg')).toString('base64')}`;
const texture = `data:image/png;base64,${fs.readFileSync(path.join(assets, 'paper-strokes.png')).toString('base64')}`;
const ink = '#202725', paper = '#F7F2E9', gold = '#8A7046', mute = '#676F69';
const outer = (w, h, body) => `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img">${body}</svg>\n`;
const mark = (x,y,s) => `<svg x="${x}" y="${y}" width="${s}" height="${s}" viewBox="275 240 700 760"><image x="0" y="0" width="1254" height="1254" href="${logo}" xlink:href="${logo}"/></svg>`;
const title = (x,y,color=ink,size=125) => `<text x="${x}" y="${y}" fill="${color}" font-family="Georgia, 'Times New Roman', serif" font-size="${size}" font-weight="700" letter-spacing="-4">Strokera</text>`;
const rule = (x,y) => `<path d="M${x} ${y}h200" stroke="${gold}" stroke-width="5"/>`;
const header = outer(1600,500,`<image width="1600" height="500" href="${texture}" xlink:href="${texture}" preserveAspectRatio="xMidYMid slice"/><rect x="56" y="53" width="377" height="385" rx="12" fill="${paper}" opacity=".8"/>${mark(70,59,355)}${title(490,252)}${rule(495,280)}<text x="495" y="346" fill="${mute}" font-family="Arial,sans-serif" font-size="31" letter-spacing="3">THE PAINTING PROCESS PROTOCOL</text><text x="495" y="418" fill="${gold}" font-family="Georgia,serif" font-size="19" letter-spacing="4">LAYER  ·  STROKE  ·  REVISE</text>`);
const light = outer(1600,440,`<rect width="1600" height="440" fill="${paper}"/>${mark(83,42,350)}${title(495,219)}${rule(500,246)}<text x="500" y="317" fill="${mute}" font-family="Arial,sans-serif" font-size="32" letter-spacing="3">THE PAINTING PROCESS PROTOCOL</text>`);
const dark = outer(1600,440,`<rect width="1600" height="440" fill="${ink}"/><rect x="74" y="35" width="370" height="370" rx="14" fill="${paper}"/>${mark(84,45,350)}${title(505,219,paper)}${rule(510,246)}<text x="510" y="317" fill="#D2C7B4" font-family="Arial,sans-serif" font-size="32" letter-spacing="3">THE PAINTING PROCESS PROTOCOL</text>`);
const social = outer(1200,630,`<image width="1200" height="630" href="${texture}" xlink:href="${texture}" preserveAspectRatio="xMidYMid slice"/><rect x="44" y="83" width="430" height="466" rx="14" fill="${paper}" opacity=".86"/>${mark(75,105,400)}${title(505,279,ink,100)}${rule(510,306)}<text x="510" y="366" fill="${mute}" font-family="Arial,sans-serif" font-size="24" letter-spacing="2">THE PAINTING PROCESS PROTOCOL</text><text x="510" y="475" fill="${gold}" font-family="Georgia,serif" font-size="20" letter-spacing="3">FROM FUNCTION TO BRUSHSTROKE</text>`);
const avatar = outer(1024,1024,`<rect width="1024" height="1024" fill="${paper}"/>${mark(92,80,840)}`);
const icon = outer(512,512,`<rect width="512" height="512" rx="92" fill="${paper}"/>${mark(48,45,416)}`);
for (const [name, content] of Object.entries({'github-header.svg':header,'lockup-light.svg':light,'lockup-dark.svg':dark,'social-card.svg':social,'avatar.svg':avatar,'app-icon.svg':icon})) {
  fs.writeFileSync(path.join(assets,name),content,'utf8');
  process.stdout.write(`${name}\n`);
}
