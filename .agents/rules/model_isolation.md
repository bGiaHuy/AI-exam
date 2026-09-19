# Model Isolation & Protection Rule

## Boundary Contract:
- **DO NOT TOUCH `model/`**: Never create, modify, overwrite, refactor, or delete any file in the `model/` directory (e.g. `model/exam_analyzer.py`, `model/test_demo.py`, `model/api_server.py`, or any files in `model/weights/`).
- The AI detection models, weights, pose estimation math, and behavior detection heuristics are exclusively managed and completed by the user.
- The assistant's scope is strictly bounded to the surrounding application:
  1. **Frontend**: React, Tailwind CSS, components, monitors, matrix views, report modals, video evidence players.
  2. **Backend**: FastAPI endpoints, SQLite database (WAL mode), incident persistence, evidence serving, ring buffer streaming.
