from urllib.request import urlopen

# Input arguments
url = 'https://www.dlsu.edu.ph'
scraping_time = 10
num_threads = 10

# Main
if __name__ == '__main__':
    page = urlopen(url)
    html_bytes = page.read()
    html = html_bytes.decode()
    print(html)