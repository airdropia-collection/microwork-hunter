
"""
Review Compiler
"""
import json
import glob
from pathlib import Path


def compile_review_package():
    result_files = glob.glob("result_*.json")
    pending, completed, failed = [], [], []

    for rf in result_files:
        try:
            with open(rf) as f:
                result = json.load(f)
            status = result.get('status', 'unknown')
            if status == 'dry_run':
                pending.append(result)
            elif status == 'completed':
                completed.append(result)
            elif status == 'failed':
                failed.append(result)
        except Exception as e:
            print(f"Error reading {rf}: {e}")

    discovered = 0
    try:
        with open('discovery_log.json') as f:
            log = json.load(f)
            discovered = log.get('total_found', 0)
    except:
        pass

    package = {
        'discovered': discovered,
        'attempted': len(result_files),
        'successful': len(completed),
        'failed': len(failed),
        'pending': pending,
        'completed': completed,
        'failed_tasks': failed,
        'summary': f"{len(pending)} pending, {len(completed)} completed, {len(failed)} failed"
    }

    with open('review_package.json', 'w') as f:
        json.dump(package, f, indent=2)

    print(f"Review package: {package['summary']}")
    return package


if __name__ == '__main__':
    compile_review_package()
