"""Malaysia Prayer Time UVX Plugin."""


def get_prayer_times(zone: str):
    """Get prayer times for a specific zone in Malaysia."""
    return {
        "content": [
            {
                "type": "text",
                "text": f"Prayer times for {zone}: Fajr 5:30, Dhuhr 12:30, Asr 16:00, Maghrib 19:00, Isha 20:30",
            }
        ]
    }


def list_zones():
    """List all available prayer time zones in Malaysia."""
    return {
        "content": [
            {
                "type": "text",
                "text": "SGR01: Gombak (Selangor)\nKUL01: Kuala Lumpur (W.P. Kuala Lumpur)\nJHR01: Pulau Aur (Johor)",
            }
        ]
    }


def get_current_prayer(zone: str):
    """Get the current prayer time status for a specific zone."""
    return {
        "content": [
            {
                "type": "text",
                "text": f"Current prayer for {zone}: Asr (16:00), Next: Maghrib (19:00), Remaining: 3:00",
            }
        ]
    }
