from requests import Session
from ..data import CategoryDescriptor


class PetScan:

    def __init__(self, session: Session = Session()):
        self.httpSession = session


    def getSubcategories(self, categoryName: str, depth: int = 1) -> list[CategoryDescriptor]:
        categoryName = categoryName.replace('_', ' ')
        requestParams = {
            'categories': categoryName,
            'depth': depth,
            'wikidata_item': 'with',
            'project': 'wikimedia',
            'language': 'commons',
            'format': 'json',
            'ns[14]': 1,  # Namespace for categories
            'search_max_results': 500, # Seems to be ignored by PetScan...
            'doit': 1
        }
        
        rawResponse = self.httpSession.get(
            'https://petscan.wmcloud.org/',
            params=requestParams,
            timeout=60,
        )
        try:
            response = rawResponse.json()
        except Exception as e:
            raise Exception(
                'PetScan API responded with invalid JSON (response code: ' +
                str(rawResponse.status_code) + '). Beginning of the response: ' + rawResponse.text[:200]
            ) from e

        # PetScan JSON response is far from self-explanatory,
        # property path: response['*'][0]['a']['*']
        items = response \
            .get('*', [{}])[0] \
            .get('a', {}) \
            .get('*', [])
        
        return [
            CategoryDescriptor(item['q'], item['title'])
            for item in items
            if 'q' in item and 'title' in item
        ]
