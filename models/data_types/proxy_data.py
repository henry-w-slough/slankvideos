from dataclasses import dataclass


@dataclass
class ProxyData:
    """The urls required to add a proxy to a RequestHandler.
    
    Note that the http and https schemes need to be the full url for the proxy."""  
    http: str
    https: str