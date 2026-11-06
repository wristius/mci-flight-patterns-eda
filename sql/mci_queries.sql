-- MCI Flight Patterns — SQL queries (SQLite, D426 practice)
-- Tables: airports, routes (OpenFlights raw), mci_outbound (cleaned, with distance)
-- Run: sqlite3 mci_flights.sqlite < sql/mci_queries.sql

-- 1. How many outbound routes does MCI have, and to how many destinations?
SELECT COUNT(*) AS outbound_routes,
       COUNT(DISTINCT dst) AS unique_destinations
FROM mci_outbound;

-- 2. Top 10 destinations from MCI by route count
SELECT dst_city, dst_country, COUNT(*) AS routes
FROM mci_outbound
GROUP BY dst_city, dst_country
ORDER BY routes DESC, dst_city
LIMIT 10;

-- 3. Routes by airline from MCI
SELECT airline, COUNT(*) AS routes
FROM mci_outbound
GROUP BY airline
ORDER BY routes DESC;

-- 4. Domestic vs international
SELECT CASE WHEN dst_country = 'United States' THEN 'Domestic'
            ELSE 'International' END AS scope,
       COUNT(*) AS routes
FROM mci_outbound
GROUP BY scope;

-- 5. Distance: shortest, longest, average, median is done in Python
SELECT MIN(distance_miles) AS shortest_mi,
       MAX(distance_miles) AS longest_mi,
       ROUND(AVG(distance_miles)) AS avg_mi
FROM mci_outbound;

-- 6. Longest routes from MCI
SELECT dst_city, dst_country, distance_miles
FROM mci_outbound
ORDER BY distance_miles DESC
LIMIT 10;

-- 7. Which destinations does MCI serve that no other route in the
--    outbound set duplicates? (one route per destination)
SELECT dst_city, COUNT(*) AS routes
FROM mci_outbound
GROUP BY dst_city
HAVING COUNT(*) = 1
ORDER BY dst_city;
