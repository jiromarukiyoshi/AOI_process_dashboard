# AOI長泉倉庫進捗ダッシュボード backend

## 起動

```powershell
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
copy .env.example .env
.\venv\Scripts\python manage.py runserver 127.0.0.1:8000
```

`AOI_USE_MOCK_DATA=true` の場合はOracleへ接続せず、デモデータでAPIが動作します。
