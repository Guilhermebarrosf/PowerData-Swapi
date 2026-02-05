# PowerOfData - SWAPI Proxy (Python + Cloud Functions + API Gateway)

Projeto de API simples que consome a **SWAPI (https://swapi.dev/)** e expõe um endpoint único para consulta de:
- people (personagens)
- films (filmes)
- planets (planetas)
- starships (naves)
- vehicles (veículos)

A solução foi pensada para rodar no **Google Cloud Platform (GCP)** utilizando **Cloud Functions** e **API Gateway**, com foco em simplicidade e clareza (nível Júnior).

---

## Arquitetura da Solução

```
Cliente
   |
   | HTTP GET /swapi
   v
API Gateway (API Key)
   |
   | encaminhamento
   v
Cloud Function (Python)
   |
   | requests HTTP
   v
SWAPI (https://swapi.dev)
```

**Responsabilidades:**
- **API Gateway**: expõe o endpoint público, aplica autenticação simples (API Key) e roteia requisições.
- **Cloud Function**: valida parâmetros básicos, chama a SWAPI, aplica filtros simples e retorna JSON.
- **SWAPI**: API pública que fornece os dados de Star Wars.

---

## Endpoint

### GET `/swapi`

### Parâmetros de Query

- `resource` (**obrigatório**): `people | films | planets | starships | vehicles`
- `id` (opcional): busca item específico pelo id
- `search` (opcional): busca textual
- `page` (opcional): paginação da SWAPI
- `fields` (opcional): seleciona campos do retorno (ex: `name,height`)
- `sort` (opcional): ordena resultados (`name` ou `-name`)
- `limit` (opcional): limita quantidade de itens (1 a 50)
- `related` (opcional): consulta correlacionada (ex: `characters` para filmes)

---

## Exemplos de Uso (Local)

### Buscar personagens por texto
```bash
curl "http://localhost:8080?resource=people&search=luke"
```

### Buscar filme por id
```bash
curl "http://localhost:8080?resource=films&id=1"
```

### Filtrar campos + ordenar + limitar
```bash
curl "http://localhost:8080?resource=people&search=a&fields=name&sort=-name&limit=3"
```

### Consulta correlacionada (personagens de um filme)
```bash
curl "http://localhost:8080?resource=films&id=1&related=characters&limit=5&fields=name"
```

---

## Como Rodar Localmente

### Pré-requisitos
- Python 3.11+
- pip

### Instalar dependências
```bash
pip install -r requirements.txt
```

### Rodar Cloud Function localmente
```bash
functions-framework --target=swapi --source=src/main.py --port=8080
```

Acesse no navegador:
```
http://localhost:8080?resource=people&search=luke
```

---

## Testes Unitários

Os testes foram implementados com **pytest**, cobrindo:
- validação de método HTTP
- parâmetros inválidos
- consulta correlacionada

Executar:
```bash
pytest -q
```

---

### API Gateway
- Configurado via `openapi.yaml`
- Autenticação simples usando API Key (`x-api-key`)

---

## Decisões Técnicas

- Utilização de **Cloud Functions** para evitar gerenciamento de servidores.
- Um único endpoint para simplificar o design e o roteamento.
- Filtros simples (`fields`, `sort`, `limit`) para agregar valor sem aumentar complexidade.
- Consulta correlacionada (`related`) limitada para evitar excesso de requisições.

---

