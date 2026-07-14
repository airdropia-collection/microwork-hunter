
"""
Earnings Tracker
"""
import json
import glob
from datetime import datetime
from pathlib import Path


class EarningsTracker:
    def __init__(self):
        self.data_file = Path('earnings.json')
        self.data = self._load()

    def _load(self):
        if self.data_file.exists():
            with open(self.data_file) as f:
                return json.load(f)
        return {'total_earnings_usd': 0.0, 'total_earnings_satoshi': 0, 'total_earnings_points': 0,
                'platforms': {}, 'history': []}

    def update(self):
        for result_file in glob.glob('result_*.json'):
            try:
                with open(result_file) as f:
                    result = json.load(f)
                if result.get('status') != 'completed':
                    continue
                platform = result.get('platform', 'unknown')
                if platform not in self.data['platforms']:
                    self.data['platforms'][platform] = {'tasks_completed': 0, 'total_earned': 0.0, 'currency': 'USD'}
                self.data['platforms'][platform]['tasks_completed'] += 1
            except Exception as e:
                print(f"Error processing {result_file}: {e}")

        self.data['history'].append({
            'date': datetime.now().isoformat(),
            'total_earnings_usd': self.data['total_earnings_usd'],
            'platforms': self.data['platforms'].copy()
        })

        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)

        print(f"Earnings updated: {self.data['total_earnings_usd']} USD")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--update', action='store_true')
    args = parser.parse_args()

    tracker = EarningsTracker()
    if args.update:
        tracker.update()

    print(f"Total USD: ${tracker.data['total_earnings_usd']:.2f}")
    print(f"Total Satoshi: {tracker.data['total_earnings_satoshi']}")
    print(f"Total Points: {tracker.data['total_earnings_points']}")
    for platform, data in tracker.data['platforms'].items():
        print(f"  {platform}: {data['tasks_completed']} tasks | {data['total_earned']} {data['currency']}")


if __name__ == '__main__':
    main()
