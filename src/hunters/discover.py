
"""
Task Discovery Orchestrator
"""
import json
import argparse
from typing import List, Dict, Any
from src.platforms.sproutgigs import SproutGigsPlatform
from src.platforms.coinpayu import CoinPayuPlatform
from src.platforms.timebucks import TimeBucksPlatform
from src.platforms.prizerebel import PrizeRebelPlatform


PLATFORM_MAP = {
    'sproutgigs': SproutGigsPlatform,
    'coinpayu': CoinPayuPlatform,
    'timebucks': TimeBucksPlatform,
    'prizerebel': PrizeRebelPlatform,
}


def discover_platform(platform_name: str, max_tasks: int = 5) -> List[Dict[str, Any]]:
    print(f"🔍 Discovering tasks from {platform_name}...")

    platform_class = PLATFORM_MAP.get(platform_name)
    if not platform_class:
        print(f"❌ Unknown platform: {platform_name}")
        return []

    try:
        with platform_class() as platform:
            tasks = platform.discover_tasks()
            tasks.sort(key=lambda t: t.reward / max(t.estimated_time, 1), reverse=True)
            tasks = tasks[:max_tasks]
            print(f"✅ Found {len(tasks)} tasks on {platform_name}")
            return [t.to_dict() for t in tasks]
    except Exception as e:
        print(f"❌ Error with {platform_name}: {e}")
        return []


def discover_all(max_tasks_per_platform: int = 5) -> List[Dict[str, Any]]:
    all_tasks = []
    for platform_name in PLATFORM_MAP.keys():
        tasks = discover_platform(platform_name, max_tasks_per_platform)
        all_tasks.extend(tasks)

    all_tasks.sort(key=lambda t: t.get('reward', 0) / max(t.get('estimated_time', 1), 1), reverse=True)
    return all_tasks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--platform', default='all', choices=['all', 'sproutgigs', 'coinpayu', 'timebucks', 'prizerebel'])
    parser.add_argument('--max-tasks', type=int, default=5)
    args = parser.parse_args()

    if args.platform == 'all':
        tasks = discover_all(args.max_tasks)
    else:
        tasks = discover_platform(args.platform, args.max_tasks)

    with open('tasks_found.json', 'w') as f:
        json.dump(tasks, f, indent=2)

    with open('tasks_found_count.txt', 'w') as f:
        f.write(str(len(tasks)))

    with open('discovery_log.json', 'w') as f:
        json.dump({'platform': args.platform, 'total_found': len(tasks), 'tasks': tasks}, f, indent=2)

    print(f"\\n📊 Total tasks discovered: {len(tasks)}")
    return 0 if len(tasks) > 0 else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
