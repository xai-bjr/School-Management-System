# TechValorPK SchoolOS — Web Experience Preview

A browser-first visual prototype of a modern school operations workspace, built with semantic HTML5, CSS3, JavaScript ES modules and Three.js r187.

## Preview features

- Animated TechValorPK startup sequence with a source-line loading terminal.
- Three.js 3D campus hero, preferring WebGPU and falling back to WebGL 2.
- Responsive dark/light workspace with 3D-lift cards and tactile button states.
- Overview dashboard, attendance chart, campus schedule, activity feed and quick actions.
- Students, faculty, classes, attendance, examinations, fees, library, transport, analytics and calendar views.
- Command palette (Ctrl/Cmd + K), keyboard focus states and responsive mobile sidebar.
- Add-student demo flow and CSV export; demo records persist in browser localStorage.

## Run locally

Serve the `web` directory over HTTP; ES modules and import maps should not be opened as a `file://` URL.

```bash
cd web
python -m http.server 8000
```

Open http://localhost:8000.

Three.js r187 is loaded from jsDelivr using the official import-map pattern. Keep all Three.js imports pinned to the same version and CDN. Internet access is required for the 3D module and hosted fonts; the SVG campus illustration remains as a fallback.

## GitHub Pages

The workflow at `.github/workflows/deploy-school-web.yml` publishes the `web/` directory when code is pushed to branch `web/techvalorpk-threejs-demo`.

For the first deployment, open repository **Settings → Pages** and choose **GitHub Actions** as the build and deployment source. Then open **Actions** and confirm that the deployment workflow succeeds.

## Important scope and security note

This is a front-end demonstration, not a production school database or authentication system. Student records added in the preview are stored only in the current browser's localStorage. The sample people, attendance, fee and activity data are fictional. Do not enter real student or staff information.

A production deployment needs a server-side API, database, authentication, role-based authorization, backups, audit controls, validation, privacy protections and HTTPS configuration. GitHub Pages is static hosting and cannot safely provide those server-side functions by itself.