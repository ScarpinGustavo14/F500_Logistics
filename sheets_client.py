import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]


class SheetsClient:
    def __init__(self, service_account_file, sheet_id, worksheet_name):
        creds = Credentials.from_service_account_file(service_account_file, scopes=SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(sheet_id)
        self.worksheet = spreadsheet.worksheet(worksheet_name)

    def read_rows(self):
        """Retorna (header, lista de linhas como dict) com número da linha real na planilha."""
        all_values = self.worksheet.get_all_values()
        if not all_values:
            return [], []
        header = all_values[0]
        rows = []
        for i, raw_row in enumerate(all_values[1:], start=2):
            row = {header[j]: (raw_row[j] if j < len(raw_row) else "") for j in range(len(header))}
            row["_row_number"] = i
            rows.append(row)
        return header, rows

    def update_cell(self, row_number, header, column_name, value):
        if column_name not in header:
            raise ValueError(f"Coluna '{column_name}' não existe na planilha.")
        col_index = header.index(column_name) + 1
        self.worksheet.update_cell(row_number, col_index, value)
