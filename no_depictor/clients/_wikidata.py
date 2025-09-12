from ..data import CategoryDescriptor
from requests import Session

class WikidataAPI:

    def __init__(self, session: Session = Session()):
        self.httpSession = session

    
    def hasImageClaim(self, qId: str) -> bool:
        requestParams = {
            'action': 'wbgetentities',
            'ids': qId,
            'props': 'claims',
            'format': 'json',
        }

        response = self.httpSession.get(
            'https://www.wikidata.org/w/api.php',
            params=requestParams,
            timeout=60,
        ).json()

        itemData = response.get('entities', {}).get(qId, {})
        claims = itemData.get('claims', {})

        return 'P18' in claims
    

    def getItemForCommonsCategory(self, categoryName: str) -> CategoryDescriptor:
        sparql = f'''
            select ?item ?image ?cat where {{
              ?item wdt:P18 ?image;
                    wdt:P373 "{categoryName}";
                    wdt:P373 ?cat.
            }}
        '''

        requestParams = {
            'format': 'json',
            'query': sparql,
        }

        response = self.httpSession.get(
            'https://query.wikidata.org/sparql',
            params=requestParams,
            timeout=60,
        ).json()

        if 'results' not in response or 'bindings' not in response['results']:
            raise Exception(f'Invalid response from Wikidata SPARQL: {response}')
        
        bindings = response['results']['bindings']
        if not bindings:
            raise Exception(f'No results found for category "{categoryName}" in Wikidata SPARQL query.')
        
        binding = bindings[0]
        itemUri = binding.get('item', {}).get('value')
        if not itemUri:
            raise Exception(f'No item found for category "{categoryName}" in Wikidata SPARQL query.')
        
        qId = itemUri.split('/')[-1]  # Extract the QID from the URI
        if not qId.startswith('Q'):
            raise Exception(f'Invalid QID "{qId}" extracted from item URI "{itemUri}".')

        return CategoryDescriptor(qId, categoryName)
