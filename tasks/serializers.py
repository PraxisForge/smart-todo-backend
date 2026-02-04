from datetime import datetime, timedelta
import re

from django.conf import settings
from rest_framework import serializers

from .models import Task

# Google Calendar helper (isolated usage)
from backend.calendar_helper import add_to_google_calendar

try:
    from zoneinfo import ZoneInfo
    USE_ZONEINFO = True
except Exception:
    import pytz
    USE_ZONEINFO = False


def get_tz():
    tz_name = getattr(settings, "TIME_ZONE", "UTC")
    if USE_ZONEINFO:
        return ZoneInfo(tz_name)
    return pytz.timezone(tz_name)


MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


class TaskSerializer(serializers.ModelSerializer):
    formatted_date = serializers.CharField(read_only=True)

    class Meta:
        model = Task
        fields = ["id", "title", "status", "priority", "due_date", "formatted_date"]
        read_only_fields = ["id", "formatted_date"]

    # ------------------------------------------------------------------
    # 1️⃣ PURE INPUT → DATE & TIME PARSER (REFERENCE LOGIC)
    # ------------------------------------------------------------------
    def _parse_natural_time(self, raw: str):
        tz = get_tz()
        now = datetime.now(tz)

        s = raw.strip()
        s_lower = s.lower()
        base_date = now.date()

        # ---- Explicit Date: 23 Mar 2026 / 05 Mar 26 ----
        m = re.search(
            r"\b(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{2,4})\b",
            s_lower,
        )
        if m:
            day = int(m.group(1))
            month = MONTH_MAP[m.group(2)]
            year = int(m.group(3))
            if year < 100:
                year += 2000
            base_date = datetime(year, month, day).date()
            s = re.sub(m.group(0), "", s, flags=re.I)
            s_lower = s.lower()

        # ---- Explicit Date: 23.05.26 ----
        m = re.search(r"\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b", s_lower)
        if m:
            day = int(m.group(1))
            month = int(m.group(2))
            year = int(m.group(3))
            if year < 100:
                year += 2000
            base_date = datetime(year, month, day).date()
            s = re.sub(m.group(0), "", s, flags=re.I)
            s_lower = s.lower()

        # ---- Relative Dates ----
        if "tomorrow" in s_lower:
            base_date = (now + timedelta(days=1)).date()
            s = re.sub(r"\btomorrow\b", "", s, flags=re.I)
            s_lower = s.lower()
        elif "today" in s_lower:
            base_date = now.date()
            s = re.sub(r"\btoday\b", "", s, flags=re.I)
            s_lower = s.lower()

        # ---- Time Parsing ----
        time_match = re.search(
            r"(?:at\s*)?((?:1[0-2]|0?[1-9])(?::[0-5]\d)?\s*(?:am|pm))\b",
            s_lower,
            flags=re.I,
        )
        if not time_match:
            time_match = re.search(
                r"(?:at\s*)?((?:[01]?\d|2[0-3]):[0-5]\d)\b", s_lower
            )

        due_dt = None
        if time_match:
            time_str = time_match.group(1)
            s = s[: time_match.start()] + s[time_match.end() :]

            ampm = re.search(r"(am|pm)", time_str, flags=re.I)
            if ampm:
                h = int(re.search(r"\d{1,2}", time_str).group())
                m = int(re.search(r":(\d{2})", time_str).group(1)) if ":" in time_str else 0
                if ampm.group(1).lower() == "pm" and h != 12:
                    h += 12
                if ampm.group(1).lower() == "am" and h == 12:
                    h = 0
            else:
                h, m = map(int, time_str.split(":"))

            due_dt = datetime(
                base_date.year,
                base_date.month,
                base_date.day,
                h,
                m,
                tzinfo=tz,
            )

        # ---- Clean Title ----
        s = re.sub(r"\b(at|on|by|in)\b", "", s, flags=re.I)
        cleaned_title = re.sub(r"\s+", " ", s).strip()

        return due_dt, cleaned_title

    # ------------------------------------------------------------------
    # 2️⃣ GOOGLE CALENDAR SYNC (SEPARATE, SAFE)
    # ------------------------------------------------------------------
    def _sync_google_calendar(self, task):
        if not task.due_date:
            return
        try:
            add_to_google_calendar(task.title, task.due_date)
        except Exception as e:
            print(f"Google Calendar Sync Error: {e}")

    # ------------------------------------------------------------------
    # 3️⃣ CREATE TASK
    # ------------------------------------------------------------------
    def create(self, validated_data):
        raw_title = validated_data.get("title", "").strip()

        # Parse input
        due_dt, cleaned_title = self._parse_natural_time(raw_title)

        # Priority detection
        urgent_keywords = ["urgent", "asap", "important", "critical", "deadline"]
        if any(k in raw_title.lower() for k in urgent_keywords):
            validated_data["priority"] = "High"

        validated_data["title"] = cleaned_title or raw_title
        if due_dt:
            validated_data["due_date"] = due_dt

        task = Task.objects.create(**validated_data)

        # Calendar sync (isolated)
        self._sync_google_calendar(task)

        return task

    # ------------------------------------------------------------------
    # 4️⃣ OUTPUT FORMAT
    # ------------------------------------------------------------------
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.due_date:
            dt = instance.due_date.astimezone(get_tz())
            data["formatted_date"] = dt.strftime("%b %d %Y, %I:%M %p")
        else:
            data["formatted_date"] = ""
        return data
