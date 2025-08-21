#!/usr/bin/env python3
"""
Log Analytics Script for Request Metrics Analysis
Analyzes logs-insights-results.csv to extract request metrics by time periods
"""

import argparse
import csv
import json
from collections import Counter
from datetime import datetime
from typing import Dict, List, Tuple


class LogAnalyzer:
    def __init__(self, csv_file: str):
        self.csv_file = csv_file
        self.logs = []

    def parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp from CSV format: 2025-07-29 20:09:02.638"""
        return datetime.strptime(timestamp_str[:19], "%Y-%m-%d %H:%M:%S")

    def load_logs(self) -> None:
        """Load and parse log entries from CSV file"""
        print(f"Loading logs from {self.csv_file}...")

        with open(self.csv_file, "r", encoding="utf-8") as file:
            csv_reader = csv.reader(file)
            next(csv_reader)  # Skip header

            for row in csv_reader:
                if len(row) >= 2:
                    timestamp_str = row[0]
                    message = row[1]

                    try:
                        timestamp = self.parse_timestamp(timestamp_str)
                        self.logs.append(
                            {
                                "timestamp": timestamp,
                                "message": message,
                                "raw_timestamp": timestamp_str,
                            }
                        )
                    except ValueError as e:
                        print(f"Error parsing timestamp {timestamp_str}: {e}")
                        continue

        print(f"Loaded {len(self.logs)} log entries")

    def analyze_requests_by_day(self) -> Dict[str, int]:
        """Analyze requests grouped by day"""
        day_counts = Counter()

        for log in self.logs:
            day = log["timestamp"].strftime("%Y-%m-%d")
            day_counts[day] += 1

        return dict(day_counts)

    def analyze_requests_by_hour(self) -> Dict[str, int]:
        """Analyze requests grouped by hour"""
        hour_counts = Counter()

        for log in self.logs:
            hour = log["timestamp"].strftime("%Y-%m-%d %H:00")
            hour_counts[hour] += 1

        return dict(hour_counts)

    def analyze_requests_by_minute(self) -> Dict[str, int]:
        """Analyze requests grouped by minute"""
        minute_counts = Counter()

        for log in self.logs:
            minute = log["timestamp"].strftime("%Y-%m-%d %H:%M")
            minute_counts[minute] += 1

        return dict(minute_counts)

    def analyze_requests_by_hour_of_day(self) -> Dict[int, int]:
        """Analyze requests by hour of day (0-23)"""
        hour_of_day_counts = Counter()

        for log in self.logs:
            hour_of_day = log["timestamp"].hour
            hour_of_day_counts[hour_of_day] += 1

        return dict(hour_of_day_counts)

    def analyze_requests_by_minute_of_hour(self) -> Dict[int, int]:
        """Analyze requests by minute of hour (0-59)"""
        minute_of_hour_counts = Counter()

        for log in self.logs:
            minute_of_hour = log["timestamp"].minute
            minute_of_hour_counts[minute_of_hour] += 1

        return dict(minute_of_hour_counts)

    def get_top_n(self, data: Dict, n: int = 10) -> List[Tuple]:
        """Get top N entries from a dictionary sorted by value"""
        return sorted(data.items(), key=lambda x: x[1], reverse=True)[:n]

    def print_metrics(self) -> None:
        """Print comprehensive metrics analysis"""
        print("\n" + "=" * 80)
        print("LOG ANALYSIS METRICS REPORT")
        print("=" * 80)

        # Total requests
        total_requests = len(self.logs)
        print(f"\nTotal Requests: {total_requests:,}")

        if total_requests == 0:
            print("No data to analyze")
            return

        # Time range
        timestamps = [log["timestamp"] for log in self.logs]
        start_time = min(timestamps)
        end_time = max(timestamps)
        print(f"Time Range: {start_time} to {end_time}")
        print(f"Duration: {end_time - start_time}")

        # Daily analysis
        print("\n" + "-" * 50)
        print("TOP 10 DAYS WITH MOST REQUESTS")
        print("-" * 50)
        daily_data = self.analyze_requests_by_day()
        top_days = self.get_top_n(daily_data, 10)

        for i, (day, count) in enumerate(top_days, 1):
            percentage = (count / total_requests) * 100
            print(f"{i:2d}. {day}: {count:,} requests ({percentage:.2f}%)")

        # Hourly analysis (by specific hour)
        print("\n" + "-" * 50)
        print("TOP 10 HOURS WITH MOST REQUESTS")
        print("-" * 50)
        hourly_data = self.analyze_requests_by_hour()
        top_hours = self.get_top_n(hourly_data, 10)

        for i, (hour, count) in enumerate(top_hours, 1):
            percentage = (count / total_requests) * 100
            print(f"{i:2d}. {hour}: {count:,} requests ({percentage:.2f}%)")

        # Minute analysis
        print("\n" + "-" * 50)
        print("TOP 10 MINUTES WITH MOST REQUESTS")
        print("-" * 50)
        minute_data = self.analyze_requests_by_minute()
        top_minutes = self.get_top_n(minute_data, 10)

        for i, (minute, count) in enumerate(top_minutes, 1):
            percentage = (count / total_requests) * 100
            print(f"{i:2d}. {minute}: {count:,} requests ({percentage:.2f}%)")

        # Hour of day analysis (0-23)
        print("\n" + "-" * 50)
        print("REQUESTS BY HOUR OF DAY (0-23)")
        print("-" * 50)
        hour_of_day_data = self.analyze_requests_by_hour_of_day()
        top_hours_of_day = self.get_top_n(hour_of_day_data, 24)

        for i, (hour, count) in enumerate(top_hours_of_day, 1):
            percentage = (count / total_requests) * 100
            print(f"{i:2d}. Hour {hour:02d}: {count:,} requests ({percentage:.2f}%)")

        # Minute of hour analysis (0-59)
        print("\n" + "-" * 50)
        print("TOP 10 MINUTES OF HOUR (0-59)")
        print("-" * 50)
        minute_of_hour_data = self.analyze_requests_by_minute_of_hour()
        top_minutes_of_hour = self.get_top_n(minute_of_hour_data, 10)

        for i, (minute, count) in enumerate(top_minutes_of_hour, 1):
            percentage = (count / total_requests) * 100
            print(
                f"{i:2d}. Minute {minute:02d}: {count:,} requests ({percentage:.2f}%)"
            )

        print("\n" + "=" * 80)

    def export_to_json(self, output_file: str = None) -> None:
        """Export analysis results to JSON file"""
        if not output_file:
            output_file = "log_analysis_results.json"

        results = {
            "metadata": {
                "total_requests": len(self.logs),
                "analysis_timestamp": datetime.now().isoformat(),
                "source_file": self.csv_file,
            },
            "daily_requests": self.analyze_requests_by_day(),
            "hourly_requests": self.analyze_requests_by_hour(),
            "minute_requests": self.analyze_requests_by_minute(),
            "hour_of_day_requests": self.analyze_requests_by_hour_of_day(),
            "minute_of_hour_requests": self.analyze_requests_by_minute_of_hour(),
            "top_metrics": {
                "top_10_days": self.get_top_n(self.analyze_requests_by_day(), 10),
                "top_10_hours": self.get_top_n(self.analyze_requests_by_hour(), 10),
                "top_10_minutes": self.get_top_n(self.analyze_requests_by_minute(), 10),
                "top_10_hours_of_day": self.get_top_n(
                    self.analyze_requests_by_hour_of_day(), 10
                ),
                "top_10_minutes_of_hour": self.get_top_n(
                    self.analyze_requests_by_minute_of_hour(), 10
                ),
            },
        }

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\nResults exported to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Analyze log request metrics")
    parser.add_argument("csv_file", help="Path to the CSV log file")
    parser.add_argument("--json-output", help="Export results to JSON file")
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress console output"
    )

    args = parser.parse_args()

    analyzer = LogAnalyzer(args.csv_file)

    try:
        analyzer.load_logs()

        if not args.quiet:
            analyzer.print_metrics()

        if args.json_output:
            analyzer.export_to_json(args.json_output)

    except FileNotFoundError:
        print(f"Error: File '{args.csv_file}' not found")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0
