## 2024-05-18 - Missing functools.lru_cache for CSV loading
**Learning:** Loading CSV data for FastAPI endpoints without caching can become a bottleneck when calling `/athletes` or `/events-csv` repeatedly.
**Action:** Add caching mechanism to static file loads.
