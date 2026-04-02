from __future__ import annotations

from flask import Flask, render_template, request

from services import CandleRequest, InvestError, fetch_candles, candles_to_dataframe, plot_candles_base64, sdk_name

# token в отдельном файле secrets.py (он в .gitignore)
try:
    from app_secrets import TINKOFF_TOKEN
except Exception:
    TINKOFF_TOKEN = ""


app = Flask(__name__)

TOP_COMPANIES = [
    {"name": "Сбербанк (ао)", "ticker": "SBER", "figi": "BBG004730N88"},
    {"name": "Роснефть", "ticker": "ROSN", "figi": "BBG004731354"},
    {"name": "Лукойл", "ticker": "LKOH", "figi": "BBG004731032"},
    {"name": "НОВАТЭК", "ticker": "NVTK", "figi": "BBG00475KKY8"},
    {"name": "Газпром", "ticker": "GAZP", "figi": "BBG004730RP0"},
    {"name": "ГМК Норильский никель", "ticker": "GMKN", "figi": "BBG004731489"},
    {"name": "Полюс", "ticker": "PLZL", "figi": "BBG000BN55S6"},
    {"name": "Татнефть (ао)", "ticker": "TATN", "figi": "BBG0047313P2"},
    {"name": "Сургутнефтегаз (ап)", "ticker": "SNGSP", "figi": "BBG0047315D0"},
    {"name": "Северсталь", "ticker": "CHMF", "figi": "BBG004730V44"},
]
COMPANY_BY_FIGI = {company["figi"]: company for company in TOP_COMPANIES}
DEFAULT_INSTRUMENT_ID = TOP_COMPANIES[0]["figi"]


@app.get("/")
def index():
    return render_template(
        "index.html",
        companies=TOP_COMPANIES,
        default_instrument_id=DEFAULT_INSTRUMENT_ID,
        default_days=10,
        default_interval="4h",
        sdk=sdk_name(),
    )


@app.post("/run")
def run():
    manual_instrument_id = (request.form.get("instrument_id") or "").strip()
    selected_instrument_id = (request.form.get("selected_instrument_id") or "").strip()
    instrument_id = manual_instrument_id or selected_instrument_id
    interval = (request.form.get("interval") or "4h").strip()
    company = COMPANY_BY_FIGI.get(instrument_id)

    try:
        days_back = int(request.form.get("days_back") or "10")
    except ValueError:
        return render_template("error.html", message="Количество дней должно быть целым числом."), 400

    if not instrument_id:
        return render_template("error.html", message="Введите FIGI вручную или выберите компанию из списка."), 400

    if not 1 <= days_back <= 365:
        return render_template("error.html", message="Количество дней должно быть в диапазоне от 1 до 365."), 400

    if not TINKOFF_TOKEN:
        return render_template(
            "error.html",
            message="Не найден токен. Создайте файл app_secrets.py рядом с app.py и задайте TINKOFF_TOKEN.",
        ), 500

    try:
        candles = fetch_candles(
            TINKOFF_TOKEN,
            CandleRequest(instrument_id=instrument_id, days_back=days_back, interval=interval),
        )
        df = candles_to_dataframe(candles)
        chart_uri = plot_candles_base64(df)
        # покажем первые строки таблицы, чтобы не перегружать страницу
        table_html = df.tail(30).to_html(classes="table", border=0)
        return render_template(
            "result.html",
            company=company,
            manual_instrument_id=manual_instrument_id,
            instrument_id=instrument_id,
            days_back=days_back,
            interval=interval,
            chart_uri=chart_uri,
            table_html=table_html,
            sdk=sdk_name(),
            n=len(df),
        )
    except InvestError as e:
        return render_template("error.html", message=str(e)), 400


if __name__ == "__main__":
    app.run(debug=True)
