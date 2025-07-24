from requests import Session

class WikidataAPI:

    def __init__(self, session: Session = Session()):
        self.httpSession = session

    
    def hasImageClaim(self, qId: str) -> bool:
        requestParams = {
            'action': 'wbgetentities',
            'ids': qId,
            'props': 'claims',
            'format': 'json'
        }

        response = self.httpSession.get(
            'https://www.wikidata.org/w/api.php',
            params=requestParams
        ).json()

        itemData = response.get('entities', {}).get(qId, {})
        claims = itemData.get('claims', {})

        return 'P18' in claims
