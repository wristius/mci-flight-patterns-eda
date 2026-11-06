#!/usr/bin/env python3
"""MCI Flight Patterns — Exploratory Data Analysis.
Source: OpenFlights (jpatokal/openflights), airports/routes/airlines data.
Public data, downloaded Nov 6, 2026. No invented numbers: every finding
below is computed from these files in this script.
"""
import csv, math, sqlite3, pathlib
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = pathlib.Path('/home/hatch/workspace/projects/mci-flight-patterns-eda')
DATA = ROOT / 'data'
CHARTS = ROOT / 'charts'

AIR_COLS = ['airport_id','name','city','country','iata','icao','lat','lon',
            'altitude_ft','timezone','dst','tz','type','source']
ROUTE_COLS = ['airline','airline_id','src','src_id','dst','dst_id',
              'codeshare','stops','equipment']
LINE_COLS = ['airline_id','name','alias','iata','icao','callsign',
             'country','active']

air = pd.read_csv(DATA/'airports.dat', header=None, names=AIR_COLS,
                  dtype=str, na_filter=False)
routes = pd.read_csv(DATA/'routes.dat', header=None, names=ROUTE_COLS,
                     dtype=str, na_filter=False)
lines = pd.read_csv(DATA/'airlines.dat', header=None, names=LINE_COLS,
                    dtype=str, na_filter=False)

air['lat'] = pd.to_numeric(air['lat'], errors='coerce')
air['lon'] = pd.to_numeric(air['lon'], errors='coerce')
air_by_iata = air.set_index('iata')
mci = air_by_iata.loc['MCI']
print(f"MCI: {mci['name']}, {mci['city']}, {mci['country']}, "
      f"lat {mci['lat']}, lon {mci['lon']}, alt {mci['altitude_ft']} ft")

out = routes[routes['src'] == 'MCI'].copy()
inn = routes[routes['dst'] == 'MCI'].copy()
print(f"Outbound routes from MCI: {len(out)}")
print(f"Inbound routes to MCI: {len(inn)}")

def haversine(lat1, lon1, lat2, lon2):
    r = 3959  # miles
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlmb/2)**2
    return 2 * r * math.asin(math.sqrt(a))

# Enrich outbound routes with destination airport info + distance
rows = []
for _, r in out.iterrows():
    if r['dst'] in air_by_iata.index:
        d = air_by_iata.loc[r['dst']]
        dist = haversine(float(mci['lat']), float(mci['lon']),
                         float(d['lat']), float(d['lon']))
        rows.append({'airline': r['airline'], 'dst': r['dst'],
                     'dst_city': d['city'], 'dst_country': d['country'],
                     'dst_lat': float(d['lat']), 'dst_lon': float(d['lon']),
                     'stops': int(r['stops']), 'codeshare': r['codeshare'],
                     'equipment': r['equipment'],
                     'distance_miles': round(dist)})
mci_out = pd.DataFrame(rows)
mci_out.to_csv(ROOT/'mci_outbound_routes.csv', index=False)

findings = []
findings.append(f"Outbound routes from MCI: {len(mci_out)}")
findings.append(f"Unique destinations from MCI: {mci_out['dst'].nunique()}")
findings.append(f"Unique airlines from MCI: {mci_out['airline'].nunique()}")
dom = (mci_out['dst_country'] == 'United States').sum()
findings.append(f"Domestic destinations: {dom} ({dom/len(mci_out)*100:.1f}%), "
               f"international: {len(mci_out)-dom}")
findings.append(f"Nonstop routes (0 stops): {(mci_out['stops']==0).sum()}, "
               f"with stops: {(mci_out['stops']>0).sum()}")
findings.append(f"Distance: median {mci_out['distance_miles'].median():.0f} mi, "
               f"mean {mci_out['distance_miles'].mean():.0f} mi, "
               f"longest {mci_out['distance_miles'].max():.0f} mi "
               f"({mci_out.loc[mci_out['distance_miles'].idxmax(),'dst_city']}), "
               f"shortest {mci_out['distance_miles'].min():.0f} mi "
               f"({mci_out.loc[mci_out['distance_miles'].idxmin(),'dst_city']})")
