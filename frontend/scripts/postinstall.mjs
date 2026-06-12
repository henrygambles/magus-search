#!/usr/bin/env node
/**
 * Clears Gatekeeper quarantine flags on Next.js SWC binaries so dev server
 * can start instantly on macOS (otherwise Next compiles SWC from source).
 */
import { existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';

const isMac = process.platform === 'darwin';
if (!isMac) {
  process.exit(0);
}

const swcDir = join(process.cwd(), 'node_modules', '@next');
if (!existsSync(swcDir)) {
  process.exit(0);
}

const tag = '[magus postinstall]';
const xattrCheck = spawnSync('xattr', ['-h'], { stdio: 'ignore' });
if (xattrCheck.error) {
  console.warn(`${tag} xattr not available; run ./fix_macos_swc.sh manually if startup is slow.`);
  process.exit(0);
}

const result = spawnSync('xattr', ['-dr', 'com.apple.quarantine', swcDir], { stdio: 'ignore' });
if (result.status === 0) {
  console.log(`${tag} Cleared macOS quarantine flags for Next SWC binaries.`);
} else {
  console.warn(
    `${tag} Could not clear macOS quarantine flags (exit ${result.status}). Run ./fix_macos_swc.sh manually.`,
  );
}
