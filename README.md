# SuperCube Backend

FastAPI Highscore-Backend für das SuperCube Unity WebGL Spiel.

🔗 **Deploy auf Render.com**

## Setup

```bash
pip install -r requirements.txt
uvicorn main:app --reload
# Docs: http://localhost:8000/docs
```

## Endpunkte

| Methode | Pfad | Beschreibung |
|---------|------|-------------|
| GET | `/highscores` | Top-6 Highscores (Unity-kompatibles Format) |
| POST | `/highscores` | Neuen Highscore speichern |
| GET | `/highscores/all` | Alle Einträge (Debug) |
| DELETE | `/highscores/{id}` | Eintrag löschen (Admin-Key erforderlich) |

## Umgebungsvariablen (Render.com)

| Variable | Beschreibung | Beispiel |
|----------|-------------|---------|
| `ALLOWED_ORIGINS` | GitHub Pages URL | `https://michdo93.github.io` |
| `ADMIN_KEY` | Schlüssel für Delete-Route | Render generiert automatisch |
| `TOP_N` | Anzahl angezeigte Highscores | `6` |

## JSON-Format (kompatibel mit Unity)

**GET /highscores:**
```json
{
  "scores": [
    {"name": "Alice", "points": "9500"},
    {"name": "Bob",   "points": "8200"},
    {"name": "-",     "points": "-"}
  ]
}
```

**POST /highscores:**
```json
{"name": "Alice", "points": 9500}
```
