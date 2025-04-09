import asyncio
from playwright.async_api import async_playwright, Playwright
from bs4 import BeautifulSoup
import re
import time
import concurrent.futures

sitemap_url = 'https://www.dlsu.edu.ph/sitemap_index.xml'
sitemap_filter = re.compile('post-sitemap')

max_tabs = 20
page_limit = 1400
max_timeout = 15000 # milliseconds

email_filter = re.compile(r"^\S+@\S+\.\S+$") 

# Finds all <loc> XML tags and gets string inside
def parse_links(xml):
    #start_time = time.time()

    soup = BeautifulSoup(xml, 'xml')
    links = [tag.string for tag in soup.find_all('loc') if tag.prefix == '']
    #print(links)
    #print(len(links))

    #print(time.time() - start_time, 'seconds')

    return links

# Returns content of HTML document as a string
async def load_html(context, url, timeout=30000, reload=False):
    page = await context.new_page()
    await page.goto(url, timeout=timeout, wait_until='domcontentloaded')
    if reload:
        await page.reload()
    html = await page.content()
    await page.close()
    return html

async def get_links_from_sitemap(context, sitemap_url):
    sitemaps = parse_links(await load_html(context, sitemap_url))

    start_time = time.time()

    tasks = [asyncio.create_task(load_html(context, sitemap, reload=True)) for sitemap in sitemaps]
    results = await asyncio.gather(*tasks)
    #print(results)
    #print(len(results))
    #print(len(sitemaps))
    links = [parse_links(html) for html in results]

    print(time.time() - start_time, 'seconds')

    return sitemaps, links

def filter_links(sitemaps, links, sitemap_filter):
    final_sitemaps = []
    final_links = []
    for sitemap, links in zip(sitemaps, links):
        if sitemap_filter.search(sitemap):
            final_sitemaps.append(sitemap)
            final_links.extend(links)

    print(final_links)
    print(len(final_links))
    print(final_sitemaps)

    return final_sitemaps, final_links

def get_emails(html):
    soup = BeautifulSoup(html, 'lxml')
    emails.update(soup.find_all(string=email_filter))

async def email_worker(queue):
    while True:
        html = await queue.get()
        get_emails(html)
        queue.task_done()



async def run(playwright: Playwright):
    chromium = playwright.chromium # or "firefox" or "webkit".
    browser = await chromium.launch()
    context = await browser.new_context()
    
    sitemaps, links = await get_links_from_sitemap(context, sitemap_url)
    final_sitemaps, final_links = filter_links(sitemaps, links, sitemap_filter)

    # Initialize email searching threads
    # loop = asyncio.get_event_loop()
    # with concurrent.futures.ProcessPoolExecutor() as pool:
    #     pass
    
    results = asyncio.Queue()
    
    consumer = asyncio.create_task(email_worker(results))

    # Run tasks max_tabs at a time
    for i in range(1000, page_limit, max_tabs):
        start_time = time.time()
        tasks = [asyncio.create_task(load_html(context, link, max_timeout)) for link in final_links[i:i+max_tabs]]

        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                results.put_nowait(result)
            except Exception as e:
                print(e)
        
        # Sequential test
        # for link in final_links[i:i+max_tabs]:
        #     try:
        #         result = await load_html(context, link, max_timeout)
        #         results.put_nowait(result)
        #     except Exception as e:
        #         print(e)

        #await asyncio.gather(*tasks, return_exceptions=True)
        print(f'{time.time() - start_time} seconds for links {i+1}-{i+max_tabs}')

    await results.join()
    consumer.cancel()

    print(results)
    print(results.qsize())
    print(emails)
    # print(len(results))
    # for result in results:
    #     start_time = time.time()
    #     get_emails(result)
    #     print(f'{time.time() - start_time} seconds for result')

    #html = await load_html(context, 'https://www.dlsu.edu.ph/contact-us-new-normal/')


async def main():
    async with async_playwright() as playwright:
        await run(playwright)

    with open('output.txt', 'w') as f:
        for email in emails:
            f.write(f'{email}\n')

emails = set()
asyncio.run(main())