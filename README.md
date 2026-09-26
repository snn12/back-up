# Desktop yedek (elsen-app-backup)

PC reset öncesi Desktop'taki opencode/AI projelerinin tek repoda yedeği (26.09.2026).

## İçerik

- `app.py` — MULTI PRO MMC Flask uygulaması (`Desktop/elsen/app.py`, 21.09.2026)
- `elsen-extra/` — uploads/, multipro.db, partner_logos/, screen/
- `aparatura/` — PyQt masaüstü uygulaması (main.py + app/*)
- `rsi/` — trading paneli (html + rsi_btc.py; orijinal git: snn12/rsi-panel, zaten push'lu)
- `trade/` — tools/*.py + knowledge/ (ham forexfactory verisi `data/` hariç ~53MB)
- `example/`, `example-2/`, `new-folder/`, `nat-site/` — küçük web denemeleri
- `nat-website/` — Next.js kurumsal site (node_modules/.next/.env hariç)

## Hariç tutulanlar

`node_modules/`, `.next/`, `.venv/`, iç `.git/`ler, `.env` dosyaları,
`*.exe`ler, `trade/data/forexfactory_raw/` (~53MB ham veri ayrıca yedeklenmeli).

## Çalıştırma

```bash
pip install Flask
python app.py
# prod: gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

Admin şifresi varsayılan `1234` (env `ADMIN_PASSWORD` ile override edilir).
