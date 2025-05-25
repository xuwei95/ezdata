from typing import Optional

from pydantic import BaseModel, ConfigDict


class NotionInfo(BaseModel):
    """
    Notion import info.
    """
    notion_workspace_id: str
    notion_obj_id: str
    notion_page_type: str
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, **data) -> None:
        super().__init__(**data)


class WebsiteInfo(BaseModel):
    """
    website import info.
    """
    provider: str = 'firecrawl'
    job_id: str = ''
    url: str
    mode: str = 'scrape'
    only_main_content: bool = False

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data) -> None:
        super().__init__(**data)


class ExtractSetting(BaseModel):
    """
    Model class for provider response.
    """
    datasource_type: str
    upload_file: Optional[str] = None
    notion_info: Optional[NotionInfo] = None
    website_info: Optional[WebsiteInfo] = None
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, **data) -> None:
        super().__init__(**data)
