import csv
from collections import Counter

csv_path = r'c:\Users\florian\Desktop\logparser_results_20251222_213110_detail.csv'

with open(csv_path, encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))
    
types = [r['Type/Source'] for r in rows]
counter = Counter(types)

print(f'Gesamt Zeilen: {len(rows)}')
print(f'Unique Type/Source: {len(counter)}')
print(f'\nTop 10 haeufigste Duplikate:')
for typ, count in counter.most_common(10):
    display = typ[:70] + '...' if len(typ) > 70 else typ
    print(f'  {count}x: {display}')

print(f'\nSollte sein: {len(counter)} Zeilen')
print(f'Tatsaechlich: {len(rows)} Zeilen')
print(f'Reduzierung noetig: {len(rows) - len(counter)} Zeilen ({(len(rows) - len(counter))/len(rows)*100:.1f}%)')
