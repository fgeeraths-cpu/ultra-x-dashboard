"""Fix PLAN km targets and WEEKLY_DETAILS daily km to be consistent."""
import re

with open(r'C:\Users\fgeer\projects\ultra-x-dashboard\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# ── Corrected PLAN entries (only changed ones) ──
plan_fixes = {
    # wk: (km, longRun, key)
    5:  (55, 30, "'Tempo 6 km + hill repeats + B2B intro (30+10)'"),
    7:  (62, 32, "'Back-to-back weekend (32+12) + tempo'"),
    9:  (36, 22, "'Recovery week — easy + cross-training'"),
    10: (68, 35, "'B2B (35+15) + zandtraining'"),
    12: (75, 38, "'B2B (38+18) + mentale training'"),
    13: (56, 28, "'Recovery + race gear testen'"),
    16: (47, 25, "'Recovery — easy runs + sauna'"),
    22: (13, 5,  "'Shakeout runs. Mentale visualisatie.'"),
    23: (116, 60, "'Ma-Wo shakeout 3-5 km. Do rust. Vr 60 km + Za 50 km RACE!'"),
}

for wk, (km, lr, key) in plan_fixes.items():
    pattern = rf"(\{{wk:{wk},date:'[^']+',phase:'[^']+',)km:\d+,longRun:\d+,key:'[^']*'"
    def repl(m):
        return f"{m.group(1)}km:{km},longRun:{lr},key:{key}"
    html, n = re.subn(pattern, repl, html)
    if n == 0:
        # Try alternate key format
        pattern2 = rf"(\{{wk:{wk},date:'[^']+',phase:'[^']+',)km:\d+,longRun:\d+,key:\"[^\"]*\""
        html, n = re.subn(pattern2, repl, html)
    print(f"  PLAN wk{wk}: {'OK' if n else 'MISS'} -> km:{km}, longRun:{lr}")

# ── Corrected daily km values ──
# Format: wk: [Ma,Di,Wo,Do,Vr,Za,Zo]
daily_fixes = {
    1:  [0,6,6,4,5,24,0],       # was [0,8,8,6,7,24,0]=53 -> 45
    2:  [0,5,8,4,5,26,0],       # was [0,8,10,6,8,26,0]=58 -> 48
    3:  [0,6,8,4,6,28,0],       # was [0,8,10,6,8,28,0]=60 -> 52
    4:  [0,7,5,0,8,22,0],       # was [0,8,6,0,8,22,0]=44 -> 42
    5:  [0,4,6,2,3,30,10],      # was [0,8,10,7,6,30,12]=73 -> 55
    6:  [0,6,8,6,8,30,0],       # was [0,8,10,6,8,30,0]=62 -> 58
    7:  [0,4,8,3,3,32,12],      # was [0,9,12,7,7,32,15]=82 -> 62
    8:  [0,10,11,7,7,30,0],     # was [0,10,11,7,9,30,0]=67 -> 65
    # 9: no change (36=36, PLAN adjusts)
    10: [0,5,7,3,3,35,15],      # was [0,10,12,7,7,35,20]=91 -> 68
    # 11: no change (72=72)
    12: [0,6,7,3,3,38,18],      # was [0,10,10,7,6,38,22]=93 -> 75
    # 13: no change (56=56, PLAN adjusts)
    14: [0,3,5,0,4,38,25],      # was [0,10,12,7,7,38,25]=99 -> 75
    15: [0,3,5,4,3,40,25],      # was [0,8,12,7,7,40,25]=99 -> 80
    # 16: no change (47=47, PLAN adjusts)
    17: [0,3,6,3,3,38,25],      # was [0,10,10,7,7,38,25]=97 -> 78
    18: [0,3,6,3,3,38,22],      # was [0,10,10,7,8,38,22]=95 -> 75
    19: [0,8,8,6,8,25,0],       # was [0,10,10,6,8,25,0]=59 -> 55
    20: [0,8,8,0,9,20,0],       # was [0,8,8,0,7,20,0]=43 -> 45
    # 21: no change (35=35)
    # 22: no change (13=13, PLAN adjusts)
    # 23: no change (116=116, PLAN adjusts)
}

# For each week that needs daily fixes, replace km values in WEEKLY_DETAILS
for wk, new_kms in daily_fixes.items():
    # Find the week's array in WEEKLY_DETAILS
    # Pattern: wk: [\n    {day:'Ma',...,km:X},\n    ...7 days...\n  ],
    week_pattern = rf"({wk}:\s*\[)([\s\S]*?)(\],)"
    m = re.search(week_pattern, html)
    if not m:
        print(f"  DAILY wk{wk}: MISS - pattern not found")
        continue

    block = m.group(2)
    # Replace km values one by one (7 days)
    counter = [0]
    def replace_km(match):
        if counter[0] < len(new_kms):
            result = f"km:{new_kms[counter[0]]}"
            counter[0] += 1
            return result
        return match.group(0)

    new_block = re.sub(r'km:\d+', replace_km, block)
    html = html[:m.start(2)] + new_block + html[m.end(2):]

    total = sum(new_kms)
    print(f"  DAILY wk{wk}: OK -> [{','.join(str(k) for k in new_kms)}]={total}")

# ── Update milestone text ──
html = html.replace(
    'Eerste <strong>back-to-back</strong> weekend (25+20 km)',
    'Eerste <strong>back-to-back</strong> weekend (32+12 km)'
)
html = html.replace(
    '<strong>70+ km/week</strong>. B2B 30+20 km. Voedingsstrategie verfijnen.',
    '<strong>68+ km/week</strong>. B2B 35+15 km. Voedingsstrategie verfijnen.'
)
print("  Milestones: updated")

with open(r'C:\Users\fgeer\projects\ultra-x-dashboard\index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("\nDone! Verifying...")

# Verify all weeks match
import json
plan_match = re.findall(r'\{wk:(\d+).*?km:(\d+)', html)
plan_kms = {int(wk): int(km) for wk, km in plan_match}

week_pattern2 = re.findall(r'(\d+):\s*\[([\s\S]*?)\],',
    re.search(r'const WEEKLY_DETAILS = \{([\s\S]*?)\};', html).group(1))

all_ok = True
for wk_str, block in week_pattern2:
    wk = int(wk_str)
    kms = [int(x) for x in re.findall(r'km:(\d+)', block)]
    daily_sum = sum(kms)
    plan_km = plan_kms.get(wk, '?')
    if daily_sum != plan_km:
        print(f"  X Week {wk}: PLAN={plan_km} Daily={daily_sum} STILL MISMATCHED")
        all_ok = False
    else:
        print(f"  OK Week {wk}: {plan_km} km")

if all_ok:
    print("\nOK All 23 weeks are now consistent!")
else:
    print("\nX Some weeks still have mismatches")
