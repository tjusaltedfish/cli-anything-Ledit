# Test Plan

1. Unit-test square-array geometry generation:
   - total box count equals `rows * cols`
   - bounding box matches origin, pitch, and square size
   - generated `.tco` uses L-Edit command-window syntax: `cell`, `layer`, `box -!`, `save`

2. Full CLI test:
   - invoke `cli_anything.ledit.ledit_cli` through Click's test runner
   - assert JSON receipt is valid
   - assert `.tco` and `.svg` files are written
   - assert the script contains one `box` command per square

3. Local backend inspection:
   - verify the configured L-Edit executable path is reported
   - do not require launching the commercial GUI in automated tests
