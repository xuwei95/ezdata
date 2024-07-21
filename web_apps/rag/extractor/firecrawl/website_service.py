import datetime
import json
from web_apps.rag.extractor.firecrawl.firecrawl_app import FirecrawlApp
from utils.cache_utils import redis_cli
from utils.ext_storage import storage
api_key = ''
base_url = ''


class WebsiteService:

    @classmethod
    def document_create_args_validate(cls, args: dict):
        if 'url' not in args or not args['url']:
            raise ValueError('url is required')
        if 'options' not in args or not args['options']:
            raise ValueError('options is required')
        if 'limit' not in args['options'] or not args['options']['limit']:
            raise ValueError('limit is required')

    @classmethod
    def crawl_url(cls, args: dict) -> dict:
        provider = args.get('provider')
        url = args.get('url')
        options = args.get('options')
        if provider == 'firecrawl':
            firecrawl_app = FirecrawlApp(api_key=api_key,
                                         base_url=base_url)
            crawl_sub_pages = options.get('crawl_sub_pages', False)
            only_main_content = options.get('only_main_content', False)
            if not crawl_sub_pages:
                params = {
                    'crawlerOptions': {
                        "includes": [],
                        "excludes": [],
                        "generateImgAltText": True,
                        "limit": 1,
                        'returnOnlyUrls': False,
                        'pageOptions': {
                            'onlyMainContent': only_main_content,
                            "includeHtml": False
                        }
                    }
                }
            else:
                includes = options.get('includes').split(',') if options.get('includes') else []
                excludes = options.get('excludes').split(',') if options.get('excludes') else []
                params = {
                    'crawlerOptions': {
                        "includes": includes if includes else [],
                        "excludes": excludes if excludes else [],
                        "generateImgAltText": True,
                        "limit": options.get('limit', 1),
                        'returnOnlyUrls': False,
                        'pageOptions': {
                            'onlyMainContent': only_main_content,
                            "includeHtml": False
                        }
                    }
                }
                if options.get('max_depth'):
                    params['crawlerOptions']['maxDepth'] = options.get('max_depth')
            job_id = firecrawl_app.crawl_url(url, params)
            website_crawl_time_cache_key = f'website_crawl_{job_id}'
            time = str(datetime.datetime.now().timestamp())
            redis_cli.setex(website_crawl_time_cache_key, 3600, time)
            return {
                'status': 'active',
                'job_id': job_id
            }
        else:
            raise ValueError('Invalid provider')

    @classmethod
    def get_crawl_status(cls, job_id: str, provider: str) -> dict:
        if provider == 'firecrawl':
            # decrypt api_key
            firecrawl_app = FirecrawlApp(api_key=api_key,
                                         base_url=base_url)
            result = firecrawl_app.check_crawl_status(job_id)
            crawl_status_data = {
                'status': result.get('status', 'active'),
                'job_id': job_id,
                'total': result.get('total', 0),
                'current': result.get('current', 0),
                'data': result.get('data', [])
            }
            if crawl_status_data['status'] == 'completed':
                website_crawl_time_cache_key = f'website_crawl_{job_id}'
                start_time = redis_cli.get(website_crawl_time_cache_key)
                if start_time:
                    end_time = datetime.datetime.now().timestamp()
                    time_consuming = abs(end_time - float(start_time))
                    crawl_status_data['time_consuming'] = f"{time_consuming:.2f}"
                    redis_cli.delete(website_crawl_time_cache_key)
        else:
            raise ValueError('Invalid provider')
        return crawl_status_data

    @classmethod
    def get_crawl_url_data(cls, job_id: str, provider: str, url: str) -> dict | None:
        if provider == 'firecrawl':
            file_key = 'website_files/' + job_id + '.txt'
            if storage.exists(file_key):
                data = storage.load_once(file_key)
                if data:
                    data = json.loads(data.decode('utf-8'))
            else:
                # decrypt api_key
                firecrawl_app = FirecrawlApp(api_key=api_key,
                                             base_url=base_url)
                result = firecrawl_app.check_crawl_status(job_id)
                if result.get('status') != 'completed':
                    raise ValueError('Crawl job is not completed')
                data = result.get('data')
            if data:
                for item in data:
                    if item.get('source_url') == url:
                        return item
            return None
        else:
            raise ValueError('Invalid provider')

    @classmethod
    def get_scrape_url_data(cls, provider: str, url: str, only_main_content: bool) -> dict | None:
        if provider == 'firecrawl':
            # decrypt api_key
            firecrawl_app = FirecrawlApp(api_key=api_key,
                                         base_url=base_url)
            params = {
                'pageOptions': {
                    'onlyMainContent': only_main_content,
                    "includeHtml": False
                }
            }
            result = firecrawl_app.scrape_url(url, params)
            return result
        else:
            raise ValueError('Invalid provider')
