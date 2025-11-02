# ETL SBC — Execução no VS Code

## Passos rápidos
1. Crie e ative a venv (opcional, mas recomendado):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Confirme/edite as variáveis em **.env** (já configurado com password `1234`).

3. Rode pelo terminal:
   ```bash
   ./run_etl.sh
   ```
   ou diretamente:
   ```bash
   python etl_sbc_syslog_to_db.py --table public.syslog_events --limit 1000 --since-id 0 --debug
   ```

4. Rode pelo VS Code (F5):
   - O arquivo **.vscode/launch.json** já está pronto; ele usa o `.env` automaticamente.
   - Selecione a venv em *Python: Select Interpreter*.

## Dicas
- Para processar tudo, remova `--limit 1000` ou use `--limit all` (se suportado no script).
- Para pegar apenas registros após um ID:
  ```bash
  python etl_sbc_syslog_to_db.py --table public.syslog_events --since-id 12345
  ```
- Para reduzir a verbosidade, remova `--debug`.
