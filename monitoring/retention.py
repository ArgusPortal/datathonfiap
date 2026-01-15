"""
Data Retention Script - Limpeza de dados antigos.
Fase 8: Hardening de Produção.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import BASE_DIR, RETENTION_DAYS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("retention")

# Files subject to retention policy
RETENTION_TARGETS = [
    "logs/inference_store.jsonl",
    "logs/drift_events.jsonl",
    "monitoring/inference_store.jsonl",
]


def get_cutoff_date(retention_days: int) -> datetime:
    """Calculate cutoff date for retention."""
    return datetime.now(timezone.utc) - timedelta(days=retention_days)


def filter_jsonl_file(
    filepath: Path,
    cutoff_date: datetime,
    timestamp_field: str = "timestamp",
    dry_run: bool = False,
) -> dict:
    """
    Filter JSONL file to remove records older than cutoff date.
    
    Returns:
        dict with statistics: total_records, removed_records, retained_records
    """
    if not filepath.exists():
        logger.info(f"File not found, skipping: {filepath}")
        return {"total": 0, "removed": 0, "retained": 0, "skipped": True}
    
    total = 0
    removed = 0
    retained_lines = []
    
    # Make cutoff_date offset-naive for comparison if needed
    cutoff_naive = cutoff_date.replace(tzinfo=None) if cutoff_date.tzinfo else cutoff_date
    
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            total += 1
            try:
                record = json.loads(line)
                ts_str = record.get(timestamp_field)
                
                if ts_str:
                    # Handle ISO format timestamps - normalize to naive UTC
                    ts_clean = ts_str.replace("Z", "+00:00")
                    ts = datetime.fromisoformat(ts_clean)
                    # Convert to naive (strip tzinfo) for comparison
                    ts_naive = ts.replace(tzinfo=None)
                    
                    if ts_naive < cutoff_naive:
                        removed += 1
                        continue
                
                retained_lines.append(line)
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Could not parse line in {filepath}: {e}")
                retained_lines.append(line)  # Keep unparseable lines
    
    retained = len(retained_lines)
    
    if not dry_run and removed > 0:
        # Write filtered content back
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(retained_lines))
            if retained_lines:
                f.write("\n")
        logger.info(f"Updated {filepath}: removed {removed}/{total} records")
    else:
        logger.info(f"Would update {filepath}: remove {removed}/{total} records (dry_run={dry_run})")
    
    return {"total": total, "removed": removed, "retained": retained, "skipped": False}


def cleanup_old_logs(
    base_dir: Path,
    retention_days: int,
    dry_run: bool = False,
) -> dict:
    """
    Clean up old log files based on retention policy.
    
    Returns:
        Summary of cleanup operations.
    """
    cutoff = get_cutoff_date(retention_days)
    logger.info(f"Retention policy: {retention_days} days, cutoff date: {cutoff.isoformat()}")
    
    summary = {
        "retention_days": retention_days,
        "cutoff_date": cutoff.isoformat(),
        "dry_run": dry_run,
        "files": {},
    }
    
    for target in RETENTION_TARGETS:
        filepath = base_dir / target
        result = filter_jsonl_file(filepath, cutoff, dry_run=dry_run)
        summary["files"][target] = result
    
    # Calculate totals
    total_removed = sum(f["removed"] for f in summary["files"].values())
    total_retained = sum(f["retained"] for f in summary["files"].values())
    
    summary["totals"] = {
        "removed": total_removed,
        "retained": total_retained,
    }
    
    return summary


def cleanup_old_files_by_mtime(
    directory: Path,
    retention_days: int,
    pattern: str = "*.log",
    dry_run: bool = False,
) -> dict:
    """
    Clean up old files based on modification time.
    """
    cutoff_ts = (datetime.now(timezone.utc) - timedelta(days=retention_days)).timestamp()
    
    removed = []
    retained = []
    
    if not directory.exists():
        return {"removed": [], "retained": [], "skipped": True}
    
    for f in directory.glob(pattern):
        if f.is_file():
            if f.stat().st_mtime < cutoff_ts:
                if not dry_run:
                    f.unlink()
                removed.append(str(f))
                logger.info(f"{'Would remove' if dry_run else 'Removed'}: {f}")
            else:
                retained.append(str(f))
    
    return {"removed": removed, "retained": retained, "skipped": False}


def main():
    parser = argparse.ArgumentParser(
        description="Data retention cleanup script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run with default retention
  python retention.py --dry-run
  
  # Apply retention with custom days
  python retention.py --days 7
  
  # Also clean old log files
  python retention.py --include-logs
        """,
    )
    
    parser.add_argument(
        "--days",
        type=int,
        default=RETENTION_DAYS,
        help=f"Retention period in days (default: {RETENTION_DAYS})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--include-logs",
        action="store_true",
        help="Also clean old .log files by modification time",
    )
    parser.add_argument(
        "--output-json",
        action="store_true",
        help="Output results as JSON",
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Data Retention Cleanup")
    logger.info("=" * 60)
    
    # Run JSONL cleanup
    summary = cleanup_old_logs(BASE_DIR, args.days, dry_run=args.dry_run)
    
    # Optionally clean old log files
    if args.include_logs:
        logs_dir = BASE_DIR / "logs"
        log_cleanup = cleanup_old_files_by_mtime(
            logs_dir, args.days, pattern="*.log", dry_run=args.dry_run
        )
        summary["log_files"] = log_cleanup
    
    # Output
    if args.output_json:
        print(json.dumps(summary, indent=2))
    else:
        logger.info("-" * 60)
        logger.info("Summary:")
        logger.info(f"  Retention period: {args.days} days")
        logger.info(f"  Dry run: {args.dry_run}")
        logger.info(f"  Total records removed: {summary['totals']['removed']}")
        logger.info(f"  Total records retained: {summary['totals']['retained']}")
        
        for filename, stats in summary["files"].items():
            if not stats.get("skipped"):
                logger.info(f"  {filename}: removed {stats['removed']}, retained {stats['retained']}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
