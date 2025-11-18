from urllib.parse import urlparse, urljoin


def get_sub_urls(url:str):
    parsed_url = urlparse(url)
    l = urlparse(url).path.split('/')
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return [urljoin(base_url, '/'.join(l[:i+1])) for i in range(len(l))]

print(get_sub_urls('https://example.com/a/b/c'))