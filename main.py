from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import yaml

from tools.get_signals import get_signals


def load_config(config_path: str | Path = 'config.yaml') -> dict[str, Any]:
    with Path(config_path).open('r', encoding='utf-8') as handle:
        return yaml.safe_load(handle) or {}


def mask_secret(value: str | None) -> str:
    if not value:
        return '<missing>'
    if len(value) <= 8:
        return '***'
    return value[:4] + '...' + value[-4:]


def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    schedule = config.get('schedule', {})
    execution_enabled = os.getenv('EXECUTION_ENABLED', 'false').strip().lower() == 'true'
    return {
        'public_base_url': config.get('public', {}).get('base_url', ''),
        'wm_base_url': os.getenv('WM_BASE_URL', ''),
        'signal_interval_minutes': schedule.get('context_signals_interval_minutes', 15),
        'execution_enabled': bool(config.get('features', {}).get('execution_enabled', False) and execution_enabled),
        'public_token': mask_secret(os.getenv('PUBLIC_API_SECRET_KEY')),
        'wm_key': mask_secret(os.getenv('WORLDMONITOR_API_KEY')),
    }


def build_scheduler(config: dict[str, Any]) -> BackgroundScheduler:
    schedule = config.get('schedule', {})
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: asyncio.run(get_signals()),
        'interval',
        minutes=int(schedule.get('context_signals_interval_minutes', 15)),
        id='context_signals',
    )
    return scheduler


async def run_once(symbols: list[str] | None = None) -> dict[str, Any]:
    result = await get_signals(symbols=symbols)
    print('CONTEXT_SIGNALS:')
    print(json.dumps(result, indent=2, default=str))
    print('RUN_ONCE_RESULT:')
    print(json.dumps(result, indent=2, default=str))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description='Agent Oculus context-signal runtime')
    parser.add_argument('--config', default='config.yaml')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--run-once', action='store_true')
    parser.add_argument('--symbols', nargs='*', default=None)
    args = parser.parse_args()

    load_dotenv()

    config = load_config(args.config)
    summary = validate_config(config)
    print(json.dumps({'config_summary': summary}, indent=2))

    execution_state = 'execution ENABLED' if summary['execution_enabled'] else 'execution disabled'
    print(f'Agent Oculus ready | context signals active | {execution_state}')

    if args.run_once:
        asyncio.run(run_once(args.symbols))
        return

    scheduler = build_scheduler(config)
    scheduler.start()
    if args.dry_run:
        scheduler.shutdown(wait=False)
        return

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        scheduler.shutdown(wait=False)


if __name__ == '__main__':
    main()
