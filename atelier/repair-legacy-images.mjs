import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { validateWorkspace } from './lib.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const workspacePath = path.join(root, 'data', 'atelier', 'workspace.json');
const historyDir = path.join(root, 'data', 'atelier', 'history');
const mapPath = path.join(root, 'build', 'image_files_map.json');

const workspace = JSON.parse(fs.readFileSync(workspacePath, 'utf8'));
const imageMap = JSON.parse(fs.readFileSync(mapPath, 'utf8'));
const before = JSON.stringify(workspace, null, 2) + '\n';
const restoredAt = new Date().toISOString();
let repaired = 0;
let preserved = 0;
let unavailable = 0;

function resolveLegacyFull(mappedPath) {
  if (!mappedPath) return null;
  if (fs.existsSync(path.join(root, mappedPath))) return mappedPath;
  const parsed = path.posix.parse(mappedPath);
  for (const extension of ['.jpg', '.jpeg', '.webp', '.png', '.svg']) {
    const candidate = path.posix.join(parsed.dir, `${parsed.name}${extension}`);
    if (fs.existsSync(path.join(root, candidate))) return candidate;
  }
  return null;
}

for (const entry of workspace.entries) {
  const image = entry.image || (entry.image = {});
  const thumb = String(image.thumb || '');
  const match = thumb.match(/^thumbs\/([^/]+)\/([^/.]+)\.[a-z0-9]+$/i);
  if (!match) continue;

  const [, listId, imageKey] = match;
  const legacyFull = resolveLegacyFull(imageMap[listId]?.[imageKey]);
  if (!legacyFull) {
    unavailable += 1;
    continue;
  }

  const isManual = [image.source, image.full]
    .some(value => String(value || '').startsWith('assets/atelier/'));
  if (isManual) {
    preserved += 1;
    continue;
  }

  image.source = legacyFull;
  image.full = legacyFull;
  image.thumb = thumb;
  image.crop ||= { cx: 0.5, cy: 0.5, w: 1 };
  image.provenance = {
    ...(image.provenance || {}),
    legacyFullRestored: legacyFull,
    restoredAt,
  };
  repaired += 1;
}

const errors = validateWorkspace(workspace);
if (errors.length) throw new Error(errors.join('\n'));

fs.mkdirSync(historyDir, { recursive: true });
const stamp = restoredAt.replace(/[:.]/g, '-');
fs.writeFileSync(path.join(historyDir, `${stamp}-before-full-image-repair.json`), before);
workspace.revision = Number(workspace.revision || 0) + 1;
workspace.updatedAt = restoredAt;
const temporaryPath = `${workspacePath}.tmp-${process.pid}`;
fs.writeFileSync(temporaryPath, JSON.stringify(workspace, null, 2) + '\n');
fs.renameSync(temporaryPath, workspacePath);

console.log(JSON.stringify({
  repaired,
  preserved,
  unavailable,
  revision: workspace.revision,
}, null, 2));
