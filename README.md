
```bash
python -m uvicorn main:app --reload --port 8000
```
The API docs will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
### 4. Set Up the Frontend Next.js Client
In a separate terminal window:
```bash
cd frontend
# Install Node modules
npm install
# Run in development mode
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to access the customer support agent chat interface.
---
## 🧪 Testing & Validation
A suite of verification scripts are provided under `scripts/` to validate each layer of the architecture independently:
* **Intent Routing Test**: `python -m scripts.test_router`
* **Access Control Check**: Run `python -m scripts.test_query_service` to verify that cross-tenant queries raise explicit `AccountAccessError` exceptions.
* **Vector Retriever Evaluation**: `python -m scripts.test_retrieval`
* **Gemini Pipeline Check**: `python -m scripts.test_gemini` and `python -m scripts.test_generator`
---
## 🔒 Security Best Practices Implemented
> [!IMPORTANT]
> **Strict Tenant Context Mapping**
> Under no circumstances does the query interface allow executing requests without an `account_id`. Standard API endpoints require an explicit authorization parameter to bind execution to a single tenant context.
> [!WARNING]
> **Write Action Sanitization**
> No state-changing endpoints (e.g. status changes, updates, or deletions) permit query injections. Values are parsed, validated, and explicitly updated using SQLAlchemy transaction parameters rather than dynamic SQL strings.
