# SchoolOS Web Preview

The public-facing preview for TechValorPK SchoolOS.

To run locally from this directory:

```bash
python -m http.server 8000
```

Open http://localhost:8000.

The root entry point is `index.html`. This is a static frontend prototype; records stay in browser localStorage and are not connected to a production database.