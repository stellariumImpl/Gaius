# README

初版骨架

```
/Users/felix/Desktop/Gaius
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── health.py
│   └── services/
│       └── __init__.py
├── .env
├── pyproject.toml
├── uv.lock
├── README.md
└── main.py
```

启动

```
uvicorn app.main:app --reload
```