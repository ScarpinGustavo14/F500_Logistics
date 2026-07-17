"""
Calculadora de rotas para planilhas Google Sheets.

Lê uma planilha com colunas de origem e destino, calcula distância e
duração da rota (via OpenRouteService, gratuito) e escreve o resultado
de volta nas colunas correspondentes.

Uso:
    python route_calculator.py

Configuração: veja o arquivo .env.example.
"""
import os
import sys

from dotenv import load_dotenv

from cache import RouteCache
from routing_client import OpenRouteServiceClient, RoutingError
from sheets_client import SheetsClient

COL_ORIGEM = "Origem"
COL_DESTINO = "Destino"
COL_DISTANCIA = "Distância (km)"
COL_DURACAO = "Duração (min)"
COL_STATUS = "Status"


def main():
    load_dotenv()

    ors_api_key = os.getenv("ORS_API_KEY")
    service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "credentials.json")
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    worksheet_name = os.getenv("GOOGLE_WORKSHEET_NAME", "Rotas")

    if not sheet_id:
        sys.exit("GOOGLE_SHEET_ID não configurado. Veja o arquivo .env.example.")
    if not os.path.exists(service_account_file):
        sys.exit(
            f"Arquivo de credenciais '{service_account_file}' não encontrado. "
            "Veja o README para gerar a service account do Google."
        )

    cache = RouteCache()
    routing_client = OpenRouteServiceClient(api_key=ors_api_key, cache=cache)
    sheets_client = SheetsClient(service_account_file, sheet_id, worksheet_name)

    header, rows = sheets_client.read_rows()
    for col in (COL_ORIGEM, COL_DESTINO, COL_DISTANCIA, COL_DURACAO, COL_STATUS):
        if col not in header:
            sys.exit(
                f"A planilha precisa ter a coluna '{col}'. Colunas encontradas: {header}"
            )

    calculadas = 0
    puladas = 0
    com_erro = 0

    for row in rows:
        origem = row.get(COL_ORIGEM, "").strip()
        destino = row.get(COL_DESTINO, "").strip()
        distancia_existente = row.get(COL_DISTANCIA, "").strip()

        if not origem or not destino:
            continue
        if distancia_existente:
            puladas += 1
            continue

        row_number = row["_row_number"]
        try:
            resultado = routing_client.get_route(origem, destino)
        except RoutingError as e:
            sheets_client.update_cell(row_number, header, COL_STATUS, f"Erro: {e}")
            com_erro += 1
            print(f"[linha {row_number}] ERRO: {e}")
            continue

        sheets_client.update_cell(row_number, header, COL_DISTANCIA, resultado["distance_km"])
        sheets_client.update_cell(row_number, header, COL_DURACAO, resultado["duration_min"])
        sheets_client.update_cell(row_number, header, COL_STATUS, "OK")
        calculadas += 1
        print(
            f"[linha {row_number}] {origem} -> {destino}: "
            f"{resultado['distance_km']} km, {resultado['duration_min']} min"
        )

        cache.save()

    cache.save()
    print(
        f"\nConcluído. {calculadas} rota(s) calculada(s), "
        f"{puladas} já preenchida(s), {com_erro} com erro."
    )


if __name__ == "__main__":
    main()
