#!/usr/bin/env python3
"""soul-diff: Compare two snapshots and generate a diff report."""

import json
import sys
import os

def load_snapshot(path):
    with open(path) as f:
        return json.load(f)

def diff_snapshots(old_path, new_path):
    old = load_snapshot(old_path)
    new = load_snapshot(new_path)
    
    old_files = {f['path']: f for f in old['files']}
    new_files = {f['path']: f for f in new['files']}
    
    all_paths = set(list(old_files.keys()) + list(new_files.keys()))
    
    changed = []
    unchanged = []
    added_files = []
    removed_files = []
    
    for path in sorted(all_paths):
        if path not in old_files:
            added_files.append(path)
            continue
        if path not in new_files:
            removed_files.append(path)
            continue
        if old_files[path]['hash'] == new_files[path]['hash']:
            unchanged.append(path)
            continue
        
        # File changed — find which sections changed
        old_sections = {s['heading']: s for s in old_files[path].get('sections', [])}
        new_sections = {s['heading']: s for s in new_files[path].get('sections', [])}
        
        all_headings = set(list(old_sections.keys()) + list(new_sections.keys()))
        section_changes = []
        
        for heading in sorted(all_headings):
            if heading not in old_sections:
                section_changes.append({
                    'section': heading,
                    'type': 'added',
                    'newLines': new_sections[heading]['lineCount']
                })
            elif heading not in new_sections:
                section_changes.append({
                    'section': heading,
                    'type': 'removed',
                    'oldLines': old_sections[heading]['lineCount']
                })
            elif old_sections[heading]['hash'] != new_sections[heading]['hash']:
                section_changes.append({
                    'section': heading,
                    'type': 'modified',
                    'oldLines': old_sections[heading]['lineCount'],
                    'newLines': new_sections[heading]['lineCount'],
                    'lineDelta': new_sections[heading]['lineCount'] - old_sections[heading]['lineCount']
                })
        
        old_size = old_files[path].get('sizeBytes', old_files[path].get('size', 0))
        new_size = new_files[path].get('sizeBytes', new_files[path].get('size', 0))
        size_delta = new_size - old_size
        
        changed.append({
            'file': path,
            'sizeDelta': size_delta,
            'sectionChanges': section_changes,
            'sectionsAdded': len([s for s in section_changes if s['type'] == 'added']),
            'sectionsRemoved': len([s for s in section_changes if s['type'] == 'removed']),
            'sectionsModified': len([s for s in section_changes if s['type'] == 'modified']),
        })
    
    report = {
        'oldSnapshot': old['timestamp'],
        'newSnapshot': new['timestamp'],
        'timeDelta': f"{old['timestamp']} → {new['timestamp']}",
        'ageDelta': f"day {old.get('agent',{}).get('dayAge','?')} → day {new.get('agent',{}).get('dayAge','?')}",
        'summary': {
            'filesChanged': len(changed),
            'filesUnchanged': len(unchanged),
            'filesAdded': len(added_files),
            'filesRemoved': len(removed_files),
        },
        'changedFiles': changed,
        'unchangedFiles': unchanged,
        'addedFiles': added_files,
        'removedFiles': removed_files,
    }
    
    return report

def print_report(report):
    print(f"soul-diff: {report['timeDelta']}")
    print(f"  Age: {report['ageDelta']}")
    print(f"  Changed: {report['summary']['filesChanged']} | "
          f"Unchanged: {report['summary']['filesUnchanged']} | "
          f"Added: {report['summary']['filesAdded']} | "
          f"Removed: {report['summary']['filesRemoved']}")
    print()
    
    for cf in report['changedFiles']:
        sign = '+' if cf['sizeDelta'] >= 0 else ''
        print(f"  📝 {cf['file']} ({sign}{cf['sizeDelta']}B)")
        for sc in cf['sectionChanges']:
            if sc['type'] == 'added':
                print(f"    ✅ ADDED: \"{sc['section']}\" ({sc['newLines']} lines)")
            elif sc['type'] == 'removed':
                print(f"    ❌ REMOVED: \"{sc['section']}\" ({sc['oldLines']} lines)")
            elif sc['type'] == 'modified':
                sign2 = '+' if sc['lineDelta'] >= 0 else ''
                print(f"    ✏️  MODIFIED: \"{sc['section']}\" ({sign2}{sc['lineDelta']} lines)")
        print()
    
    if report['addedFiles']:
        for f in report['addedFiles']:
            print(f"  🆕 {f}")
    if report['removedFiles']:
        for f in report['removedFiles']:
            print(f"  🗑️  {f}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: diff.py <old_snapshot.json> <new_snapshot.json> [--json]")
        sys.exit(1)
    
    report = diff_snapshots(sys.argv[1], sys.argv[2])
    
    if '--json' in sys.argv:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)
