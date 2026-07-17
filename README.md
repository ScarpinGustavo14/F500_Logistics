# F500 Logistics — Calculadora de Rotas

Script Python que lê uma planilha do Google Sheets com colunas de origem e
destino, calcula a distância e o tempo de viagem entre os pontos e escreve
o resultado de volta na própria planilha.

O cálculo de rota usa a **[OpenRouteService](https://openrouteservice.org/)**
(baseada em OpenStreetMap), que tem um plano gratuito sem necessidade de
cartão de crédito — diferente da API do Google Maps, que exige conta de
faturamento mesmo dentro da cota grátis.

## Como funciona

1. Lê todas as linhas da aba configurada da planilha.
2. Para cada linha com `Origem` e `Destino` preenchidos e `Distância (km)`
   vazia, geocodifica os endereços e calcula a rota.
3. Escreve `Distância (km)`, `Duração (min)` e `Status` de volta na planilha.
4. Mantém um cache local (`route_cache.json`) para nunca pagar/consultar
   duas vezes a mesma rota ou endereço.

Linhas que já têm distância preenchida são puladas — então é seguro rodar
o script várias vezes na mesma planilha (só completa o que falta).

## Estrutura esperada da planilha

A aba precisa ter, na primeira linha, estas colunas (pode haver outras
colunas extras, a ordem não importa):

| Origem | Destino | Distância (km) | Duração (min) | Status |
|---|---|---|---|---|
| Av. Paulista, São Paulo | Aeroporto de Guarulhos | | | |

`Origem` e `Destino` podem ser um endereço em texto ou coordenadas no
formato `latitude,longitude`.

## Configuração

### 1. Chave gratuita do OpenRouteService

1. Crie uma conta em https://openrouteservice.org/dev/#/signup (sem cartão
   de crédito).
2. Gere uma chave de API (token) no painel — plano gratuito com 2.000
   requisições/dia.

### 2. Service account do Google (para acessar o Sheets)

1. No [Google Cloud Console](https://console.cloud.google.com/), crie um
   projeto (ou use um existente).
2. Ative a **Google Sheets API** (APIs & Services → Enable APIs → busque
   "Google Sheets API").
3. Vá em **APIs & Services → Credentials → Create Credentials → Service
   Account**, crie a service account.
4. Na service account criada, vá em **Keys → Add Key → Create new key →
   JSON** e baixe o arquivo. Salve-o na raiz do projeto como
   `credentials.json` (não commite esse arquivo — já está no `.gitignore`).
5. Abra sua planilha no Google Sheets e compartilhe com o e-mail da service
   account (campo `client_email` dentro do JSON baixado), com permissão de
   **Editor**.

### 3. Variáveis de ambiente

Copie `.env.example` para `.env` e preencha:

```bash
cp .env.example .env
```

```
ORS_API_KEY=sua_chave_do_openrouteservice
GOOGLE_SERVICE_ACCOUNT_FILE=credentials.json
GOOGLE_SHEET_ID=id_da_planilha  # está na URL, entre /d/ e /edit
GOOGLE_WORKSHEET_NAME=Rotas     # nome da aba
```

### 4. Instalar dependências e rodar

```bash
pip install -r requirements.txt
python route_calculator.py
```

## Limites do plano gratuito

- OpenRouteService: 2.000 requisições/dia, 40/minuto. O script já espera
  ~1,6s entre chamadas para respeitar o limite por minuto.
- O cache local evita reconsultar rotas/endereços já calculados em
  execuções anteriores.
