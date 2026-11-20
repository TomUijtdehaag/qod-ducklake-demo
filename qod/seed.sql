-- PROTOTYPE: tiny tables to exercise the policies. Run by carol (engineers) through QoD: `mise run seed`.
CREATE OR REPLACE TABLE qod.main.aircraft (hex VARCHAR, registration VARCHAR, operator VARCHAR, owner_email VARCHAR);
INSERT INTO qod.main.aircraft VALUES
    ('484506', 'PH-BXA', 'KLM',        'fleet@klm.example'),
    ('4851f6', 'PH-EXB', 'KLM Cityhopper', 'ops@cityhopper.example'),
    ('44d076', 'OO-SNA', 'Brussels Airlines', 'fleet@brusselsairlines.example'),
    ('3c6444', 'D-AIBD', 'Lufthansa',  'fleet@lufthansa.example');

CREATE OR REPLACE TABLE qod.main.position_reports (sample_time TIMESTAMP, hex VARCHAR, country VARCHAR, lat DOUBLE, lon DOUBLE, alt INTEGER);
INSERT INTO qod.main.position_reports VALUES
    ('2026-11-20 10:00:00', '484506', 'NL', 52.31, 4.76, 3000),
    ('2026-11-20 10:01:00', '484506', 'NL', 52.40, 4.95, 7000),
    ('2026-11-20 10:00:00', '4851f6', 'NL', 51.95, 4.44, 12000),
    ('2026-11-20 10:01:00', '4851f6', 'BE', 51.20, 4.40, 15000),
    ('2026-11-20 10:00:00', '44d076', 'BE', 50.90, 4.48, 2000),
    ('2026-11-20 10:01:00', '44d076', 'BE', 50.95, 4.10, 6000),
    ('2026-11-20 10:00:00', '3c6444', 'DE', 50.03, 8.57, 4000),
    ('2026-11-20 10:01:00', '3c6444', 'NL', 51.50, 6.10, 33000);
