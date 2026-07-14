
"""
Cookie Validator
"""
import json
import argparse
from pathlib import Path
from src.browser import get_browser


class CookieValidator:
    PLATFORMS = {
        'sproutgigs': {'url': 'https://sproutgigs.com', 'login_indicator': 'dashboard'},
        'coinpayu': {'url': 'https://www.coinpayu.com', 'login_indicator': 'dashboard'},
        'timebucks': {'url': 'https://timebucks.com', 'login_indicator': 'dashboard'},
        'prizerebel': {'url': 'https://www.prizerebel.com', 'login_indicator': 'members'},
    }

    def validate_all(self):
        results = {}
        for name, config in self.PLATFORMS.items():
            results[name] = self._validate(name, config)
        return results

    def _validate(self, name, config):
        result = {'platform': name, 'valid': False, 'error': None}
        try:
            browser = get_browser()
            browser.start()
            browser.goto(config['url'], timeout=15000)

            current_url = browser.page.url if hasattr(browser, 'page') else ''
            result['current_url'] = current_url
            result['valid'] = config['login_indicator'] in current_url.lower()

            browser.close()
        except Exception as e:
            result['error'] = str(e)
        return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--platform', default='all')
    args = parser.parse_args()

    validator = CookieValidator()
    results = validator.validate_all() if args.platform == 'all' else {args.platform: validator._validate(args.platform, validator.PLATFORMS[args.platform])}

    with open('cookies_valid.json', 'w') as f:
        json.dump(results, f, indent=2)

    ready = sum(1 for r in results.values() if r['valid'])
    with open('platforms_ready.txt', 'w') as f:
        f.write(str(ready))

    print(f"Validated: {ready}/{len(results)} platforms ready")
    return 0 if ready > 0 else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
