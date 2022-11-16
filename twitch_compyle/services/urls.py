from collections import namedtuple
from urllib.parse import urljoin, urlencode, urlparse, urlunparse
from collections.abc import Iterable
# Endpoint = namedtuple('Endpoint', ['base_url', 'slug', 'required_params', 'optional_params'])
# Endpoint.__new__.__defaults__ = (None,) * len(Endpoint._fields)

class Endpoint():
    def __init__(self, base_url: str, slug: str, required_params = None, optional_params = None):
        def validate_urls(*args):
            for arg in args:
                if not isinstance(arg, str):
                    raise TypeError(f"string excpected, wrong type provided, found {type(arg)}")
        
            return args
        
        self.base_url, self.slug = validate_urls(base_url, slug)
        
        def validate_params(*args):
            args = list(args)
            for i, arg in enumerate(args):
                if arg is None:
                    args[i] = {}
                else:
                    if not isinstance(arg, Iterable):
                        raise TypeError(f"iterable excpected, wrong type provided, found {type(arg)}")
                    elif arg and not all(isinstance(item, str) for item in arg):
                        raise TypeError(f"iterable of strings excpected, wrong type provided")
                    args[i] = set(arg)
            
            if set.intersection(*args):
                raise ValueError(f"required and optional parameters must be disjoint")
            
            return args
                         
        self.required_params, self.optional_params = validate_params(required_params, optional_params)
    
    def build_url(self, **query):
        noramlized_query = {k: query[k] for k in self.required_params | self.optional_params if k in query and query[k]}
        
        if len(noramlized_query) < len(self.required_params) or not all(param in noramlized_query for param in self.required_params):
            raise ValueError(f"Missing following required parameters: {self.required_params.difference(noramlized_query)}")

        components = list(urlparse(self.base_url))
        components[2] = self.slug
        components[4] = urlencode(noramlized_query)
        
        return urlunparse(components)

test = Endpoint("https://api.twitch.tv/helix", "/token", ["client_id", "client_secret", "grant_type"], ["scope"])
url = test.build_url(client_id="1", client_secret="2", grant_type="client_credentials")
print(url)
#url = urlunparse(
        #     Components(
        #         scheme='https',
        #         netloc='example.com',
        #         ,
        #         path='',
        #         url='/',
        #         #fragment='anchor'
        #     )
        # )

#     Components = namedtuple(
#     typename='Components', 
#     field_names=['scheme', 'netloc', 'url', 'path', 'query', 'fragment']
# )

# query_params = {
#     'param1': 'some data', 
#     'param2': 42
# }

# 