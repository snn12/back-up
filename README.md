# elsen-app-backup

PC reset öncesi yedek. `natttt` klasöründe sadece `__pycache__/app.cpython-314.pyc` kalmıştı,
gerçek kaynak `elsen/app.py` (21.09.2026) buraya geri kopyalandı.

## İçerik

- `app.py` — MULTI PRO MMC Flask uygulaması (tek dosya, 1493 satır)
- Orijinal proje: `Desktop/elsen/` (multipro.db, uploads/, partner_logos/, screen/)

## Çalıştırma

```bash
pip install Flask
python app.py
# prod: gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

Admin şifresi varsayılan `1234` (env `ADMIN_PASSWORD` ile override edilir).
