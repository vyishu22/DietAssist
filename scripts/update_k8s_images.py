#!/usr/bin/env python3
"""Update k8s manifest image tags for backend and backup images.

Usage:
  python scripts/update_k8s_images.py --backend IMAGE --backup IMAGE

This script performs an in-place update of the following files:
- k8s/backend-deployment.yaml (container image under spec.template.spec.containers)
- k8s/backup-cronjob.yaml (cronjob container image)

It is intentionally conservative and uses simple string replacement based on the image name prefix.
"""
import argparse
import sys
from pathlib import Path


def replace_image_in_file(path: Path, image_prefix: str, new_image: str) -> bool:
    text = path.read_text()
    if image_prefix not in text:
        return False
    # Replace any image line that contains the prefix
    updated = []
    changed = False
    for line in text.splitlines():
        if image_prefix in line and 'image:' in line:
            indent = line[:line.index('image:')]
            updated_line = f"{indent}image: {new_image}"
            updated.append(updated_line)
            changed = True
        else:
            updated.append(line)
    if changed:
        path.write_text('\n'.join(updated) + "\n")
    return changed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--backend', required=True, help='Backend image full name (e.g., ghcr.io/org/dietassist-backend:sha)')
    parser.add_argument('--backup', required=True, help='Backup image full name (e.g., ghcr.io/org/dietassist-backup-tools:sha)')
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    backend_deploy = repo_root / 'k8s' / 'backend-deployment.yaml'
    backup_cron = repo_root / 'k8s' / 'backup-cronjob.yaml'

    modified = False

    if backend_deploy.exists():
        if replace_image_in_file(backend_deploy, 'dietassist-backend', args.backend):
            print(f'Updated backend deployment image to {args.backend}')
            modified = True
        else:
            print('No backend image line with prefix found; skipping')

    if backup_cron.exists():
        if replace_image_in_file(backup_cron, 'dietassist-backup-tools', args.backup):
            print(f'Updated backup CronJob image to {args.backup}')
            modified = True
        else:
            print('No backup image line with prefix found; skipping')

    if not modified:
        print('No files modified')
        sys.exit(0)


if __name__ == '__main__':
    main()
