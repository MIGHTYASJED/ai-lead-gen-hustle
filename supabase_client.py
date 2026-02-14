import requests

class SupabaseClient:
    def __init__(self, url, key):
        self.url = url
        self.key = key
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }

    def table(self, table_name):
        return SupabaseQueryBuilder(self.url, self.headers, table_name)

class SupabaseQueryBuilder:
    def __init__(self, base_url, headers, table_name):
        self.query_url = f"{base_url}/rest/v1/{table_name}"
        self.headers = headers.copy()
        self.params = {}
        self.json_data = None
        self.method = 'GET'

    def select(self, columns="*"):
        self.method = 'GET'
        self.params["select"] = columns
        return self

    def eq(self, column, value):
        self.params[f"{column}"] = f"eq.{value}"
        return self
        
    def limit(self, count):
        self.params["limit"] = str(count)
        return self

    def upsert(self, data, on_conflict=None):
        self.method = 'POST'
        self.headers["Prefer"] = "resolution=merge-duplicates,return=representation"
        if on_conflict:
            self.params["on_conflict"] = on_conflict
        self.json_data = data
        return self

    def update(self, data):
        self.method = 'PATCH'
        self.headers["Prefer"] = "return=representation"
        self.json_data = data
        return self

    def execute(self):
        try:
            if self.method == 'GET':
                response = requests.get(self.query_url, headers=self.headers, params=self.params)
            elif self.method == 'POST':
                response = requests.post(self.query_url, headers=self.headers, params=self.params, json=self.json_data)
            elif self.method == 'PATCH':
                response = requests.patch(self.query_url, headers=self.headers, params=self.params, json=self.json_data)
            else:
                return Response(None, "Unsupported Method")
                
            response.raise_for_status()
            try:
                data = response.json()
            except ValueError:
                data = [] # Handle no content
                
            return Response(data)
            
        except Exception as e:
            # print(f"Supabase Request Error: {e}")
            return Response([], str(e))

class Response:
    def __init__(self, data, error=None):
        self.data = data
        self.error = error

def create_client(url, key):
    return SupabaseClient(url, key)
