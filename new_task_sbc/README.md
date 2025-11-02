# VS Code setup — task_sbc_standalone.py

## Passos
1. Crie a venv e instale as deps
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Ajuste `.env` se necessário (já vem com 127.0.0.1:15432 test_db sysloguser/1234).
3. Rode pelo terminal:
   ```bash
   ./run_standalone.sh
   ```
4. Ou rode pelo VS Code: **Run and Debug → "Standalone: analysis"** (F5).

## Linha de comando equivalente
```bash
python task_sbc_standalone.py       --dsn "host=127.0.0.1 port=15432 dbname=test_db user=sysloguser password=1234"       --ranges-only --quiet-missing-clients       --log-file sbc_debug.log --log-sql-level INFO       analysis
```
