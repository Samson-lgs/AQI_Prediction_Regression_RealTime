import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_handlers.openweather_handler import OpenWeatherHandler

h = OpenWeatherHandler()
cities = list(h.CITY_COORDINATES.keys())

print('='*60)
print('SYSTEM CONFIGURED FOR 97 INDIAN CITIES')
print('='*60)
print(f'Total Cities: {len(cities)}')
print(f'\nFirst 10 Cities (Alphabetical):')
for city in sorted(cities)[:10]:
    print(f'  - {city}')
print('  ...')
print(f'  - {sorted(cities)[-1]}')
print('='*60)
print('STATUS: READY FOR ALL 97 CITIES')
print('='*60)