top_dest = mci_out['dst_city'].value_counts().head(10)
findings.append("Top destinations by route count:\n" +
                "\n".join(f"  {c}: {n}" for c, n in top_dest.items()))
top_air = mci_out['airline'].value_counts().head(10)
# map airline codes to names where known
line_names = lines.set_index('iata')['name'].to_dict()
findings.append("Top airlines by outbound routes:\n" +
                "\n".join(f"  {code} ({line_names.get(code,'?')}): {n}"
                          for code, n in top_air.items()))

for f in findings:
    print(f)

# --- SQLite (D426 practice): load the same data, answer in SQL ---
db = ROOT/'mci_flights.sqlite'
if db.exists():
    db.unlink()
con = sqlite3.connect(db)
air.to_sql('airports', con, index=False)
routes.to_sql('routes', con, index=False)
mci_out.to_sql('mci_outbound', con, index=False)
sql_checks = {
    'outbound_count': "SELECT COUNT(*) FROM mci_outbound",
    'destinations': "SELECT COUNT(DISTINCT dst) FROM mci_outbound",
    'top_airline': ("SELECT airline, COUNT(*) c FROM mci_outbound "
                    "GROUP BY airline ORDER BY c DESC LIMIT 1"),
    'avg_distance': "SELECT ROUND(AVG(distance_miles)) FROM mci_outbound",
}
for name, q in sql_checks.items():
    print(name, con.execute(q).fetchall())
con.close()

# --- Charts ---
plt.rcParams.update({'font.size': 10})
# 1. Top destinations
top15 = mci_out['dst_city'].value_counts().head(15).sort_values()
fig, ax = plt.subplots(figsize=(9, 6))
top15.plot.barh(ax=ax, color='#2B59C3')
ax.set_xlabel('Outbound routes from MCI')
ax.set_title('Top 15 destinations from Kansas City (MCI)')
fig.tight_layout(); fig.savefig(CHARTS/'top_destinations.png', dpi=150); plt.close(fig)

# 2. Routes by airline
by_air = mci_out['airline'].value_counts().head(10).sort_values()
labels = [f"{c} ({line_names.get(c,'?')})" for c in by_air.index]
fig, ax = plt.subplots(figsize=(9, 5))
ax.barh(labels, by_air.values, color='#D9A81C')
ax.set_xlabel('Outbound routes from MCI')
ax.set_title('Outbound routes from MCI by airline')
fig.tight_layout(); fig.savefig(CHARTS/'routes_by_airline.png', dpi=150); plt.close(fig)

# 3. Distance distribution
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(mci_out['distance_miles'], bins=15, color='#2B59C3', edgecolor='white')
ax.set_xlabel('Distance from MCI (miles)')
ax.set_ylabel('Routes')
ax.set_title('How far do flights from MCI go?')
fig.tight_layout(); fig.savefig(CHARTS/'distance_distribution.png', dpi=150); plt.close(fig)

# 4. Route map (lat/lon, no basemap needed for a portfolio chart)
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(mci_out['dst_lon'], mci_out['dst_lat'], s=18, color='#2B59C3', alpha=0.8)
for _, r in mci_out.iterrows():
    ax.plot([float(mci['lon']), r['dst_lon']],
            [float(mci['lat']), r['dst_lat']], color='#2B59C3', alpha=0.15, lw=0.7)
ax.scatter([float(mci['lon'])], [float(mci['lat'])], s=120, color='#D9A81C',
           marker='*', zorder=5)
ax.set_xlabel('Longitude'); ax.set_ylabel('Latitude')
ax.set_title('Routes out of Kansas City (MCI) — gold star is MCI')
fig.tight_layout(); fig.savefig(CHARTS/'route_map.png', dpi=150); plt.close(fig)

(ROOT/'FINDINGS.txt').write_text("\n\n".join(findings) + "\n")
print("Charts:", sorted(p.name for p in CHARTS.glob('*.png')))
