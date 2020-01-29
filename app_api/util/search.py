
def datum_for_county(county):
    '''Given a US_County instance, returns a dictionary that can be
    serialized as part of a JSON array of search data for Bloodhound.js
    '''
    return {
        'id': county.fips5,
        'value': county.search_str,
        'tokens': county.search_str.split(' '),
        'name': county.name,
        'state': county.state.full,
    }

def datum_for_state(state):
    return state.full
