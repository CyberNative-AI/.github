-- lockcap(mode): lock distinct tables t1..t80000 in one transaction until an error; return count + SQLSTATE
CREATE OR REPLACE FUNCTION lockcap(lmode text, maxn int DEFAULT 80000,
  OUT n int, OUT state text, OUT msg text) AS $$
DECLARE i int;
BEGIN
  n := 0; state := 'CEILING'; msg := '';
  BEGIN
    FOR i IN 1..maxn LOOP
      EXECUTE format('LOCK TABLE %I IN %s MODE', 't' || i, lmode);
      n := n + 1;
    END LOOP;
  EXCEPTION WHEN OTHERS THEN
    state := SQLSTATE; msg := SQLERRM;
  END;
END $$ LANGUAGE plpgsql;
